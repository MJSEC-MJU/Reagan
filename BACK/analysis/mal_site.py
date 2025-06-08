import sys
import time
import uuid
import json
from urllib.parse import parse_qs

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 활성화된 <input>요소를 모두 찾아서 무작위 문자열 입력
def fill_inputs_in_context(driver, sent_values):
    xpath = "//input[@name and (boolean(@type)=false() or translate(@type, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')!='hidden')]"
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

# Chrome Performance 로그에서 postData를 파싱한 뒤, sent_values에 들어간 값(expected) 안에 actual 값(actual)이 포함되어 있는지 확인합니다.
def extract_post_data_from_logs(logs, sent_values):
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
    for field_name, expected in sent_values.items():
        actual_list = parsed_params.get(field_name)
        if actual_list:
            actual = actual_list[0]
            # “actual이 expected 안에 포함되어 있으면 True”
            if actual in expected:
                print(f"  • [{field_name}] 포함: True  (보낸 값 = '{expected}' / 패킷 값 = '{actual}')")
            else:
                print(f"  • [{field_name}] 포함: False (보낸 값 = '{expected}' / 패킷 값 = '{actual}')")
        else:
            print(f"  • [{field_name}] 값 없음: False (보낸 값 = '{expected}' / 패킷에는 해당 필드 없음)")
    print("============================\n")

def input_url(target_url):
    # 1) ChromeOptions 준비
    chrome_options = Options()
    # 필요하면 주석 해제하여 헤드리스 모드 사용 가능
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    # 2) Performance 로그(네트워크)를 활성화하기 위해 Options에 로깅 설정 추가
    chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    # 3) ChromeDriver 실행 (desired_capabilities 대신 옵션에 capability를 넣음)
    driver = webdriver.Chrome(options=chrome_options)

    # 4) CDP로 Network 수집 활성화
    driver.execute_cdp_cmd("Network.enable", {})

    try:
        print(f"[+] {target_url} 페이지에 접속 중...")
        driver.get(target_url)
        time.sleep(1)

        sent_values = {}

        # 5) 메인 문서에서 입력 필드 채우기
        print("▶ 메인 문서에서 입력 필드 탐색 및 채우기")
        fill_inputs_in_context(driver, sent_values)

        # 6) 1단계 iframe 순회하며 내부 입력 필드 채우기
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
            sys.exit(1)

        # 7) 입력한 랜덤 문자열들 출력
        print("\n[+] 입력을 시도한 필드 및 랜덤 문자열 목록")
        for k, v in sent_values.items():
            print(f"  - {k} = {v}")

        # 8) 첫 번째 <form> 요소 찾아서 submit()
        try:
            form_elem = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//form"))
            )
        except Exception:
            print("⚠️ <form> 요소를 찾을 수 없어 전송할 수 없습니다.")
            driver.quit()
            sys.exit(1)

        print("\n[+] 폼을 전송(submit)합니다...")
        driver.execute_script("arguments[0].submit();", form_elem)

        # 9) 네트워크 요청이 잡힐 때까지 잠시 대기
        time.sleep(3)

        # 10) Performance 로그 전체 가져오기
        logs = driver.get_log("performance")

        # 11) 로그에서 POST data 파싱하여 비교
        extract_post_data_from_logs(logs, sent_values)

    finally:
        driver.quit()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("사용법: python mal_site.py <타겟_URL>")
        sys.exit(1)

    target_url = sys.argv[1]
    input_url(target_url)