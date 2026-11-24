from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

PASSWORD = "ContraseñaSegura123!"


class BaseUsersAPITestCase(APITestCase):
    """
    Base común: limpia la caché antes de cada test.
    Los endpoints de auth tienen throttle ('auth': 5/min) y DRF guarda los contadores
    en la caché (LocMemCache), que persiste entre tests. Sin limpiarla, unos tests
    agotarían el límite de otros y fallarían de forma aleatoria (429).
    """

    def setUp(self):
        cache.clear()

    def crear_usuario(self, email="user@test.com", full_name="Usuario Test", **extra):
        return User.objects.create_user(
            email=email, password=PASSWORD, full_name=full_name, **extra
        )


# ---------------------------------------------------------------------------
# Modelo / Manager
# ---------------------------------------------------------------------------
class UserManagerTests(BaseUsersAPITestCase):
    def test_create_user_ok(self):
        user = self.crear_usuario()
        self.assertEqual(user.email, "user@test.com")
        self.assertTrue(user.check_password(PASSWORD))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_normaliza_dominio_del_email(self):
        user = User.objects.create_user(
            email="Test@EXAMPLE.COM", password=PASSWORD, full_name="X"
        )
        self.assertEqual(user.email, "Test@example.com")

    def test_create_user_sin_email_falla(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password=PASSWORD, full_name="X")

    def test_create_user_sin_password_deja_password_inutilizable(self):
        # Caso Google OAuth: sin contraseña
        user = User.objects.create_user(email="g@test.com", full_name="G")
        self.assertFalse(user.has_usable_password())

    def test_create_superuser_ok(self):
        admin = User.objects.create_superuser(
            email="admin@test.com", password=PASSWORD, full_name="Admin"
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_create_superuser_con_is_staff_false_falla(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="admin@test.com", password=PASSWORD, full_name="A", is_staff=False
            )

    def test_create_superuser_con_is_superuser_false_falla(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="admin@test.com",
                password=PASSWORD,
                full_name="A",
                is_superuser=False,
            )

    def test_email_duplicado_no_permitido(self):
        from django.db import IntegrityError, transaction

        self.crear_usuario()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.crear_usuario()

    def test_str_devuelve_email(self):
        self.assertEqual(str(self.crear_usuario()), "user@test.com")


# ---------------------------------------------------------------------------
# POST /api/users/register/
# ---------------------------------------------------------------------------
class RegisterEndpointTests(BaseUsersAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("user-register-list")
        self.payload = {
            "email": "nuevo@test.com",
            "password": PASSWORD,
            "full_name": "Nuevo Usuario",
        }

    def test_registro_ok_crea_usuario(self):
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "nuevo@test.com")
        self.assertEqual(response.data["full_name"], "Nuevo Usuario")
        self.assertTrue(User.objects.filter(email="nuevo@test.com").exists())

    def test_registro_no_devuelve_password(self):
        response = self.client.post(self.url, self.payload, format="json")
        self.assertNotIn("password", response.data)

    def test_registro_guarda_password_hasheada(self):
        self.client.post(self.url, self.payload, format="json")
        user = User.objects.get(email="nuevo@test.com")
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))

    def test_registro_no_permite_escalar_privilegios(self):
        # Un atacante intenta registrarse como admin enviando campos extra
        payload = {**self.payload, "is_staff": True, "is_superuser": True}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="nuevo@test.com")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_registro_es_publico_no_requiere_autenticacion(self):
        # Sin credenciales no debe dar 401/403
        response = self.client.post(self.url, self.payload, format="json")
        self.assertNotIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_registro_email_duplicado_falla(self):
        self.crear_usuario(email="nuevo@test.com")
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(User.objects.filter(email="nuevo@test.com").count(), 1)

    def test_registro_email_invalido_falla(self):
        self.payload["email"] = "esto-no-es-un-email"
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_registro_campos_obligatorios(self):
        for campo in ("email", "password", "full_name"):
            with self.subTest(campo=campo):
                cache.clear()  # evitar el throttle dentro del bucle
                payload = {k: v for k, v in self.payload.items() if k != campo}
                response = self.client.post(self.url, payload, format="json")

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(campo, response.data)

    def test_registro_body_vacio_falla(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registro_metodos_no_permitidos(self):
        # Solo existe POST (CreateModelMixin)
        self.assertEqual(
            self.client.get(self.url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )
        self.assertEqual(
            self.client.put(self.url, self.payload, format="json").status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(
            self.client.delete(self.url).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_registro_throttle_tras_5_peticiones(self):
        # scope 'auth' = 5/min: la sexta petición debe ser rechazada con 429
        for i in range(5):
            response = self.client.post(
                self.url,
                {**self.payload, "email": f"u{i}@test.com"},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            self.url, {**self.payload, "email": "u6@test.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


# ---------------------------------------------------------------------------
# GET /api/users/profile/me/
# ---------------------------------------------------------------------------
class ProfileMeEndpointTests(BaseUsersAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("user-profile-me")
        self.user = self.crear_usuario()

    def test_me_sin_autenticar_devuelve_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_devuelve_perfil_del_usuario_autenticado(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.user.id))
        self.assertEqual(response.data["email"], "user@test.com")
        self.assertEqual(response.data["full_name"], "Usuario Test")
        self.assertFalse(response.data["is_staff"])

    def test_me_solo_expone_campos_esperados(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(
            set(response.data.keys()), {"id", "email", "full_name", "is_staff"}
        )
        self.assertNotIn("password", response.data)

    def test_me_indica_is_staff_para_admin(self):
        admin = User.objects.create_superuser(
            email="admin@test.com", password=PASSWORD, full_name="Admin"
        )
        self.client.force_authenticate(user=admin)
        response = self.client.get(self.url)

        self.assertTrue(response.data["is_staff"])

    def test_me_devuelve_siempre_el_usuario_del_token_y_no_otro(self):
        otro = self.crear_usuario(email="otro@test.com", full_name="Otro")
        self.client.force_authenticate(user=otro)
        response = self.client.get(self.url)

        self.assertEqual(response.data["email"], "otro@test.com")

    def test_me_con_token_jwt_real(self):
        # Flujo completo: login -> access token -> perfil
        login = self.client.post(
            reverse("token_obtain_pair"),
            {"email": "user@test.com", "password": PASSWORD},
            format="json",
        )
        access = login.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "user@test.com")

    def test_me_con_token_invalido_devuelve_401(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer token.falso.invalido")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_metodos_no_permitidos(self):
        self.client.force_authenticate(user=self.user)
        for metodo in ("post", "put", "patch", "delete"):
            with self.subTest(metodo=metodo):
                response = getattr(self.client, metodo)(self.url)
                self.assertEqual(
                    response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
                )

    def test_profile_no_expone_ruta_por_id(self):
        # Solo existe /me/, nunca /profile/<id>/ (seguridad)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/users/profile/{self.user.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# POST /api/token/  y  POST /api/token/refresh/
# ---------------------------------------------------------------------------
class TokenEndpointsTests(BaseUsersAPITestCase):
    def setUp(self):
        super().setUp()
        self.login_url = reverse("token_obtain_pair")
        self.refresh_url = reverse("token_refresh")
        self.user = self.crear_usuario()

    def test_login_ok_devuelve_access_y_refresh(self):
        response = self.client.post(
            self.login_url,
            {"email": "user@test.com", "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_password_incorrecta_devuelve_401(self):
        response = self.client.post(
            self.login_url,
            {"email": "user@test.com", "password": "incorrecta"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)

    def test_login_usuario_inexistente_devuelve_401(self):
        response = self.client.post(
            self.login_url,
            {"email": "noexiste@test.com", "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_usuario_inactivo_devuelve_401(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(
            self.login_url,
            {"email": "user@test.com", "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_campos_faltantes_devuelve_400(self):
        response = self.client.post(self.login_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_usuario_google_sin_password_no_puede_entrar_por_password(self):
        User.objects.create_user(email="g@test.com", full_name="G")  # sin password
        response = self.client.post(
            self.login_url, {"email": "g@test.com", "password": ""}, format="json"
        )
        self.assertIn(
            response.status_code,
            (status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED),
        )

    def test_login_throttle_tras_5_peticiones(self):
        datos = {"email": "user@test.com", "password": "incorrecta"}
        for _ in range(5):
            r = self.client.post(self.login_url, datos, format="json")
            self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

        r = self.client.post(self.login_url, datos, format="json")
        self.assertEqual(r.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_refresh_ok_devuelve_nuevo_access(self):
        login = self.client.post(
            self.login_url,
            {"email": "user@test.com", "password": PASSWORD},
            format="json",
        )
        response = self.client.post(
            self.refresh_url, {"refresh": login.data["refresh"]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_refresh_con_token_invalido_devuelve_401(self):
        response = self.client.post(
            self.refresh_url, {"refresh": "token.invalido"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_sin_token_devuelve_400(self):
        response = self.client.post(self.refresh_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_no_acepta_un_access_token(self):
        login = self.client.post(
            self.login_url,
            {"email": "user@test.com", "password": PASSWORD},
            format="json",
        )
        response = self.client.post(
            self.refresh_url, {"refresh": login.data["access"]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# POST /api/users/google-login/
# ---------------------------------------------------------------------------
class GoogleLoginEndpointTests(BaseUsersAPITestCase):
    """Se mockea el servicio: NUNCA se debe llamar a Google en los tests."""

    def setUp(self):
        super().setUp()
        self.url = reverse("google-login")

    @patch("users.views.verify_google_token_and_create_user")
    def test_google_login_ok_devuelve_tokens(self, mock_service):
        mock_service.return_value = {"access": "a.b.c", "refresh": "d.e.f"}

        response = self.client.post(self.url, {"token": "token-google"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"access": "a.b.c", "refresh": "d.e.f"})
        mock_service.assert_called_once_with("token-google")

    @patch("users.views.verify_google_token_and_create_user")
    def test_google_login_token_invalido_devuelve_400(self, mock_service):
        mock_service.side_effect = ValueError("El token de Google es inválido")

        response = self.client.post(self.url, {"token": "malo"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    @patch("users.views.verify_google_token_and_create_user")
    def test_google_login_sin_token_devuelve_400_y_no_llama_al_servicio(
        self, mock_service
    ):
        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("token", response.data)
        mock_service.assert_not_called()

    @patch("users.views.verify_google_token_and_create_user")
    def test_google_login_token_vacio_devuelve_400(self, mock_service):
        response = self.client.post(self.url, {"token": ""}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_service.assert_not_called()

    def test_google_login_solo_acepta_post(self):
        self.assertEqual(
            self.client.get(self.url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @patch("users.views.verify_google_token_and_create_user")
    def test_google_login_throttle_tras_5_peticiones(self, mock_service):
        mock_service.return_value = {"access": "a", "refresh": "r"}
        for _ in range(5):
            r = self.client.post(self.url, {"token": "t"}, format="json")
            self.assertEqual(r.status_code, status.HTTP_200_OK)

        r = self.client.post(self.url, {"token": "t"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


# ---------------------------------------------------------------------------
# Servicio de Google (lógica que hay detrás del endpoint google-login)
# ---------------------------------------------------------------------------
class GoogleServiceTests(BaseUsersAPITestCase):
    """Se mockea id_token.verify_oauth2_token para simular la respuesta de Google."""

    TARGET = "users.services.id_token.verify_oauth2_token"

    def setUp(self):
        super().setUp()
        self.url = reverse("google-login")

    @patch(TARGET)
    def test_usuario_nuevo_se_crea_con_password_inutilizable(self, mock_verify):
        mock_verify.return_value = {
            "email": "nuevo@gmail.com",
            "sub": "google-123",
            "name": "Nuevo Google",
        }

        response = self.client.post(self.url, {"token": "x"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        user = User.objects.get(email="nuevo@gmail.com")
        self.assertEqual(user.google_id, "google-123")
        self.assertEqual(user.full_name, "Nuevo Google")
        self.assertFalse(user.has_usable_password())

    @patch(TARGET)
    def test_usuario_existente_sin_google_id_se_vincula(self, mock_verify):
        existente = self.crear_usuario(email="user@test.com")
        mock_verify.return_value = {
            "email": "user@test.com",
            "sub": "google-456",
            "name": "Da igual",
        }

        response = self.client.post(self.url, {"token": "x"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        existente.refresh_from_db()
        self.assertEqual(existente.google_id, "google-456")
        # Conserva su contraseña original y no se duplica
        self.assertTrue(existente.check_password(PASSWORD))
        self.assertEqual(User.objects.filter(email="user@test.com").count(), 1)

    @patch(TARGET)
    def test_usuario_con_google_id_no_se_sobrescribe(self, mock_verify):
        existente = self.crear_usuario(email="user@test.com", google_id="original")
        mock_verify.return_value = {
            "email": "user@test.com",
            "sub": "otro-id",
            "name": "X",
        }

        self.client.post(self.url, {"token": "x"}, format="json")

        existente.refresh_from_db()
        self.assertEqual(existente.google_id, "original")

    @patch(TARGET)
    def test_google_sin_name_usa_cadena_vacia(self, mock_verify):
        mock_verify.return_value = {"email": "sn@gmail.com", "sub": "g-789"}

        response = self.client.post(self.url, {"token": "x"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(User.objects.get(email="sn@gmail.com").full_name, "")

    @patch(TARGET)
    def test_token_rechazado_por_google_devuelve_400_sin_crear_usuario(
        self, mock_verify
    ):
        mock_verify.side_effect = ValueError("Token expired")

        response = self.client.post(self.url, {"token": "caducado"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(User.objects.count(), 0)

    @patch(TARGET)
    def test_tokens_devueltos_sirven_para_acceder_al_perfil(self, mock_verify):
        mock_verify.return_value = {
            "email": "flujo@gmail.com",
            "sub": "g-flujo",
            "name": "Flujo",
        }
        login = self.client.post(self.url, {"token": "x"}, format="json")

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = self.client.get(reverse("user-profile-me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "flujo@gmail.com")
