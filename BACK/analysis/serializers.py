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
        # overall_status 자동 업데이트를 위해 write 지원
        fields = ('id', 'site_url', 'overall_status', 'created_at', 'updated_at', 'tasks')
        read_only_fields = ('created_at', 'updated_at')

    # 새로운 요청 생성 시 자동으로 3개 작업 생성
    def create(self, validated_data):
        req = AnalysisRequest.objects.create(**validated_data)
        # 태스크 타입에 맞춰 인스턴스 생성
        for t in ('site', 'packet', 'captcha'):
            AnalysisTask.objects.create(request=req, task_type=t)
        return req

