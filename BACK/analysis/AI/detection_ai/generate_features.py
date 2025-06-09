import pandas as pd
import re
from urllib.parse import urlparse
import random

# 특징 추출
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

def main():
    # 파일 경로 이건 로컬 파일 경로고 사실 서버에 들어가면 쓸 일 없음 나만 쓰면 됨
    DATA_PATH = "/Users/phaethon/Desktop/Reagan Project/Reagan/DATA/"
    tranco_file = DATA_PATH + "tranco_realistic_urls.csv"
    phishing_file = DATA_PATH + "phishing_urls.csv"
    output_file = DATA_PATH + "phishing_features.csv"

    # 1. 정상 URL (컬럼 없음 → 실제는 rank 컬럼에 URL 있음)
    df_tranco = pd.read_csv(tranco_file, names=["rank", "domain"])
    urls_normal = [
        str(url).strip()
        for url in df_tranco["rank"]
        if isinstance(url, str) and url.startswith("http")
    ]

    # safe url 모음 추가 (네이버, 구글, 깃허브, 유튜브 등 여러가지)
    safe_file = DATA_PATH + "safe_urls.csv"
    df_safe = pd.read_csv(safe_file)
    safe_urls = df_safe["url"].dropna().tolist()
    urls_normal.extend(safe_urls)

    urls_normal.extend(safe_urls)

    urls_normal = random.sample(urls_normal, 20000)

    # 2. 악성 URL (컬럼명: phishing_url)
    df_phishing = pd.read_csv(phishing_file)
    urls_phishing = df_phishing["phishing_url"].dropna().sample(n=20000, random_state=42).tolist()

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