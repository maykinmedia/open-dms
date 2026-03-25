from maykin_common.vcr import VCRMixin
from rest_framework import status
from vng_api_common.tests import reverse

from .base import ElasticSearchAPITestCase
from .factories import IndexDocumentFactory


class SearchApiAuthenticationTest(VCRMixin, ElasticSearchAPITestCase):
    url = reverse("api:search")

    def test_permissions(self):
        # logout
        self.client.logout()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # login
        doc = IndexDocumentFactory.build(uuid="525747fd-7e58-4005-8efa-59bcf4403385")
        self.index_document(doc)

        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
