import os
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile

def create_firefox_with_profile(profile_path: str = None) -> webdriver.Firefox:
    """
    Selenium 4.x 기준으로 Firefox 프로필만 로딩합니다.
    - profile_path에 실제 Firefox 프로필 경로를 지정하면 해당 프로필을 복사 없이 그대로 사용합니다.
    - profile_path가 None이면 기본 빈(임시) 프로필이 사용됩니다.
    """

    # 1) Firefox 옵션 객체 생성
    options = Options()
    options.headless = False  # 창을 띄우려면 False, 아예 보이지 않게 하려면 True

    # 2) 프로필 지정
    if profile_path:
        if not os.path.isdir(profile_path):
            raise FileNotFoundError(f"지정한 프로필 경로를 찾을 수 없습니다: {profile_path}")
        profile = FirefoxProfile(profile_path)
    else:
        profile = FirefoxProfile()

    # Selenium 4부터는 firefox_profile 인자를 직접 받지 않고 Options.profile에 지정해야 함
    options.profile = profile

    # 3) 드라이버 실행 (프록시나 capabilities 없이)
    driver = webdriver.Firefox(options=options)
    return driver
