from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.tests import get_validation_errors, reverse

from opendms.accounts.tests.factories import UserFactory

User = get_user_model()


class LoginViewTest(APITestCase):
    def setUp(self):
        self.path = reverse("accounts:login")

    def test_incorrect_login(self):
        response = self.client.post(
            self.path, data={"username": "johndoe", "password": "incorrect"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            get_validation_errors(response, "nonFieldErrors"),
            {
                "name": "nonFieldErrors",
                "code": "authorization",
                "reason": _("Unable to log in with provided credentials."),
            },
        )

    def test_correct_login(self):
        user = UserFactory.create(username="johndoe", password="s3cret")
        response = self.client.post(
            self.path, data={"username": "johndoe", "password": "s3cret"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["is_authenticated"], True)
        self.assertEqual(response.data["user"]["pk"], user.pk)


class LogoutViewTest(APITestCase):
    def setUp(self):
        self.path = reverse("accounts:logout")

    def test_not_logged_in(self):
        self.client.get(self.path)
        response = self.client.get(reverse("accounts:whoami"))
        self.assertFalse(response.data["is_authenticated"])

    def test_logged_in(self):
        user = UserFactory.create()
        self.client.force_login(user)
        response = self.client.get(reverse("accounts:whoami"))
        self.assertTrue(response.data["is_authenticated"])

        self.client.get(self.path)
        response = self.client.get(reverse("accounts:whoami"))
        self.assertFalse(response.data["is_authenticated"])


class WhoAmIViewTest(APITestCase):
    def setUp(self):
        self.path = reverse("accounts:whoami")

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
