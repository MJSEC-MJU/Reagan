import pickle
from selenium import webdriver

def load_cookies_from_file(driver, cookie_pkl_path: str, domain: str = None):
    """
    cookie_pkl_path: pickle로 저장된 쿠키 리스트
    domain: 쿠키를 추가할 도메인 (예: '.google.com')
    """
    with open(cookie_pkl_path, "rb") as f:
        cookies = pickle.load(f)

    for cookie in cookies:
        # domain이 지정되어 있으면, cookie['domain']을 덮어써서 특정 도메인으로 주입
        if domain:
            cookie['domain'] = domain
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            # 만약 도메인 mismatch 등 오류 나면 무시
            print(f"Cookie add failed: {e}")
    return
