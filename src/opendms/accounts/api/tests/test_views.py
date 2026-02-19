from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from rest_framework import status

from opendms.accounts.tests.factories import UserFactory

User = get_user_model()


class LoginViewTest(TestCase):
    def setUp(self):
        self.path = reverse("api:v1:accounts:login")

    def test_incorrect_login(self):
        response = self.client.post(
            self.path, data={"username": "johndoe", "password": "incorrect"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["non_field_errors"][0],
            _("Unable to log in with provided credentials."),
        )

    def test_correct_login(self):
        user = UserFactory.create(username="johndoe", password="s3cret")
        response = self.client.post(
            self.path, data={"username": "johndoe", "password": "s3cret"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["is_authenticated"], True)
        self.assertEqual(response.data["user"]["pk"], user.pk)


class LogoutViewTest(TestCase):
    def setUp(self):
        self.path = reverse("api:v1:accounts:logout")

    def test_not_logged_in(self):
        self.client.get(self.path)
        response = self.client.get(reverse("api:v1:accounts:whoami"))
        self.assertFalse(response.data["is_authenticated"])

    def test_logged_in(self):
        user = UserFactory.create()
        self.client.force_login(user)
        response = self.client.get(reverse("api:v1:accounts:whoami"))
        self.assertTrue(response.data["is_authenticated"])

        self.client.get(self.path)
        response = self.client.get(reverse("api:v1:accounts:whoami"))
        self.assertFalse(response.data["is_authenticated"])


class WhoAmIViewTest(TestCase):
    def setUp(self):
        self.path = reverse("api:v1:accounts:whoami")

    def test_whoami_anonymous_user(self):
        response = self.client.get(self.path)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_authenticated"])
        self.assertIsNone(response.data["user"])

    def test_whoami_authenticated_user(self):
        user = UserFactory.create()
        self.client.force_login(user)
        response = self.client.get(self.path)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_authenticated"])
        self.assertEqual(response.data["user"]["pk"], user.pk)
