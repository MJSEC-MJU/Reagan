from rest_framework import serializers
from .models import AnalysisRequest, AnalysisTask

class AnalysisTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisTask
        fields = '__all__'
        read_only_fields = ('status', 'result', 'started_at', 'finished_at')

class AnalysisRequestSerializer(serializers.ModelSerializer):
    tasks = AnalysisTaskSerializer(many=True, read_only=True)

    class Meta:
        model = AnalysisRequest
        fields = ('id', 'site_url', 'overall_status', 'created_at', 'updated_at', 'tasks')

    # POST /analysis-requests 시 자동으로 3개 작업 생성
    def create(self, validated_data):
        req = AnalysisRequest.objects.create(**validated_data)
        for t in ('site', 'packet', 'captcha'):
            AnalysisTask.objects.create(request=req, task_type=t)
        return req
