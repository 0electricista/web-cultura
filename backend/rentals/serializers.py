from rest_framework import serializers
from .models import Rent

#Validación de datos para acciones CRUD (general).
class RentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rent 
        fields = ["id", "user", "product", "started_at", "ended_at","status"]
        read_only_fields = ["id", "user","status"]

    def validate_product(self,value):
        if value.stock <=0:
            raise serializers.ValidationError("No quedan unidades disponibles de este producto.")
        return value

#Validación de la nueva fecha final introducida al renovar un alquiler (acción renew).
class RenewRentSerializer(serializers.Serializer):
    ended_at=serializers.DateField(required=True)

    #Validar que fecha de fin nueva no es ni null ni anterior a la actual
    def validate_ended_at(self,value):
        rent=self.context["rent"]
        if value<=rent.ended_at: 
            raise serializers.ValidationError("La nueva fecha introducida debe ser posterior a la fecha de devolución actual.")

        return value

    def validate(self,attrs):
        rent=self.context["rent"]
        if rent.status in ["CANCELLED","COMPLETED"]:
            raise serializers.ValidationError(f"No se puede renovar una fecha en estado {rent.status}")

        return attrs

