from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIRequestFactory

from opendms.accounts.api.views import WhoAmIView
from opendms.accounts.tests.factories import UserFactory

User = get_user_model()


class WhoAmIViewTest(TestCase):
    def test_whoami_anonymous_user(self):
        request = APIRequestFactory().get("/")
        view = WhoAmIView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_authenticated"])
        self.assertIsNone(response.data["user"])

    def test_whoami_authenticated_user(self):
        request = APIRequestFactory().get("/")
        request.user = UserFactory.build()
        view = WhoAmIView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_authenticated"])
        self.assertEqual(response.data["user"]["pk"], request.user.pk)
