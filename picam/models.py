from django.db import models

# Create your models here.

class Detection(models.Model):
    """
    객체 감지 결과를 저장하는 모델
    """
    image = models.ImageField(upload_to='detections/')
    result_image = models.ImageField(upload_to='results/', blank=True, null=True)
    objects_detected = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Detection {self.id} at {self.created_at}"