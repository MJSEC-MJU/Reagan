import sys
import time
import uuid
import json
import platform
from urllib.parse import parse_qs

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def create_chrome_driver():
    chrome_options = Options()
    system = platform.system()

    if system == "Linux":
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
    elif system == "Windows":
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
    else:
        chrome_options.add_argument("--disable-gpu")

    chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    return webdriver.Chrome(options=chrome_options)

def fill_inputs_in_context(driver, sent_values):
    xpath = "//input[@name and (boolean(@type)=false() or translate(@type,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')!='hidden')]"
    input_elements = driver.find_elements(By.XPATH, xpath)

    for elem in input_elements:
        try:
            if not elem.is_displayed() or not elem.is_enabled():
                continue

            field_name = elem.get_attribute("name")
            rand_str = uuid.uuid4().hex
            elem.clear()
            elem.send_keys(rand_str)
            sent_values[field_name] = rand_str
            print(f"  • '{field_name}' 필드에 랜덤 문자열 '{rand_str}' 입력 완료.")
        except Exception as e:
            print(f"  ⚠️ '{field_name}' 입력 실패: {e}")
            continue

def extract_post_data_from_logs(logs, sent_values):
    from urllib.parse import parse_qs
    parsed_params = {}
     # selenium-wire 요청 리스트인 경우
    if logs and hasattr(logs[0], 'method') and hasattr(logs[0], 'body'):
        
        # driver.requests 중 POST 요청 찾기
        for req in logs:
            if req.method == "POST":
                try:
                    parsed_params = parse_qs(req.body.decode(), keep_blank_values=True)
                except Exception:
                    pass
                break
    else: 
        # CDP performance 로그인 경우       
        msgs = []
        for entry in logs:
            try:
                raw = json.loads(entry["message"])["message"]
            except Exception:
                continue
            msgs.append(raw)

        parsed_params = {}
        for m in msgs:
            if m.get("method") == "Network.requestWillBeSent":
                params = m.get("params", {})
                request = params.get("request", {})
                if request.get("method") == "POST":
                    headers = request.get("headers", {})
                    content_type = headers.get("Content-Type", "")
                    if "application/x-www-form-urlencoded" in content_type:
                        post_data = request.get("postData", "")
                        if post_data:
                            parsed_params = parse_qs(post_data, keep_blank_values=True)
                            break

    print("\n=== 필드별 비교 결과 ===")
    all_ok = False # 다르면 악성코드 = True
    for field_name, expected in sent_values.items():
        actual_list = parsed_params.get(field_name)
        if actual_list:
            actual = actual_list[0]
            ok = (actual not in expected)
            print(f"  • [{field_name}] 포함: {ok}  (보낸 값 = '{expected}' / 패킷 값 = '{actual}')")
        else:
            print(f"  • [{field_name}] 값 없음: {ok} (보낸 값 = '{expected}' / 패킷에는 해당 필드 없음)")
        all_ok = all_ok and ok

    print("============================\n")
    return all_ok

def input_url(target_url, driver=None):
    a = False
    if driver is None:
        driver = create_chrome_driver()
        
        own_driver=True
    else:
        own_driver=False
        driver.requests.clear()
    try:
        if own_driver:
            driver.get(target_url)
            time.sleep(1)
        sent_values = {}
        print("▶ 메인 문서에서 입력 필드 탐색 및 채우기")
        fill_inputs_in_context(driver, sent_values)

        iframe_elements = driver.find_elements(By.TAG_NAME, "iframe")
        for idx, iframe in enumerate(iframe_elements, start=1):
            try:
                driver.switch_to.frame(iframe)
                print(f"▶ iframe #{idx} 내부로 전환 완료")
                fill_inputs_in_context(driver, sent_values)
            except Exception as e:
                print(f"  ⚠️ iframe #{idx} 접근 실패: {e}")
            finally:
                driver.switch_to.default_content()

        if not sent_values:
            print("⚠️ 입력할 <input> 요소를 전혀 찾지 못했습니다.")
            driver.quit()
            return False

        print("\n[+] 입력을 시도한 필드 및 랜덤 문자열 목록")
        for k, v in sent_values.items():
            print(f"  - {k} = {v}")

        try:
            form_elem = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//form"))
            )
        except Exception:
            print("⚠️ <form> 요소를 찾을 수 없어 전송할 수 없습니다.")
            driver.quit()
            return False

        print("\n[+] 폼을 전송(submit)합니다...")
        form_elem.submit()
        time.sleep(3)
        if hasattr(driver, 'requests'):
            logs = driver.requests
        else:
            logs = driver.get_log("performance")

        a = extract_post_data_from_logs(logs, sent_values)
        return a
        
    finally:

        driver.quit()
        return a

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("사용법: python mal_site.py <타겟_URL>")
        sys.exit(1)

    target_url = sys.argv[1]
    ok = input_url(target_url)
    sys.exit(0 if ok else 1)
