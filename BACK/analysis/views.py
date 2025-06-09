# your_app/views.py

from rest_framework import viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import AllowAny

from .models import AnalysisRequest, AnalysisTask, White_list
from .serializers import AnalysisRequestSerializer, AnalysisTaskSerializer
from .utils import run_site, run_captcha, run_packet, _update


class AnalysisRequestViewSet(viewsets.ModelViewSet):
    """
    익명 사용자도 POST로 AnalysisRequest 생성이 가능하도록,
    SessionAuthentication(CSRF 검사) 대신 BasicAuthentication만 사용하고,
    permission은 AllowAny 로 설정합니다.
    """
    queryset = AnalysisRequest.objects.all().order_by('-created_at')
    serializer_class = AnalysisRequestSerializer

    authentication_classes = [BasicAuthentication]
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # 1) 새로운 AnalysisRequest 인스턴스 생성
        req = serializer.save()

        # URL 가져오기
        url = req.site_url  # serializer에 정의된 URL 필드명이 다르다면 여기를 맞춰주세요.

        # 2) 생성 직후에 생성된 task들을 조회
        site_task: AnalysisTask = req.tasks.get(task_type='site')
        captcha_task: AnalysisTask = req.tasks.get(task_type='captcha')
        packet_task: AnalysisTask = req.tasks.get(task_type='packet')

        # 3) 1차: run_site → 결과에 is_phishing, has_captcha 정보가 찍힌다
        run_site(site_task)
        site_task.refresh_from_db()  # run_site가 DB를 업데이트했으므로 최신화

        is_phishing = site_task.result.get('is_phishing', False)
        has_captcha = site_task.result.get('has_captcha', False)

        if White_list.objects.filter(site_url=url).exists():
            _update(
                site_task,
                status='skipped',
                result={'is_phishing': False,
                        'phishing_confidence': 0.0},
                end=True
            )
            _update(
                captcha_task,
                status='skipped',
                result={'is_phishing': False,
                        'phishing_confidence': 0.0},
                end=True
            )
            _update(
                packet_task,
                status='skipped',
                result={'is_phishing': False,
                        'phishing_confidence': 0.0},
                end=True
            )

            req.overall_status = 'completed'
            req.save()
            return AnalysisRequest


        # 4) 만약 피싱 사이트로 판단되면, 캡차와 패킷 작업은 건너뛰고 skipped 처리
        # if is_phishing:
        #     _update(
        #         captcha_task,
        #         status='skipped',
        #         result={'reason': 'Site was classified as phishing; skipping captcha bypass.'},
        #         end=True
        #     )
        #     _update(
        #         packet_task,
        #         status='skipped',
        #         result={'reason': 'Site was classified as phishing; skipping packet analysis.'},
        #         end=True
        #     )

        #     req.overall_status = 'completed'
        #     req.save()
        #     return AnalysisRequest

        # 5) 피싱이 아니면, 2차: 캡차 유무 검사
        if has_captcha:
            run_captcha(captcha_task)
            captcha_task.refresh_from_db()

            bypass_success = captcha_task.result.get('bypass_success', False)
            if bypass_success:
                run_packet(packet_task)
            else:
                _update(
                    packet_task,
                    status='skipped',
                    result={'reason': 'Captcha bypass failed; skipping packet analysis.'},
                    end=True
                )

            req.overall_status = 'completed'
            req.save()
            return AnalysisRequest
        else:
            # 6) 캡차가 없으면 바로 패킷 분석 실행, captcha_task는 skipped 처리
            _update(
                captcha_task,
                status='skipped',
                result={'reason': 'No captcha detected; skipping captcha bypass.'},
                end=True
            )
            run_packet(packet_task)

            req.overall_status = 'completed'
            req.save()
            return AnalysisRequest
    


class AnalysisTaskViewSet(viewsets.ReadOnlyModelViewSet):
    """
    AnalysisTask는 조회 전용(API GET)만 허용
    """
    queryset = AnalysisTask.objects.all()
    serializer_class = AnalysisTaskSerializer
