import joblib
import re
from urllib.parse import urlparse

# 학습된 모델 로드 (같은 폴더에 lightgbm_model.pkl 있어야 함, 백에서 predictor.py 가져갈때 pkl 파일도 무조건 가져갈 것)
model = joblib.load("lightgbm_model.pkl")

# 해당 키워드 수상하게 많이 들어가면 피싱 가능성 높음 (이후에 더 추가 가능)
SUSPICIOUS_KEYWORDS = ['login', 'secure', 'update', 'verify', 'account', 'bank', 'confirm']

# URL 특징 추출 부분
def extract_features_from_url(url):
    parsed = urlparse(url)
    domain = parsed.netloc
    path = parsed.path
    return {
        'url_length': len(url),
        'num_dots': url.count('.'),
        'num_hyphens': url.count('-'),
        'num_at': url.count('@'),
        'num_subdirectories': path.count('/'),
        'has_ip': bool(re.match(r'^(\d{1,3}\.){3}\d{1,3}$', domain)),
        'uses_https': parsed.scheme == 'https',
        'has_suspicious_words': any(word in url.lower() for word in SUSPICIOUS_KEYWORDS)
    }

# 예측 함수 나중에 백엔드 연결할때 해당 함수 불러오기!!!
def predict_url(url):
    features = extract_features_from_url(url)
    X = [list(features.values())]
    prediction = model.predict(X)[0]
    probability = model.predict_proba(X)[0][1]
    return {
        "phishing": bool(prediction),
        "confidence": round(probability, 3),
    }

# 테스트 용이라 지워도 됨
if __name__ == "__main__":
    test_url = "https://www.goosmsi.com/6jlfin"
    result = predict_url(test_url)
    print(result)