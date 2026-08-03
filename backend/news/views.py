from rest_framework import viewsets
from .models import News
from .serializers import NewsSerializer
from .permissions import IsOwnerOrAdminOrReadOnly


class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]

    def perform_create(self, serializer):
        # Asigna automáticamente el usuario autenticado como dueño de la noticia
        serializer.save(user=self.request.user)
