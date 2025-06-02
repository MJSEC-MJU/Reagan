import os
import json
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# 저장 경로
base_dir = "website_dataset"
phishing_dir = os.path.join(base_dir, "phishing")
normal_dir = os.path.join(base_dir, "normal")
os.makedirs(phishing_dir, exist_ok=True)
os.makedirs(normal_dir, exist_ok=True)

# URL 파일 경로
phishing_file = "/Users/phaethon/Desktop/Reagan Project/Reagan/DATA/phishing_url_sample_1000.txt"
normal_file = "/Users/phaethon/Desktop/Reagan Project/Reagan/DATA/normal_url_sample_1000.txt"

# URL 불러오기
with open(phishing_file, "r") as f:
    phishing_urls = [line.strip() for line in f.readlines()]

with open(normal_file, "r") as f:
    normal_urls = [line.strip() for line in f.readlines()]

# 크롬드라이버 생성 함수 (악성 URL 할때는 headless=new 끄지 말 것 마우스 자동으로 이동시켜서 의도적으로 실행 or 다운로드 시작할지도 모름)
def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")
    return webdriver.Chrome(options=options)

# 기존 파일에서 최고 번호 확인
existing_files = set()
existing_numbers = []
existing_urls = set()
labels_path = os.path.join(base_dir, "labels.csv")

if os.path.exists(labels_path):
    df_old = pd.read_csv(labels_path)
    existing_urls = set(df_old['url'].tolist())
    existing_files = set(df_old['file'].tolist())
    existing_numbers = [int(f.replace(".json", "")) for f in existing_files if f.endswith(".json")]

counter = max(existing_numbers) + 1 if existing_numbers else 1

# 수집 함수
records = []
failed = []

def collect_and_save(url, label, save_dir):
    global counter
    global records

    if url in existing_urls:
        print(f"[SKIP] 중복 URL: {url}")
        return

    file_id = f"{counter:04d}.json"
    counter += 1

    file_path = os.path.join(save_dir, file_id)
    driver = create_driver()
    try:
        driver.set_page_load_timeout(10)
        driver.get(url)
        time.sleep(1)

        html = driver.page_source
        scripts = [s.get_attribute("innerHTML") for s in driver.find_elements(By.TAG_NAME, "script")]
        styles = [s.get_attribute("innerHTML") for s in driver.find_elements(By.TAG_NAME, "style")]

        data = {
            "url": url,
            "html": html,
            "scripts": scripts,
            "styles": styles
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        records.append({"file": file_id, "url": url, "label": label})
        print(f"[SAVED] {file_id} ({url})")

    except Exception as e:
        failed.append(url)
        print(f"[FAIL] {url[:60]}... → {e.__class__.__name__}: {e}")
    finally:
        driver.quit()

# 싱글 스레드 수집 루프
for label, urls, save_dir in [(1, phishing_urls, phishing_dir), (0, normal_urls, normal_dir)]:
    for url in urls:
        collect_and_save(url, label, save_dir)

# labels.csv 저장
records_df = pd.DataFrame(records)
if os.path.exists(labels_path):
    df_combined = pd.concat([df_old, records_df], ignore_index=True)
    df_combined.to_csv(labels_path, index=False)
else:
    records_df.to_csv(labels_path, index=False)

# 실패한 URL 기록
if failed:
    with open(os.path.join(base_dir, "failed_urls.txt"), "w") as f:
        f.write("\n".join(failed))

print(f"\n저장 완료: {len(records)}개 / 실패: {len(failed)}개")