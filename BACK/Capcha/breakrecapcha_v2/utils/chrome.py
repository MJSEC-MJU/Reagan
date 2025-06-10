from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from utils.vpn import get_random_proxy

def create_chrome_with_proxy():
    chrome_options = Options()
    proxy = get_random_proxy()
    chrome_options.add_argument(f'--proxy-server={proxy}')
    # 기타 옵션 추가 (headless, user-agent 등)
    # chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    return driver
