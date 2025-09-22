from django.db import models

# Create your models here.
from django.db import models

class Video(models.Model):
    source = models.CharField(max_length=50)  # 'house' or 'senate'
    title = models.CharField(max_length=255, default="")
    url = models.URLField(unique=True)
    local_path = models.CharField(max_length=255, default="")
    audio_file_path = models.CharField(max_length=255, default="")
    downloaded = models.BooleanField(default=False)
    transcribed = models.BooleanField(default=False)
    cleaned = models.BooleanField(default=False)
    transcript = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

