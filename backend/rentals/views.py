from rest_framework import viewsets
from .serializers import RentSerializer,RenewRentSerializer
from .permissions import IsOwnerOrAdmin
from .models import Rent
from django.db import transaction
from django.core.mail import send_mail
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAdminUser

def _run_model_action(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except DjangoValidationError as exc:
        detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
        raise DRFValidationError(detail)

# Create your views here.
class RentViewSet(mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,):
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
        rent = _run_model_action(serializer.save, user=self.request.user)
        
        #Descontar de stock al hacer reserva
        rent.product.decrease_stock()

        #Email de confirmación tras hacer reserva
        user_name = getattr(rent.user, "full_name", "") or rent.user.email
        send_mail(
            subject=f"Confirmacion de reserva de {rent.product.name}",
            message=f"Hola {user_name}, tu reserva de {rent.product.name} se ha realizado correctamente."
                    f"Tienes desde el {rent.started_at} hasta el {rent.ended_at} para disfrutarlo." , 
            from_email=None,#email desde el que se mande
            recipient_list=[rent.user.email],
            fail_silently=True,
        )    

    @action(detail=True,methods=["post"])
    @transaction.atomic
    def cancel(self,request,pk=None):
        rent = self.get_object()

        #Validación de estado y cancelación en BBDD
        _run_model_action(rent.cancel)
        return Response({"status":"Reserva cancelada correctamente."})

    @action(detail=True,methods=["post"])
    @transaction.atomic
    def renew(self,request,pk=None):
        rent=self.get_object()

        #Validación de fields status y ended_at
        serializer=RenewRentSerializer(data=request.data,context={"rent":rent})
        serializer.is_valid(raise_exception=True)

        #Renovación de alquiler en base de datos (método renew de models)
        _run_model_action(rent.renew, serializer.validated_data["ended_at"])
        return Response({"status":"Reserva renovada."})

    @action(detail=True,methods=["post"],permission_classes=[IsAdminUser])
    @transaction.atomic
    def pickup(self,request,pk=None):
        rent=self.get_object()

        _run_model_action(rent.pickup)
        return Response({"status":"Producto recogido correctamente."})

    @action(detail=True,methods=["post"],permission_classes=[IsAdminUser])
    @transaction.atomic
    def complete(self,request,pk=None):
        rent=self.get_object()

        _run_model_action(rent.complete)
        return Response({"status":"Producto devuelto correctamente."})


