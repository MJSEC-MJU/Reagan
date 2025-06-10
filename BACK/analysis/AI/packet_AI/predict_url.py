import json, joblib, pandas as pd
from .packet_AI import extract_all_features   # ← 방금 만든 함수들이 있는 파일명으로 수정
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent    # packet_AI 폴더 절대경로
MODEL_PATH = BASE_DIR / "rf_model.pkl"
COLS_PATH  = BASE_DIR / "rf_columns.json"

clf = joblib.load(MODEL_PATH)

with COLS_PATH.open(encoding="utf-8") as f:
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
    label = True if prob >= THRESHOLD else False
    return {"is_mal": label, "phishing_confidence": round(float(prob), 4)}

def is_malicious(url: str) -> bool:
    return classify_url(url)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("python predict_url.py <URL>")
        sys.exit(1)
    print(classify_url(sys.argv[1]))
