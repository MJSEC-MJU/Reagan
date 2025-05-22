import os
import json
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from torch_geometric.data import Data as GraphData
from torch_geometric.nn import GCNConv
from bs4 import BeautifulSoup

# 경로 설정
# LABEL_PATH = "filtered_dataset/filtered_labels.csv"
# DATA_DIR = "filtered_dataset"
# MODEL_PATH = "cnn_gcn_model.pt"

# 경로 설정
LABEL_PATH = "website_dataset/labels.csv"
DATA_DIR = "website_dataset"
MODEL_PATH = "second_detect.pt"

TAG_VOCAB = {"<UNK>": 0}

def tag_to_index(tag):
    if tag not in TAG_VOCAB:
        TAG_VOCAB[tag] = len(TAG_VOCAB)
    return TAG_VOCAB[tag]

# HTML 토큰화
def tokenize_html(html):
    soup = BeautifulSoup(html, "html.parser")
    tokens = [tag.name for tag in soup.find_all() if tag.name]
    return tokens[:200]

# DOM 구조를 그래프로 변환
def dom_to_graph(html):
    soup = BeautifulSoup(html, "html.parser")
    nodes = []
    edges = []

    def traverse(node, parent_idx=None):
        if not hasattr(node, 'name') or node.name is None:
            return
        idx = len(nodes)
        nodes.append(node.name)
        if parent_idx is not None:
            edges.append((parent_idx, idx))
        for child in node.children:
            traverse(child, idx)

    traverse(soup)

    if not nodes:
        return None

    indices = [tag_to_index(n) for n in nodes]
    x = torch.tensor(indices).unsqueeze(1).float()
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous() if edges else torch.empty((2, 0), dtype=torch.long)
    return GraphData(x=x, edge_index=edge_index)

# 커스텀 데이터셋
class WebDataset(Dataset):
    def __init__(self, df):
        self.samples = []
        for _, row in df.iterrows():
            path = os.path.join(DATA_DIR, "phishing" if row.label == 1 else "normal", row.file)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            tokens = tokenize_html(data.get("html", ""))
            graph = dom_to_graph(data.get("html", ""))
            if not graph:
                continue
            self.samples.append((tokens, graph, int(row.label)))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        tokens, graph, label = self.samples[idx]
        return tokens, graph, label

# 모델 정의
class SimpleWebClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.cnn = nn.Conv1d(embed_dim, 64, kernel_size=3, padding=1)
        self.pool = nn.AdaptiveMaxPool1d(1)
        self.gcn1 = GCNConv(1, 64)
        self.fc = nn.Linear(64 * 2, 2)

    def forward(self, token_ids, graph):
        x_embed = self.embedding(token_ids).permute(0, 2, 1)
        x_cnn = self.pool(self.cnn(x_embed)).squeeze(-1)
        x_gcn = self.gcn1(graph.x, graph.edge_index)
        x_gcn = x_gcn.mean(dim=0)
        x = torch.cat([x_cnn, x_gcn.unsqueeze(0).expand(x_cnn.size(0), -1)], dim=1)
        return self.fc(x)

# 토큰 → 인덱스 변환
def build_vocab(samples):
    vocab = {"<PAD>": 0, "<UNK>": 1}
    for tokens, _, _ in samples:
        for t in tokens:
            if t not in vocab:
                vocab[t] = len(vocab)
    return vocab

def encode_tokens(tokens, vocab, max_len=200):
    ids = [vocab.get(t, vocab["<UNK>"]) for t in tokens]
    ids += [vocab["<PAD>"]] * (max_len - len(ids))
    return torch.tensor(ids[:max_len])

model = None
vocab = None

# 학습
def train_model():
    global model, vocab
    df = pd.read_csv(LABEL_PATH)
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
    train_data = WebDataset(train_df)
    test_data = WebDataset(test_df)

    vocab = build_vocab(train_data)
    train_tokens = [encode_tokens(t, vocab) for t, _, _ in train_data]
    train_graphs = [g for _, g, _ in train_data]
    train_labels = [l for _, _, l in train_data]

    model = SimpleWebClassifier(vocab_size=len(vocab), embed_dim=64)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()

    model.train()
    for epoch in range(5):
        total_loss = 0
        for i in range(len(train_tokens)):
            token_ids = train_tokens[i].unsqueeze(0)
            graph = train_graphs[i]
            label = torch.tensor([train_labels[i]])

            out = model(token_ids, graph)
            loss = criterion(out, label)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
        print(f"Epoch {epoch+1}, Loss: {total_loss:.4f}")

    # 모델 저장
    torch.save(model.state_dict(), MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")

    # 결과 표시
    model.eval()
    y_true, y_pred = [], []
    for tokens, graph, label in test_data:
        token_ids = encode_tokens(tokens, vocab).unsqueeze(0)
        output = model(token_ids, graph)
        pred = output.argmax(dim=1).item()
        y_true.append(label)
        y_pred.append(pred)

    print("\nClassification Report:\n")
    print(classification_report(y_true, y_pred))

# 예측기 함수
@torch.no_grad()
def predict_from_html(html):
    global model, vocab
    if model is None or vocab is None:
        model = SimpleWebClassifier(vocab_size=1000, embed_dim=64)
        model.load_state_dict(torch.load(MODEL_PATH))
        model.eval()

    tokens = tokenize_html(html)
    graph = dom_to_graph(html)
    if not graph:
        return {"error": "Invalid DOM structure"}
    token_ids = encode_tokens(tokens, vocab).unsqueeze(0)
    output = model(token_ids, graph)
    pred = output.argmax(dim=1).item()
    confidence = torch.softmax(output, dim=1)[0][pred].item()
    return {
        "phishing": bool(pred),
        "confidence": round(confidence, 3)
    }

if __name__ == "__main__":
    train_model()