from django.utils import timezone
from .models import AnalysisTask
import requests

def _update(task, status, result=None, start=False, end=False):
    if start: task.started_at = timezone.now()
    if end:   task.finished_at = timezone.now()
    task.status = status
    if result is not None:
        task.result = result
    task.save()

def run_site(task): # 사이트 분석
    _update(task, 'running', start=True)
    try:
        r = requests.get(task.request.site_url, timeout=10)
        vulns = []
        if 'X-Frame-Options' not in r.headers:
            vulns.append('Missing X-Frame-Options header')
        _update(task, 'completed',
                {'status_code': r.status_code, 'vulnerabilities': vulns},
                end=True)
    except Exception as e:
        _update(task, 'failed', {'error': str(e)}, end=True)

def run_packet(task):       # 네트워크 패킷 분석석
    _update(task, 'completed', {'todo': 'packet analysis pending'}, start=True, end=True)

def run_captcha(task):      # 캡챠 우회
    _update(task, 'completed', {'todo': 'captcha bypass pending'}, start=True, end=True)
