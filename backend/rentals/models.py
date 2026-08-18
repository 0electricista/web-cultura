from django.db import models
import uuid
from django.conf import settings

# Create your models here.
class Rent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user')
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name='rent')
    started_at = models.DateField()
    ended_at = models.DateField()

    def __str__(self):
        return f"Alquiler de {self.product} ({self.user}) - {self.started_at}/{self.ended_at}"