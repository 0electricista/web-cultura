from django.test import TestCase

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Picture, Product

User = get_user_model()


class CatalogCRUDAndPermissionsTestCase(APITestCase):
    """
    Batería completa de pruebas automatizadas para el módulo de Catálogo (Product y Picture)
    y Permisos (IsAdminOrReadOnly), equivalente a la colección de Postman.
    """

    def setUp(self):
        # 1. Crear Usuario Admin / Staff (Con permisos de escritura)
        self.admin_user = User.objects.create_user(
            email='admin_catalogo@cultura.test',
            password='ClaveSegura123!',
            full_name='Carlos Admin (Staff)',
            is_staff=True
        )

        # 2. Crear Usuario Normal (Solo lectura)
        self.normal_user = User.objects.create_user(
            email='usuario_lector@cultura.test',
            password='ClaveSegura123!',
            full_name='Ana Lectora (Usuario Normal)',
            is_staff=False
        )

        # Datos de prueba para productos
        self.product_data = {
            'name': 'Cámara Réflex Canon EOS',
            'description': 'Cámara profesional disponible para alquiler cultural.',
            'stock': 5
        }

    # -------------------------------------------------------------------------
    # 2. Operaciones CRUD de Productos por Admin (Staff)
    # -------------------------------------------------------------------------

    def test_2_1_listar_productos_publicos(self):
        """2.1 Listar Productos Públicos (GET All) -> 200 OK"""
        url = reverse('product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), list)

    def test_2_2_crear_producto_como_admin(self):
        """2.2 Crear Producto como Admin (POST) -> 201 Created"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-list')
        response = self.client.post(url, self.product_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['name'], self.product_data['name'])
        self.assertEqual(response.data['stock'], self.product_data['stock'])

    def test_2_3_obtener_producto_por_id(self):
        """2.3 Obtener Producto por ID (GET Detail) -> 200 OK"""
        product = Product.objects.create(**self.product_data)
        url = reverse('product-detail', kwargs={'pk': product.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['id']), str(product.id))

    def test_2_4_actualizacion_completa_producto_por_admin(self):
        """2.4 Actualización Completa por Admin (PUT) -> 200 OK"""
        product = Product.objects.create(**self.product_data)
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-detail', kwargs={'pk': product.id})

        updated_data = {
            'name': 'Cámara Réflex Canon EOS (Editada)',
            'description': 'Descripción actualizada por el administrador.',
            'stock': 10
        }
        response = self.client.put(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], updated_data['name'])
        self.assertEqual(response.data['stock'], updated_data['stock'])

    def test_2_5_actualizacion_parcial_producto_por_admin(self):
        """2.5 Actualización Parcial por Admin (PATCH) -> 200 OK"""
        product = Product.objects.create(**self.product_data)
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-detail', kwargs={'pk': product.id})

        patch_data = {'stock': 2}
        response = self.client.patch(url, patch_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['stock'], patch_data['stock'])

    # -------------------------------------------------------------------------
    # 3. Operaciones CRUD y Validaciones de Imágenes (Picture)
    # -------------------------------------------------------------------------

    def test_3_1_crear_imagen_asociada_a_producto_como_admin(self):
        """3.1 Crear Imagen de Producto como Admin (POST) -> 201 Created"""
        product = Product.objects.create(**self.product_data)
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('picture-list')

        picture_data = {
            'product': str(product.id),
            'url': 'https://ejemplo.com/imagenes/camara-canon.jpg'
        }
        response = self.client.post(url, picture_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(response.data['product']), str(product.id))

        # Verificar que al consultar el producto aparece la imagen anidada
        product_url = reverse('product-detail', kwargs={'pk': product.id})
        product_response = self.client.get(product_url)
        self.assertEqual(len(product_response.data['pictures']), 1)

    def test_3_2_crear_imagen_sin_producto_ni_noticia_falla(self):
        """3.2 Crear Imagen Huérfana (sin product ni news) -> 400 Bad Request"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('picture-list')

        invalid_picture = {'url': 'https://ejemplo.com/imagenes/huerfana.jpg'}
        response = self.client.post(url, invalid_picture, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------------------
    # 4. Pruebas de Autorización y Seguridad (Usuario Normal sin Permisos)
    # -------------------------------------------------------------------------

    def test_4_1_lectura_por_usuario_normal_permitida(self):
        """4.1 Lectura por Usuario Normal (GET Detail) -> 200 OK (Lectura pública)"""
        product = Product.objects.create(**self.product_data)
        self.client.force_authenticate(user=self.normal_user)
        url = reverse('product-detail', kwargs={'pk': product.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_4_2_intento_post_por_usuario_normal_bloqueado(self):
        """4.2 Intento de POST por Usuario Normal -> 403 Forbidden"""
        self.client.force_authenticate(user=self.normal_user)
        url = reverse('product-list')

        response = self.client.post(url, self.product_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_4_3_intento_put_por_usuario_normal_bloqueado(self):
        """4.3 Intento de PUT por Usuario Normal -> 403 Forbidden"""
        product = Product.objects.create(**self.product_data)
        self.client.force_authenticate(user=self.normal_user)
        url = reverse('product-detail', kwargs={'pk': product.id})

        unauthorized_data = {
            'name': 'Producto hackeado por Usuario Normal',
            'description': 'Intento no autorizado',
            'stock': 999
        }
        response = self.client.put(url, unauthorized_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_4_4_intento_patch_por_usuario_normal_bloqueado(self):
        """4.4 Intento de PATCH por Usuario Normal -> 403 Forbidden"""
        product = Product.objects.create(**self.product_data)
        self.client.force_authenticate(user=self.normal_user)
        url = reverse('product-detail', kwargs={'pk': product.id})

        response = self.client.patch(url, {'stock': 0}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_4_5_intento_delete_por_usuario_normal_bloqueado(self):
        """4.5 Intento de DELETE por Usuario Normal -> 403 Forbidden"""
        product = Product.objects.create(**self.product_data)
        self.client.force_authenticate(user=self.normal_user)
        url = reverse('product-detail', kwargs={'pk': product.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # -------------------------------------------------------------------------
    # 5. Limpieza del Recurso y Pruebas de Error
    # -------------------------------------------------------------------------

    def test_5_1_eliminar_producto_por_admin(self):
        """5.1 Eliminar Producto por Admin (DELETE) -> 204 No Content"""
        product = Product.objects.create(**self.product_data)
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-detail', kwargs={'pk': product.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(id=product.id).exists())

    def test_5_2_verificar_eliminacion_get_404(self):
        """5.2 Verificar Eliminación (GET Detail) -> 404 Not Found"""
        product = Product.objects.create(**self.product_data)
        product_id = product.id
        product.delete()

        url = reverse('product-detail', kwargs={'pk': product_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_5_3_crear_producto_sin_autenticacion_falla(self):
        """5.3 Crear Producto Sin Autenticación (POST) -> 401 Unauthorized"""
        url = reverse('product-list')
        response = self.client.post(url, self.product_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)