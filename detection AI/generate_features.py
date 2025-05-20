import pandas as pd
import re
from urllib.parse import urlparse

# suspicious 키워드 정의
SUSPICIOUS_KEYWORDS = ['login', 'secure', 'update', 'verify', 'account', 'bank', 'confirm']

# URL 특징 추출 함수
def extract_features(url):
    parsed = urlparse(url)
    domain = parsed.netloc
    path = parsed.path

    return {
        'url': url,
        'url_length': len(url),
        'num_dots': url.count('.'),
        'num_hyphens': url.count('-'),
        'num_at': url.count('@'),
        'num_subdirectories': path.count('/'),
        'has_ip': bool(re.match(r'^(\d{1,3}\.){3}\d{1,3}$', domain)),
        'uses_https': parsed.scheme == 'https',
        'has_suspicious_words': any(word in url.lower() for word in SUSPICIOUS_KEYWORDS)
    }

def main():
    # 파일 경로 이건 로컬 파일 경로고 사실 서버에 들어가면 쓸 일 없음 나만 쓰면 됨
    DATA_PATH = "/Users/phaethon/Desktop/Reagan Project/Reagan/DATA/"
    tranco_file = DATA_PATH + "tranco_YLQQG.csv"
    phishing_file = DATA_PATH + "phishing_urls.csv"
    output_file = DATA_PATH + "phishing_features.csv"

    # 1. 정상 URL (컬럼 없음 → 수동 지정)
    df_tranco = pd.read_csv(tranco_file, names=["rank", "domain"])
    urls_normal = ["https://" + d for d in df_tranco.head(1000)["domain"]]

    # 2. 악성 URL (컬럼명: phishing_url)
    df_phishing = pd.read_csv(phishing_file)
    urls_phishing = df_phishing["phishing_url"].dropna().sample(n=1000, random_state=42).tolist()

    # 3. 특징 추출
    results = []

    for url in urls_normal:
        try:
            row = extract_features(url)
            row['label'] = 0  # 정상
            results.append(row)
        except Exception as e:
            print(f"[정상 URL 실패] {url}: {e}")

    for url in urls_phishing:
        try:
            row = extract_features(url)
            row['label'] = 1  # 악성
            results.append(row)
        except Exception as e:
            print(f"[악성 URL 실패] {url}: {e}")

    # 4. CSV 저장
    df_final = pd.DataFrame(results)
    df_final.to_csv(output_file, index=False)
    print(f"✅ 저장 완료: {output_file}")

if __name__ == "__main__":
    main()