from django.db import models
import uuid
from users.models import User

class News(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user')
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    text = models.TextField()
    
    def __str__(self):
        return str(self.title)
