import solve
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 1) reCAPTCHA 우회 → driver 리턴
target_url = "https://2captcha.com/ko/demo/recaptcha-v2"
driver = solve.main(target_url)
if not driver:
    raise RuntimeError("CAPTCHA bypass failed")

# 2) 타깃 페이지 로드 (이미 site_url 으로 우회했지만, 데모 페이지가 다르면 다시 GET)
# 3) (선택) 우회 직후 HTML 확인
print("=== BEFORE SUBMIT ===")
print(driver.page_source[:500])

wait = WebDriverWait(driver, 5)

# 1) 폼 안의 버튼/인풋부터 시도
submit_elems = driver.find_elements(
    By.CSS_SELECTOR,
    "form button[type=submit], form input[type=submit]"
)

# 2) 없으면 페이지 전체에서 한 번 더
if not submit_elems:
    submit_elems = driver.find_elements(
        By.CSS_SELECTOR,
        "button[type=submit], input[type=submit]"
    )

if submit_elems:
    btn = submit_elems[0]
    # 클릭 가능해질 때까지 기다리기
    wait.until(EC.element_to_be_clickable(btn))
    print(f"[Info] 제출 버튼 클릭: <{btn.tag_name} class=\"{btn.get_attribute('class')}\"…>")
    btn.click()
    # 페이지 전환 대기
    try:
        wait.until(EC.staleness_of(btn))
    except:
        time.sleep(1)
    print("=== AFTER SUBMIT ===")
    print(driver.page_source[:500])
else:
    print("[Info] 제출 버튼이 발견되지 않아 클릭을 건너뜁니다.")

time.sleep(1)
# 5) 마무리
driver.quit()