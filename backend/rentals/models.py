from django.db import models
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError

# Create your models here.
class Rent(models.Model):
    STATUS_CHOICES = [("PENDING","pendiente"),("ACTIVE","activo"),("COMPLETED","completado"),("CANCELLED","cancelado")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user')
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name='rent')
    started_at = models.DateField()
    ended_at = models.DateField()
    status = models.CharField(choices=STATUS_CHOICES,default="PENDING")

    def renew(self,new_end_date):
        self.ended_at=new_end_date
        self.save()

    #Actualización de field status en BBDD y validación del campo.
    def cancel(self):
        if self.status in ["CANCELLED","COMPLETED"]:
            raise ValidationError(f"No se puede cancelar en estado {self.status}.")
        self.status="CANCELLED"
        self.product.increase_stock()
        self.save()

    def pickup(self):
        if self.status !="PENDING":
            raise ValidationError(f"No se puede recoger un alquiler en estado {self.status}.")
        self.status="ACTIVE"
        self.save()

    def complete(self):
        if self.status !="ACTIVE":
            raise ValidationError(f"No se puede dar por devuelto un alquiler en estado {self.status}.")
        self.status="COMPLETE"
        self.product.increase_stock()
        self.product.save()
        self.save()
    

    def __str__(self):
        return f"Alquiler de {self.product} ({self.user}) - {self.started_at}/{self.ended_at}"