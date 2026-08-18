from django.shortcuts import render
from rest_framework import viewsets
from .serializers import RentSerializer
from .permissions import IsOwnerOrAdmin
from .models import Rent

# Create your views here.
class RentViewSet(viewsets.ModelViewSet):
    serializer_class = RentSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Rent.objects.all()
        return Rent.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)