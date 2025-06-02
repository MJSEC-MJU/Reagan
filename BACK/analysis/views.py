# your_app/views.py

from rest_framework import viewsets
from rest_framework.response import Response
from .models import AnalysisRequest, AnalysisTask
from .serializers import AnalysisRequestSerializer, AnalysisTaskSerializer
from .utils import run_site, run_captcha, run_packet, _update
from detection_ai.predictor import predict_url

class AnalysisRequestViewSet(viewsets.ModelViewSet):
    queryset = AnalysisRequest.objects.all().order_by('-created_at')
    serializer_class = AnalysisRequestSerializer

    def perform_create(self, serializer):
        # 1) 새로운 AnalysisRequest 인스턴스 생성
        req = serializer.save()

        # 2) 생성 직후에 생성된 task들을 조회
        site_task: AnalysisTask = req.tasks.get(task_type='site')
        captcha_task: AnalysisTask = req.tasks.get(task_type='captcha')
        packet_task: AnalysisTask = req.tasks.get(task_type='packet')

        # 3) 1차: run_site → 결과에 is_phishing, has_captcha 정보가 찍힌다
        run_site(site_task)
        site_task.refresh_from_db()  # run_site가 DB를 업데이트했으므로 최신화

        is_phishing = site_task.result.get('is_phishing', False)
        has_captcha = site_task.result.get('has_captcha', False)

        # 4) 만약 피싱 사이트로 판단되면, 캡차와 패킷 작업은 건너뛰고 skipped 처리
        if is_phishing:
            # captcha 작업 생략
            _update(
                captcha_task,
                status='skipped',
                result={'reason': 'Site was classified as phishing; skipping captcha bypass.'},
                end=True
            )
            # packet 작업 생략
            _update(
                packet_task,
                status='skipped',
                result={'reason': 'Site was classified as phishing; skipping packet analysis.'},
                end=True
            )
            return

        # 5) 피싱이 아니면, 2차: 캡차 유무 검사(has_captcha==True/False)
        if has_captcha:
            # 5-1) run_captcha → result에 bypass_success 여부가 찍힐 것
            run_captcha(captcha_task)
            captcha_task.refresh_from_db()

            bypass_success = captcha_task.result.get('bypass_success', False)
            if bypass_success:
                # 5-2) 우회 성공했으면 packet 분석으로 넘어감
                run_packet(packet_task)
            else:
                # 우회 실패 시 packet 작업 skipped
                _update(
                    packet_task,
                    status='skipped',
                    result={'reason': 'Captcha bypass failed; skipping packet analysis.'},
                    end=True
                )
        else:
            # 6) 캡차가 없으면 바로 패킷 분석 실행
            _update(
                captcha_task,
                status='skipped',
                result={'reason': 'No captcha detected; skipping captcha bypass.'},
                end=True
            )
            run_packet(packet_task)


class AnalysisTaskViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AnalysisTask.objects.all()
    serializer_class = AnalysisTaskSerializer
