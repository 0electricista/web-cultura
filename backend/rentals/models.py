from django.db import models
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

# Create your models here.
class Rent(models.Model):
    STATUS_CHOICES = [("PENDING","pendiente"),("ACTIVE","activo"),("COMPLETED","completado"),("CANCELLED","cancelado")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user')
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name='rent')
    started_at = models.DateField()
    ended_at = models.DateField()
    status = models.CharField(choices=STATUS_CHOICES,default="PENDING")

    #reglas de negocio
    def _validate_dates(self):
        #fechas no rellenadas
        if not self.started_at or not self.ended_at:
            return

        #fecha fin posterior a fecha inicio
        if self.ended_at <= self.started_at:
            raise ValidationError({"ended_at":"La fecha de devolución no puede ser anterior a la fecha de inicio."})
        
        #fecha de inicio debe ser a futuro
        if not self.pk and self.started_at < timezone.now.date():
            raise ValidationError({"started_at":"La fecha de inicion no puede ser anterior al día de hoy."})

        #la duracion del alquiler va a ser de un día como mínimo
        if (self.ended_at-self.started_at).days<1:
            raise ValidationError({"ended_at":"El alquiler no puede ser de menos de 24 horas."})

        #la duracion del alquilar no va a sobrepasar la semana
        if (self.ended_at-self.started_at).days>7:
            raise ValidationError({"ended_at":"El alquiler no puede ser de más de una semana."})

    def _validate_stock(self):
        #debe existir stock suficiente antes de reservar
        if not self.pk:
            if self.product and self.product.stock <= 0:
                raise ValidationError({"product":f"El producto '{self.product.name}' no tiene unidades disponibles."})

        #aunque haya stock no pueden coincidir reservas
        if not(self.product_id and self.started_at and self.ended_at):
            return

        overlapping_rents=Rent.objects.filter(product=self.product,status=["PENDING","ACTIVE"],started_at=self.ended_at,ended_at=self.started_at)
        if self.pk:
            overlapping_rents = overlapping_rents.exclude(pk=self.pk)
        if overlapping_rents.exists():
            raise ValidationError({"started_at":"El producto ya no está disponible en el rango de fechas seleccionado."})

    def clean(self):
        self._validate_dates()
        self._validate_stock()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args,**kwargs)

    #acciones customizadas
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

