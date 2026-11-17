from rest_framework import serializers
from .models import Picture, Product


class PictureSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        if not attrs.get("product") and not attrs.get("news"):
            raise serializers.ValidationError(
                "La imagen debe estar asociada a un producto o a una noticia."
            )
        if attrs.get("product") and attrs.get("news"):
            raise serializers.ValidationError(
                "La imagen no puede pertenecer a un producto y a una noticia a la vez."
            )
        return attrs

    class Meta:
        model = Picture
        fields = ["id", "product", "news", "url"]


class ProductSerializer(serializers.ModelSerializer):
    pictures = PictureSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "description", "stock", "pictures"]