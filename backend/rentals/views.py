from rest_framework import viewsets
from .serializers import RentSerializer,RenewRentSerializer
from .permissions import IsOwnerOrAdmin
from .models import Rent
from django.db import transaction
from django.core.mail import send_mail
from rest_framework.response import Response
from rest_framework.decorators import action

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

        #Email de confirmación tras hacer reserva
        send_mail(
            subject=f"Confirmacion de reserva de {rent.product.name}",
            message=f"Hola {rent.user.full_name}, tu reserva de {rent.product.name} se ha realizado correctamente."
                    f"Tienes desde el {rent.started_at} hasta el {rent.ended_at} para disfrutarlo." , 
            from_email="",#email desde el que se mande
            recipient_list=[rent.user.email],
            fail_silently=True,
        )    

    @action(detail=True,methods=["post"])
    @transaction.atomic
    def cancel(self,request,pk=None):
        rent = self.get_object()

        #Validación de estado y cancelación en BBDD
        rent.cancel()
        return Response({"status":"Reserva cancelada correctamente."})

    @action(detail=True,methods=["post"])
    @transaction.atomic
    def renew(self,request,pk=None):
        rent=self.get_object()

        #Validación de fields status y ended_at
        serializer=RenewRentSerializer(data=request.data,context={"rent":rent})
        serializer.is_valid(raise_exception=True)

        #Renovación de alquiler en base de datos (método renew de models)
        rent.renew(serializer.validated_data["ended_at"])
        return Response({"status":"Reserva renovada."})

    @action(detail=True,methods=["post"])
    @transaction.atomic
    def pickup(self,request,pk=None):
        rent=self.get_object()

        rent.pickup()
        return Response({"status":"Producto recogido correctamente."})

    @action(detail=True,methods=["post"])
    @transaction.atomic
    def complete(self,request,pk=None):
        rent=self.get_object()

        rent.complete()
        return Response({"status":"Producto devuelto correctamente."})


