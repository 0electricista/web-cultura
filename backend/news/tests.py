from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import News

User = get_user_model()


class NewsCRUDAndPermissionsTestCase(APITestCase):
    """
    Batería completa de pruebas automatizadas para el módulo de Noticias (News)
    y Permisos (IsOwnerOrAdminOrReadOnly), equivalente a la colección de Postman.
    """

    def setUp(self):
        # 1. Crear Usuario 1 (Propietario / Autor)
        self.user1 = User.objects.create_user(
            email='autor_noticias@cultura.test',
            password='ClaveSegura123!',
            full_name='Carlos Autor (Usuario 1)'
        )

        # 2. Crear Usuario 2 (No Autor / Lector)
        self.user2 = User.objects.create_user(
            email='usuario_intruso@cultura.test',
            password='ClaveSegura123!',
            full_name='Ana Lectora (Usuario 2)'
        )

        # Datos de prueba para noticias
        self.news_data = {
            'title': 'Noticia Exclusiva de Carlos (Usuario 1)',
            'subtitle': 'Novedades sobre la exposición de arte',
            'text': 'Esta noticia fue redactada por el Usuario 1. Solo el creador o un admin podrán modificarla.'
        }

    # -------------------------------------------------------------------------
    # 2. Operaciones CRUD por Usuario 1 (Propietario)
    # -------------------------------------------------------------------------

    def test_2_1_listar_noticias_publicas(self):
        """2.1 Listar Noticias Públicas (GET All) -> 200 OK"""
        url = reverse('news-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), list)

    def test_2_2_crear_noticia_como_usuario_1(self):
        """2.2 Crear Noticia como Usuario 1 (POST) -> 201 Created"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('news-list')
        response = self.client.post(url, self.news_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['title'], self.news_data['title'])

    def test_2_3_obtener_noticia_por_id(self):
        """2.3 Obtener Noticia por ID (GET Detail) -> 200 OK"""
        news = News.objects.create(user=self.user1, **self.news_data)
        url = reverse('news-detail', kwargs={'pk': news.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['id']), str(news.id))

    def test_2_4_actualizacion_completa_por_usuario_1(self):
        """2.4 Actualización Completa por Usuario 1 (PUT) -> 200 OK"""
        news = News.objects.create(user=self.user1, **self.news_data)
        self.client.force_authenticate(user=self.user1)
        url = reverse('news-detail', kwargs={'pk': news.id})

        updated_data = {
            'title': 'Noticia Editada por Usuario 1 (PUT)',
            'subtitle': 'Subtítulo modificado por el dueño',
            'text': 'El contenido ha sido actualizado legítimamente por el autor original.'
        }
        response = self.client.put(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], updated_data['title'])

    def test_2_5_actualizacion_parcial_por_usuario_1(self):
        """2.5 Actualización Parcial por Usuario 1 (PATCH) -> 200 OK"""
        news = News.objects.create(user=self.user1, **self.news_data)
        self.client.force_authenticate(user=self.user1)
        url = reverse('news-detail', kwargs={'pk': news.id})

        patch_data = {'subtitle': 'Subtítulo cambiado vía PATCH por el autor'}
        response = self.client.patch(url, patch_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['subtitle'], patch_data['subtitle'])

    # -------------------------------------------------------------------------
    # 3. Pruebas de Autorización y Seguridad (Usuario 2 sin Permisos)
    # -------------------------------------------------------------------------

    def test_3_1_lectura_por_usuario_2_permitida(self):
        """3.1 Lectura por Usuario 2 (GET Detail) -> 200 OK (Lectura pública)"""
        news = News.objects.create(user=self.user1, **self.news_data)
        self.client.force_authenticate(user=self.user2)
        url = reverse('news-detail', kwargs={'pk': news.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_3_2_intento_put_por_usuario_2_bloqueado(self):
        """3.2 Intento de PUT por Usuario 2 -> 403 Forbidden"""
        news = News.objects.create(user=self.user1, **self.news_data)
        self.client.force_authenticate(user=self.user2)
        url = reverse('news-detail', kwargs={'pk': news.id})

        unauthorized_data = {
            'title': 'Título hackeado por Usuario 2',
            'subtitle': 'Intento no autorizado',
            'text': 'El Usuario 2 no debería poder sobreescribir esta noticia.'
        }
        response = self.client.put(url, unauthorized_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_3_3_intento_patch_por_usuario_2_bloqueado(self):
        """3.3 Intento de PATCH por Usuario 2 -> 403 Forbidden"""
        news = News.objects.create(user=self.user1, **self.news_data)
        self.client.force_authenticate(user=self.user2)
        url = reverse('news-detail', kwargs={'pk': news.id})

        unauthorized_patch = {'subtitle': 'Subtítulo alterado de forma no autorizada por Usuario 2'}
        response = self.client.patch(url, unauthorized_patch, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_3_4_intento_delete_por_usuario_2_bloqueado(self):
        """3.4 Intento de DELETE por Usuario 2 -> 403 Forbidden"""
        news = News.objects.create(user=self.user1, **self.news_data)
        self.client.force_authenticate(user=self.user2)
        url = reverse('news-detail', kwargs={'pk': news.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # -------------------------------------------------------------------------
    # 4. Limpieza del Recurso y Pruebas de Error
    # -------------------------------------------------------------------------

    def test_4_1_eliminar_noticia_por_usuario_1(self):
        """4.1 Eliminar Noticia por Usuario 1 (DELETE) -> 204 No Content"""
        news = News.objects.create(user=self.user1, **self.news_data)
        self.client.force_authenticate(user=self.user1)
        url = reverse('news-detail', kwargs={'pk': news.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(News.objects.filter(id=news.id).exists())

    def test_4_2_verificar_eliminacion_get_404(self):
        """4.2 Verificar Eliminación (GET Detail) -> 404 Not Found"""
        news = News.objects.create(user=self.user1, **self.news_data)
        news_id = news.id
        news.delete()

        url = reverse('news-detail', kwargs={'pk': news_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_4_3_crear_noticia_sin_autenticacion_falla(self):
        """4.3 Crear Noticia Sin Autenticación (POST) -> 401 Unauthorized"""
        url = reverse('news-list')
        response = self.client.post(url, self.news_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
