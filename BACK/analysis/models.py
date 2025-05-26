from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class AnalysisRequest(models.Model):
    site_url = models.URLField()
    overall_status = models.CharField(max_length=16, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Request {self.id} - {self.site_url}'

class AnalysisTask(models.Model):
    TASK_CHOICES = [
        ('site', 'Site'),
        ('packet', 'Packet'),
        ('captcha', 'Captcha'),
    ]
    request = models.ForeignKey(
        AnalysisRequest,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    task_type = models.CharField(max_length=16, choices=TASK_CHOICES)
    status = models.CharField(max_length=16, default='pending')
    result = models.JSONField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.request.id}-{self.task_type}'


@receiver(post_save, sender=AnalysisTask)
def update_request_status(sender, instance, **kwargs):
    req = instance.request
    statuses = req.tasks.values_list('status', flat=True)
    if 'failed' in statuses:
        req.overall_status = 'failed'
    elif all(s == 'finished' for s in statuses):
        req.overall_status = 'completed'
    elif 'running' in statuses:
        req.overall_status = 'running'
    else:
        req.overall_status = 'pending'
    req.save()
