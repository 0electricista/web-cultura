from django.test import TestCase
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Product
from .models import Rent

User = get_user_model()


class RentAPITests(APITestCase):
    def setUp(self):
        # Usuarios de prueba (normal, otro usuario y administrador)
        self.user = User.objects.create_user(
            email="usuario1@test.com",
            password="Password123!",
        )
        self.other_user = User.objects.create_user(
            email="usuario2@test.com",
            password="Password123!",
        )
        self.admin = User.objects.create_user(
            email="admin@test.com",
            password="Password123!",
            is_staff=True,
        )

        # Producto de prueba (si Product en catalog exige más campos como price o category, añádelos aquí)
        self.product = Product.objects.create(
            name="Cámara Réflex",
            stock=2,
        )

        self.today = timezone.now().date()
        self.list_url = reverse("rent-list")

    def _create_sample_rent(self, user=None, start_offset=1, end_offset=3, status_value="PENDING"):
        return Rent.objects.create(
            user=user or self.user,
            product=self.product,
            started_at=self.today + timedelta(days=start_offset),
            ended_at=self.today + timedelta(days=end_offset),
            status=status_value,
        )

    def test_unauthenticated_user_cannot_access(self):
        response = self.client.get(self.list_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_create_rent_success_and_decreases_stock(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "product": self.product.id,
            "started_at": str(self.today + timedelta(days=1)),
            "ended_at": str(self.today + timedelta(days=4)),
        }
        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Rent.objects.count(), 1)

        rent = Rent.objects.first()
        self.assertEqual(rent.user, self.user)
        self.assertEqual(rent.status, "PENDING")

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)

    def test_create_rent_with_past_date_returns_400(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "product": self.product.id,
            "started_at": str(self.today - timedelta(days=1)),
            "ended_at": str(self.today + timedelta(days=2)),
        }
        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("started_at", response.data)

    def test_create_rent_over_7_days_returns_400(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "product": self.product.id,
            "started_at": str(self.today + timedelta(days=1)),
            "ended_at": str(self.today + timedelta(days=10)),
        }
        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ended_at", response.data)

    def test_overlapping_rent_returns_400(self):
        self._create_sample_rent(user=self.other_user, start_offset=2, end_offset=5)

        self.client.force_authenticate(user=self.user)
        payload = {
            "product": self.product.id,
            "started_at": str(self.today + timedelta(days=3)),
            "ended_at": str(self.today + timedelta(days=6)),
        }
        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("started_at", response.data)

    def test_user_only_lists_own_rents_while_admin_sees_all(self):
        self._create_sample_rent(user=self.user, start_offset=1, end_offset=2)
        self._create_sample_rent(user=self.other_user, start_offset=4, end_offset=5)

        self.client.force_authenticate(user=self.user)
        user_response = self.client.get(self.list_url)
        self.assertEqual(len(user_response.data), 1)

        self.client.force_authenticate(user=self.admin)
        admin_response = self.client.get(self.list_url)
        self.assertEqual(len(admin_response.data), 2)

    def test_cancel_rent_restores_stock(self):
        rent = self._create_sample_rent(user=self.user)
        self.client.force_authenticate(user=self.user)

        cancel_url = reverse("rent-cancel", args=[rent.id])
        response = self.client.post(cancel_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rent.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(rent.status, "CANCELLED")
        self.assertEqual(self.product.stock, 3)

    def test_renew_rent_extends_end_date(self):
        rent = self._create_sample_rent(user=self.user, start_offset=1, end_offset=3)
        self.client.force_authenticate(user=self.user)

        new_end = self.today + timedelta(days=5)
        renew_url = reverse("rent-renew", args=[rent.id])
        response = self.client.post(renew_url, {"ended_at": str(new_end)}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rent.refresh_from_db()
        self.assertEqual(rent.ended_at, new_end)

    def test_pickup_and_complete_require_admin_and_restore_stock(self):
        rent = self._create_sample_rent(user=self.user)
        pickup_url = reverse("rent-pickup", args=[rent.id])
        complete_url = reverse("rent-complete", args=[rent.id])

        # Un usuario normal no puede marcar recogida
        self.client.force_authenticate(user=self.user)
        forbidden_resp = self.client.post(pickup_url)
        self.assertEqual(forbidden_resp.status_code, status.HTTP_403_FORBIDDEN)

        # El administrador sí puede marcar recogida y devolución
        self.client.force_authenticate(user=self.admin)
        pickup_resp = self.client.post(pickup_url)
        self.assertEqual(pickup_resp.status_code, status.HTTP_200_OK)
        rent.refresh_from_db()
        self.assertEqual(rent.status, "ACTIVE")

        complete_resp = self.client.post(complete_url)
        self.assertEqual(complete_resp.status_code, status.HTTP_200_OK)
        rent.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(rent.status, "COMPLETED")
        self.assertEqual(self.product.stock, 3)

    def test_delete_and_patch_methods_are_not_allowed(self):
        rent = self._create_sample_rent(user=self.user)
        self.client.force_authenticate(user=self.user)
        detail_url = reverse("rent-detail", args=[rent.id])

        self.assertEqual(self.client.delete(detail_url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.patch(detail_url, {}).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
