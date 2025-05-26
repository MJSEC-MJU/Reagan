import torch
from bs4 import BeautifulSoup
from train_cnn_gcn_model import SimpleWebClassifier, tokenize_html, dom_to_graph, encode_tokens

MODEL_PATH = "second_detect.pt"

model = None
vocab = None

@torch.no_grad()
def predict_from_html(html):
    global model, vocab

    # 모델 및 vocab 초기화
    if model is None:
        model = SimpleWebClassifier(vocab_size=1000, embed_dim=64)
        model.load_state_dict(torch.load(MODEL_PATH))
        model.eval()

    if vocab is None:
        vocab = {"<PAD>": 0, "<UNK>": 1}  # 최소한의 더미 vocab

    # HTML 토큰화 및 그래프 변환
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

# 테스트용 코드
if __name__ == "__main__":
    html = """
    <html><body>
    <form action='http://malicious-site.com'>
        <input type='text' name='username'>
    </form>
    </body></html>
    """
    result = predict_from_html(html)
    print(result)