from django.shortcuts import render
from rest_framework import viewsets
from .models import Picture, Product
from .permissions import IsAdminOrReadOnly
from .serializers import PictureSerializer, ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]


class PictureViewSet(viewsets.ModelViewSet):
    queryset = Picture.objects.all()
    serializer_class = PictureSerializer
    permission_classes = [IsAdminOrReadOnly]