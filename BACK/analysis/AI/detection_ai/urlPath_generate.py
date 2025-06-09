import pandas as pd
import random

# realistic한 경로 리스트
REALISTIC_PATHS = [
    "/login", "/account/settings", "/user/profile", "/home", "/dashboard",
    "/products/view/123", "/search?q=security", "/docs/intro", "/blog/article-1",
    "/download/setup.exe", "/news/2024/06", "/api/v1/data", "/register"
]

# 트란코 파일 경로 (수정 가능)
tranco_file = "/Users/phaethon/Desktop/Reagan Project/Reagan/DATA/tranco_YLQQG.csv"
output_file = "/Users/phaethon/Desktop/Reagan Project/Reagan/DATA/tranco_realistic_urls.csv"

# 트란코 상위 도메인 읽기
df_tranco = pd.read_csv(tranco_file, names=["rank", "domain"])
top_domains = df_tranco.head(100000)["domain"].tolist()

# realistic한 URL 생성
urls_normal = []
for domain in top_domains:
    path = random.choice(REALISTIC_PATHS) if random.random() < 0.5 else ""
    url = f"https://{domain}{path}"
    urls_normal.append(url)

# 저장
df_urls = pd.DataFrame(urls_normal, columns=["url"])
df_urls.to_csv(output_file, index=False)
print(f"✅ 저장 완료: {output_file}")