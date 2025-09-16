# chat/models.py
from django.db import models
from django.contrib.auth.models import User

class Message(models.Model):
    sender = models.ForeignKey(User, related_name="sent_messages", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="received_messages", on_delete=models.CASCADE)
    message = models.TextField()
    file = models.FileField(upload_to='chat_files/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.sender} → {self.receiver}: {self.message[:30]}"
    
    def is_image(self):
        return self.file and self.file.url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
    
    def is_video(self):
        return self.file and self.file.url.lower().endswith(('.mp4', '.webm', '.ogg'))

