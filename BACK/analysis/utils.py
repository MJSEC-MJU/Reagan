from django.utils import timezone
from .models import AnalysisTask
from analysis.AI.packet_AI.predict_url import is_malicious
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


def _update(task: AnalysisTask, status: str, result=None, start=False, end=False):
    if start:
        task.started_at = timezone.now()
    if end:
        task.finished_at = timezone.now()
    task.status = status
    if result is not None:
        task.result = result
    task.save()


def analyze_phishing(source: str, base_url: str) -> bool:
    """
    자체 분석으로 피싱 여부 판단:
    - 폼 액션/링크 도메인 불일치 탐지
    - 키워드 기반 탐지
    """
    soup = BeautifulSoup(source, 'html.parser')
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc

    # 폼 액션 도메인 검사
    for form in soup.find_all('form'):
        action = form.get('action', '').strip()
        if action:
            parsed = urlparse(action)
            if parsed.netloc and parsed.netloc != base_domain:
                return True

    # 링크 도메인 불일치 검사
    for a in soup.find_all('a', href=True):
        parsed = urlparse(a['href'].strip())
        if parsed.netloc and parsed.netloc != base_domain:
            return True

    # 키워드 탐지
    text = soup.get_text(separator=' ').lower()
    keywords = ['verify', 'update', 'login', 'credential', 'password']
    if any(kw in text for kw in keywords):
        return True

    return False


def detect_captcha(source: str) -> bool:
    """
    HTML 소스에서 CAPTCHA 요소 탐지:
    - class/id, iframe src, image alt 검사
    """
    soup = BeautifulSoup(source, 'html.parser')

    # class/id에 captcha 키워드
    for tag in soup.find_all():
        for val in tag.attrs.values():
            if 'captcha' in str(val).lower():
                return True

    # reCAPTCHA iframe 검사
    for iframe in soup.find_all('iframe', src=True):
        src = iframe['src']
        if 'recaptcha' in src.lower() or 'captcha' in src.lower():
            return True

    # 이미지 ALT 텍스트 검사
    for img in soup.find_all('img', alt=True):
        if 'captcha' in img['alt'].lower():
            return True

    return False


def run_site(task: AnalysisTask):
    """
    사이트 분석 작업:
    - HTTP GET, 헤더/HTML 기반 취약점 및 피싱/캡챠 탐지
    """
    _update(task, 'running', start=True)
    try:
        r = requests.get(task.request.site_url, timeout=10)
        source = r.text
        vulnerabilities = []

        # X-Frame-Options 헤더 확인
        if 'X-Frame-Options' not in r.headers:
            vulnerabilities.append('Missing X-Frame-Options header')

        # 추가 헤더 검사 가능 (Content-Security-Policy 등)

        # 피싱/캡챠 탐지
        is_phishing = analyze_phishing(source, task.request.site_url)
        has_captcha = detect_captcha(source)

        result = {
            'status_code': r.status_code,
            'vulnerabilities': vulnerabilities,
            'is_phishing': is_phishing,
            'has_captcha': has_captcha,
        }
        _update(task, 'completed', result, end=True)
    except Exception as e:
        _update(task, 'failed', {'error': str(e)}, end=True)


def run_packet(task):       # 네트워크 패킷 분석석
    _update(task, "running", start=True)
    try:
        url = getattr(task.request, "packet_url", None) or task.request.site_url
        verdict = is_malicious(url)['label']          # True = 악성, False = 정상
        _update(
            task,
            "completed",
            {'todo': 'packet analysis pending', "url": url, "malicious": verdict},
            end=True,
        )
    except Exception as e:
        _update(task, "failed", {"error": str(e)}, end=True)
    #_update(task, 'completed', {'todo': 'packet analysis pending'}, start=True, end=True)
 
def run_captcha(task):      # 캡챠 우회
    _update(task, 'completed', {'todo': 'captcha bypass pending'}, start=True, end=True)

def run_captcha(task: AnalysisTask):
    """
    CAPTCHA 우회 작업 (stub).
    추후 구체 로직 추가 예정.
    """
    _update(task, 'running', start=True)
    # TODO: CAPTCHA 우회 로직 구현
    result = {'todo': 'captcha bypass pending'}
    _update(task, 'completed', result, end=True)
