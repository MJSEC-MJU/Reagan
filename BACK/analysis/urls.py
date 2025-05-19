from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import AnalysisRequestViewSet, AnalysisTaskViewSet

router = DefaultRouter()
router.register(r'analysis-requests', AnalysisRequestViewSet, basename='analysisrequest')
router.register(r'analysis-tasks', AnalysisTaskViewSet, basename='analysistask')

urlpatterns = [
    path('', include(router.urls))
    ]
