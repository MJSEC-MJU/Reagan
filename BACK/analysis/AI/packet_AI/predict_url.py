import json, joblib, pandas as pd
from packet_AI import extract_all_features   # ← 방금 만든 함수들이 있는 파일명으로 수정

# ─ 준비: 모델·컬럼 로드 ─
clf = joblib.load("rf_model.pkl")
with open("rf_columns.json", encoding="utf-8") as f:
    COLUMNS = json.load(f)
THRESHOLD = 0.5 # 기준값

def classify_url(url: str) -> dict:
    feats = extract_all_features(url)
    if feats is None:
        return {"label": "unknown", "prob": 0.0}

    df = pd.DataFrame([feats]).drop(columns=["url"])
    df.fillna(0, inplace=True)
    df = pd.get_dummies(df, columns=["mime_type"], prefix="mime")

    # 학습 시점 컬럼과 동일하게 맞추기
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = 0
    df = df[COLUMNS]

    prob = clf.predict_proba(df)[0][1]     # 악성 확률
    label = "malicious" if prob >= THRESHOLD else "benign"
    return {"label": label, "prob": round(float(prob), 4)}

def is_malicious(url: str) -> bool:
    return classify_url(url)["label"]

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("python predict_url.py <URL>")
        sys.exit(1)
    print(classify_url(sys.argv[1]))
