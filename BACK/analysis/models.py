from django.db import models
from django.utils import timezone

class AnalysisRequest(models.Model):
    site_url = models.URLField()
    overall_status = models.CharField(max_length=16, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

class AnalysisTask(models.Model):
    TASK_CHOICES = [
        ('site', 'Site'),
        ('packet', 'Packet'),
        ('captcha', 'Captcha'),
    ]
    request = models.ForeignKey(AnalysisRequest, on_delete=models.CASCADE, related_name='tasks')
    task_type = models.CharField(max_length=16, choices=TASK_CHOICES)
    status = models.CharField(max_length=16, default='pending')
    result = models.JSONField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.request.id}-{self.task_type}'
