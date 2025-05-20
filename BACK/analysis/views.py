from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import AnalysisRequest, AnalysisTask
from .serializers import AnalysisRequestSerializer, AnalysisTaskSerializer
from .utils import run_site, run_packet, run_captcha

class AnalysisRequestViewSet(viewsets.ModelViewSet):
    queryset = AnalysisRequest.objects.all().order_by('-created_at')
    serializer_class = AnalysisRequestSerializer

    def perform_create(self, serializer):
        req = serializer.save()
        # 세 작업을 동기로 즉시 실행
        for task in req.tasks.all():
            if task.task_type == 'site':
                run_site(task)
            elif task.task_type == 'packet':
                run_packet(task)
            elif task.task_type == 'captcha':
                run_captcha(task)

class AnalysisTaskViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AnalysisTask.objects.all()
    serializer_class = AnalysisTaskSerializer
