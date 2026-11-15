from rest_framework import serializers
from .models import News


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['id', 'user', 'title', 'subtitle', 'text']
        read_only_fields = ['id', 'user']