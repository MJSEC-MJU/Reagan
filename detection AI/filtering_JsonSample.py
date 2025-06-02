import os
import json
import re
from bs4 import BeautifulSoup
import pandas as pd

# 경로 설정
base_dir = "website_dataset"
filtered_dir = "filtered_dataset"
phishing_dir = os.path.join(base_dir, "phishing")
normal_dir = os.path.join(base_dir, "normal")
filtered_phishing_dir = os.path.join(filtered_dir, "phishing")
filtered_normal_dir = os.path.join(filtered_dir, "normal")
os.makedirs(filtered_phishing_dir, exist_ok=True)
os.makedirs(filtered_normal_dir, exist_ok=True)

# 필터 기준 함수
def is_valid_sample(sample):
    if not sample:
        return False

    html = sample.get("html", "")
    scripts = sample.get("scripts", [])

    # 기준 1: HTML 길이
    if len(html) < 500:
        return False

    # 기준 2: 스크립트 개수
    if len(scripts) == 0:
        return False

    # 기준 3: 에러 키워드 포함 여부
    error_keywords = ["not found", "403", "unauthorized", "RTM", "error", "blocked"]
    if any(k in html.lower() for k in error_keywords):
        return False

    # 기준 4: 중요한 태그 포함 여부
    soup = BeautifulSoup(html, "html.parser")
    if not (soup.find("form") or soup.find("input") or soup.find("button")):
        return False

    # 기준 5: DOM 노드 개수
    if len(soup.find_all()) < 15:
        return False

    # 기준 6: 텍스트 단어 수
    text = soup.get_text(separator=" ")
    if len(re.findall(r'\w+', text)) < 30:
        return False

    return True

# 필터링 수행
records = []

for label, in_dir, out_dir in [(1, phishing_dir, filtered_phishing_dir), (0, normal_dir, filtered_normal_dir)]:
    for fname in os.listdir(in_dir):
        if not fname.endswith(".json"):
            continue

        fpath = os.path.join(in_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            sample = json.load(f)

        if is_valid_sample(sample):
            out_path = os.path.join(out_dir, fname)
            with open(out_path, "w", encoding="utf-8") as out_f:
                json.dump(sample, out_f, ensure_ascii=False, indent=2)
            records.append({
                "file": fname,
                "url": sample.get("url", ""),
                "label": label
            })

# 라벨 저장
df = pd.DataFrame(records)
df.to_csv(os.path.join(filtered_dir, "filtered_labels.csv"), index=False)
print(f"유효한 샘플: {len(df)}개")