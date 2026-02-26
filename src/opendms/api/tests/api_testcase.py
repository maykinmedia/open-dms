from rest_framework.test import APITestCase as APITestCaseDRF

from opendms.accounts.tests.factories import UserFactory


class APITestCase(APITestCaseDRF):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.client.force_login(self.user)
