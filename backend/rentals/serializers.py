from rest_framework import serializers
from .models import Rent

class RentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rent 
        fields = ["id", "user", "product", "started_at", "ended_at"]
        read_only_fields = ["id", "user"]

    def validate_product(self,value):
        if value.stock <=0:
            raise serializers.ValidationError("No quedan unidades disponibles de este producto.")
        return value