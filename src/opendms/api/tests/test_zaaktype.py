from maykin_common.vcr import VCRMixin
from requests.exceptions import Timeout
from rest_framework import status
from vng_api_common.tests import reverse
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from .api_testcase import APITestCase


class ZaakTypeTests(VCRMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.service = ServiceFactory.create(
            label="Catalogi API",
            slug="catalogi-api",
            api_root="http://localhost:8003/catalogi/api/v1/",
            api_type=APITypes.ztc,
            auth_type=AuthTypes.zgw,
            client_id="test_client_id",
            secret="test_secret_key",
        )
        cls.list_url = reverse(
            "api:zaaktypen-list", kwargs={"service_slug": cls.service.slug}
        )

    def test_list(self):
        # not found response
        response = self.client.get(
            reverse("api:zaaktypen-list", kwargs={"service_slug": "test"})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # ok response
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 7)  # from openzaak container

    def test_service_connection(self):
        service = ServiceFactory.create(
            label="Catalogi API 2",
            slug="catalogi-api-2",
            api_root="http://testserver",
            api_type=APITypes.ztc,
        )
        with self.vcr_raises(Timeout):
            response = self.client.get(
                reverse("api:zaaktypen-list", kwargs={"service_slug": service.slug})
            )

        self.assertEqual(response.data["code"], "service_unavailable")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["title"], "External service unreachable")
        self.assertEqual(
            response.data["detail"],
            "External service 'catalogi-api-2' unreachable.",
        )

    def test_detail(self):
        # not found response
        response = self.client.get(
            reverse(
                "api:zaaktypen-detail",
                kwargs={
                    "service_slug": "catalogi-api",
                    "zaaktype_uuid": "d7301c39-4952-45e8-81df-0ad2fdf6f702",  # random uuid
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # ok response
        response = self.client.get(
            reverse(
                "api:zaaktypen-detail",
                kwargs={
                    "service_slug": "catalogi-api",
                    "zaaktype_uuid": "f609b6fe-449a-46dc-a0af-de55dc5f6774",
                },
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "uuid": "f609b6fe-449a-46dc-a0af-de55dc5f6774",
                "catalogus": "http://localhost:8003/catalogi/api/v1/catalogussen/bd58635c-793e-446d-a7e0-460d7b04829d",
                "identificatie": "ZT-001",
                "omschrijving": "Test",
                "beginGeldigheid": "2024-10-31",
                "eindeGeldigheid": None,
            },
        )

    def test_read_only(self):
        detail_url = reverse(
            "api:zaaktypen-detail",
            kwargs={
                "service_slug": "catalogi-api",
                "zaaktype_uuid": "f609b6fe-449a-46dc-a0af-de55dc5f6774",
            },
        )

        # POST
        data = {}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data["code"], "method_not_allowed")
        self.assertEqual(response.data["detail"], 'Methode "POST" niet toegestaan.')

        # PATCH
        response = self.client.patch(detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data["code"], "method_not_allowed")
        self.assertEqual(response.data["detail"], 'Methode "PATCH" niet toegestaan.')

        # PUT
        response = self.client.put(detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data["code"], "method_not_allowed")
        self.assertEqual(response.data["detail"], 'Methode "PUT" niet toegestaan.')

        # DELETE
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data["code"], "method_not_allowed")
        self.assertEqual(response.data["detail"], 'Methode "DELETE" niet toegestaan.')
