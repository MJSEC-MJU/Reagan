import joblib
import re
import os
from urllib.parse import urlparse
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # predictor.py가 있는 폴더
MODEL_PATH = os.path.join(BASE_DIR, "lightgbm_model.pkl")

# 학습된 모델 로드 (같은 폴더에 lightgbm_model.pkl 있어야 함, 백에서 predictor.py 가져갈때 pkl 파일도 무조건 가져갈 것)
model = joblib.load(MODEL_PATH)

# 의심 키워드 부분은 삭제했음

# URL 특징 추출 부분
def extract_features(url):
    parsed = urlparse(url)
    domain = parsed.netloc
    path = parsed.path
    full = parsed.geturl()

    subdomains = domain.split('.')[:-2] if len(domain.split('.')) > 2 else []
    suspicious_chars = ['@', '!', '=', '#', '&', '%', '?']
    phishing_terms = ['login', 'account', 'verify', 'bank', 'secure', 'update']

    return {
        'url_length': len(url),
        'num_hyphens': url.count('-'),
        'num_at': url.count('@'),
        'has_ip': bool(re.match(r'^(\d{1,3}\.){3}\d{1,3}$', domain)),
        'num_subdirectories': path.count('/'),
        'length_subdomain': sum(len(s) for s in subdomains),
        'has_https': parsed.scheme == 'https',
        'is_shortened': any(s in url for s in ['bit.ly', 'tinyurl.com', 'goo.gl'])
    }

# 예측 함수 나중에 백엔드 연결할때 해당 함수 불러오기!!!
def predict_url(url):
    features = extract_features(url)
    X = [list(features.values())]
    prediction = model.predict(X)[0]
    probability = model.predict_proba(X)[0][1]
    return {
        "phishing": bool(prediction),
        "confidence": float(round(probability, 3))
    }