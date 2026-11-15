from django.db import models
import uuid
from django.core.exceptions import ValidationError

# Create your models here.
# No está para nada completo solo he incluido algunas cosas que me son necesarias para llamar en rentals. Miguel

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    stock = models.PositiveIntegerField(default=1)

    def decrease_stock(self):
        self.stock-=1 if self.stock>0 else 0
        self.save()

    def increase_stock(self):
        self.stock+=1
        self.save()

    def __str__(self):
        return self.name


class Picture(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="pictures",
        null=True,
        blank=True,
    )
    news = models.ForeignKey(
        "news.News",
        on_delete=models.CASCADE,
        related_name="pictures",
        null=True,
        blank=True,
    )
    url = models.URLField(max_length=500)
    # image = models.ImageField(upload_to="pictures/")

    def clean(self):
        super().clean()
        if not self.product and not self.news:
            raise ValidationError("La imagen debe estar asociada a un producto o a una noticia.")
        if self.product and self.news:
            raise ValidationError("La imagen no puede pertenecer a un producto y a una noticia a la vez.")

    def __str__(self):
        target = self.product or self.news
        return f"Imagen de {target}"