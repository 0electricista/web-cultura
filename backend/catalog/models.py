from django.db import models

# Create your models here.
# No está para nada completo solo he incluido algunas cosas que me son necesarias para llamar en rentals. Miguel
class Product(models.Model):
    stock = models.PositiveIntegerField(default=1)

    def decrease_stock(self):
        self.stock-=1 if self.stock>0 else 0
        self.save()

    def increase_stock(self):
        self.stock+=1
        self.save()
