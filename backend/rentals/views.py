from rest_framework import viewsets
from .serializers import RentSerializer
from .permissions import IsOwnerOrAdmin
from .models import Rent
from django.db import transaction

# Create your views here.
class RentViewSet(viewsets.ModelViewSet):
    serializer_class = RentSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Rent.objects.all()
        return Rent.objects.filter(user=user)

    @transaction.atomic
    def perform_create(self, serializer):
        #Guarda la entidad del alquiler al crearlo
        rent = serializer.save(user=self.request.user)
        #Descontar de stock al hacer reserva
        rent.product.decrease_stock()