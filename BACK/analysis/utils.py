# your_app/backends/captcha_analysis.py
import sys, os
SOLVE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "Capcha", "breakrecapcha_v2")
)
sys.path.insert(0, SOLVE_DIR)   # 이 줄이 반드시 와야 합니다
from solve import main as get_bypass_driver
from django.utils import timezone
from .models import AnalysisTask

from django.utils import timezone
from .models import AnalysisTask
from .AI.packet_AI.predict_url import is_malicious
from .AI.packet_AI.mal_site import input_url
from urllib.parse import urlparse

import time
import random
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

# Selenium + undetected-chromedriver 관련
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# AI 기반 피싱 예측 모듈 import
from detection_ai.predictor import predict_url


def _update(task: AnalysisTask, status: str, result=None, start=False, end=False):
    """
    AnalysisTask의 상태를 업데이트하는 공통 함수.
    """
    if start:
        task.started_at = timezone.now()
    if end:
        task.finished_at = timezone.now()
    task.status = status
    if result is not None:
        task.result = result
    task.save()


def _build_stealth_session():
    """
    랜덤 User-Agent / Accept-Language를 설정한 requests 세션을 반환.
    (간단한 스텔스 기능)
    """
    session = requests.Session()
    ua = UserAgent()
    user_agent = ua.random
    headers = {
        "User-Agent": user_agent,
        "Accept-Language": random.choice(["ko-KR,ko;q=0.9", "en-US,en;q=0.9"]),
        # 필요하다면 Referer, Accept 등 추가 헤더를 더 넣어도 됩니다.
    }
    session.headers.update(headers)
    return session


def analyze_phishing(source: str, base_url: str) -> bool:
    """
    기존 HTML 기반 피싱 탐지 로직 (필요시 보조용으로 남겨둠).
    - 폼 액션/링크 도메인 불일치 탐지
    - 키워드 기반 탐지
    """
    soup = BeautifulSoup(source, 'html.parser')
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc

    # 1) 폼 액션 도메인 검사
    for form in soup.find_all('form'):
        action = form.get('action', '').strip()
        if action:
            parsed = urlparse(action)
            if parsed.netloc and parsed.netloc != base_domain:
                return True

    # 2) 링크 도메인 불일치 검사
    for a in soup.find_all('a', href=True):
        parsed = urlparse(a['href'].strip())
        if parsed.netloc and parsed.netloc != base_domain:
            return True

    # 3) 키워드 기반 탐지 (단순 예시)
    text = soup.get_text(separator=' ').lower()
    keywords = ['verify', 'update', 'login', 'credential', 'password']
    if any(kw in text for kw in keywords):
        return True

    return False


def detect_captcha(source: str) -> bool:
    """
    HTML 소스 내 CAPTCHA 요소 탐지:
    - class/id, iframe src, img alt 검사
    """
    soup = BeautifulSoup(source, 'html.parser')

    # 1) class 혹은 id에 'captcha' 키워드가 포함된 태그가 있는지 확인
    for tag in soup.find_all():
        for val in tag.attrs.values():
            if 'captcha' in str(val).lower():
                return True

    # 2) reCAPTCHA iframe 검사
    for iframe in soup.find_all('iframe', src=True):
        src = iframe['src']
        if 'recaptcha' in src.lower() or 'captcha' in src.lower():
            return True

    # 3) 이미지 ALT 텍스트 검사
    for img in soup.find_all('img', alt=True):
        if 'captcha' in img['alt'].lower():
            return True

    return False


def run_site(task: AnalysisTask):
    """
    사이트 분석 작업:
    - AI 기반 피싱 예측 (detection_ai.predictor.predict_url)
      → URL만으로 피싱 여부와 확신도를 판단
    - (가능하다면) Stealth 세션으로 HTTP GET
    - 헤더 기반 취약점 검사(X-Frame-Options 등)
    - HTML 기반 캡챠 유무 탐지
    → HTTP 요청이 실패해도 전체를 실패로 표시하지 않고,
      AI 예측 결과를 항상 리턴하도록 변경함.
    """
    _update(task, 'running', start=True)

    url = task.request.site_url
    vulnerabilities = []
    status_code = None
    has_captcha = False

    # 1) AI 기반 URL 피싱 예측
    try:
        ai_result = predict_url(url)
        is_phishing = ai_result.get('phishing', False)
        phishing_confidence = ai_result.get('confidence', 0.0)
    except Exception as e:
        # 만약 AI 모델 로드나 예측 단계에서 에러가 나면,
        # fallback으로 is_phishing=False, confidence=0.0 으로 설정
        is_phishing = False
        phishing_confidence = 0.0
        vulnerabilities.append(f"AI prediction failed: {str(e)}")

    # 2) 실제 HTTP 요청 시도 (가능한 경우에만)
    try:
        session = _build_stealth_session()
        r = session.get(url, timeout=10)
        status_code = r.status_code
        source = r.text

        # 2-1) 헤더 검사: X-Frame-Options 확인
        if 'X-Frame-Options' not in r.headers:
            vulnerabilities.append('Missing X-Frame-Options header')
        # (추가로 Content-Security-Policy, HSTS 등 검사 가능)

        # 2-2) HTML 기반 캡챠 탐지
        has_captcha = detect_captcha(source)

    except Exception as e:
        # HTTP 요청 실패 시에도 “전체 실패”로 표시하지 않음
        # 단, vulnerabilities에 실패 이유를 기록
        vulnerabilities.append(f'HTTP request failed: {str(e)}')
        # status_code는 None으로 남겨두고, has_captcha는 False로 간주

    # 3) 최종 결과 조합 및 업데이트
    result = {
        'status_code': status_code,                 # None 또는 실제 응답 코드
        'vulnerabilities': vulnerabilities,         # 취약점 및 오류 메시지 목록
        'is_phishing': is_phishing,                 # AI 예측 결과
        'phishing_confidence': phishing_confidence, # AI 예측 확신도
        'has_captcha': has_captcha,                 # HTML에서 탐지한 캡챠 유무
    }
    _update(task, 'completed', result, end=True)


def run_captcha(task: AnalysisTask):
    """
    CAPTCHA 우회 작업:
    - 실제 캡챠 솔버 로직을 삽입하여 bypass_success 결정
    - 결과 저장
    - bypass 성공 시 run_packet 호출
    """
    _update(task, 'running', start=True)
    driver = None
    try:
        driver = get_bypass_driver(task.request.site_url)
        if driver is None:
            raise RuntimeError("CAPTCHA bypass failed")
            
        _update(task, 'completed',
                {'captcha_detected': True, 'bypass_success': True},
                end=True)

        # 6) bypass 성공하면 run_packet 호출
        if driver:
            run_packet(task, driver)
        else:
            _update(
                task,
                'failed',
                {'error': 'Captcha bypass failed; skipping packet analysis.'},
                end=True
            )

    except Exception as e:
        _update(task, 'failed', {'error': str(e)}, end=True)
    finally:
        if driver:
            driver.quit()


def run_packet(task: AnalysisTask, driver=None):
    """
    네트워크 패킷 분석 작업:
      1) task.request에서 packet_url이 있으면 그걸 사용, 없으면 site_url 사용
      2) is_malicious(url)를 호출해 악성 여부 판단 (stub 형태)
      3) _update로 상태를 저장. (완전 구현 전이라 todo 필드만 남김)

    ※ is_malicious가 dict가 아니라 문자열을 리턴해도 안전하게 처리하도록 수정됨
    """
    _update(task, "running", start=True)

    try:
        # 1) 분석 대상 URL 결정
        url = getattr(task.request, "packet_url", None) or task.request.site_url

        # 2) is_malicious 호출 및 반환값 타입 검사
        try:
            result = is_malicious(url)
        except Exception as e:
            # is_malicious 자체 호출 실패 시 stub 처리
            result = {}
            # 필요하다면 취약점에 기록
            task.result = {'error': f"is_malicious 호출 실패: {e}"}

        result['input_malicious'] = input_url(url, driver=driver)
        # 3) 결과 저장
        result_payload = result
        _update(task, "completed", result_payload, end=True)

    except Exception as e:
        # 분석 중 예외 발생 시 상태를 'failed'로 업데이트
        _update(task, "failed", {"error": str(e)}, end=True)
    finally:
        if driver:
            driver.quit()