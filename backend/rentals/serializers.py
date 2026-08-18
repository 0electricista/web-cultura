from rest_framework import serializers
from .models import Rent

class RentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rent 
        fields = ["id", "user", "product", "started_at", "ended_at"]
        read_only_fields = ["id", "user"]