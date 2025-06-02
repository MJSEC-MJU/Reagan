from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import AnalysisRequestViewSet, AnalysisTaskViewSet

router = DefaultRouter()
router.register(r'analysis-requests', AnalysisRequestViewSet, basename='analysisrequest')
router.register(r'analysis-tasks', AnalysisTaskViewSet, basename='analysistask')

# 라우터의 경로만 반환하여 깔끔하게 설정
urlpatterns = router.urls

