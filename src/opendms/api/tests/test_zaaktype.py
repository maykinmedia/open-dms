from django.urls import NoReverseMatch

from maykin_common.vcr import VCRMixin
from requests.exceptions import RequestException
from rest_framework import status
from vng_api_common.tests import reverse
from zgw_consumers.constants import APITypes

from opendms.api.tests.factories import ServiceFactory, ZGWApiGroupConfigFactory

from .api_testcase import APITestCase


class ZaakTypeTests(VCRMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.ztc_service = ServiceFactory.create(for_ztc_service_docker_compose=True)
        cls.configuration = ZGWApiGroupConfigFactory.create(ztc_service=cls.ztc_service)

        cls.list_url = reverse(
            "api:zaaktypen-list", kwargs={"service_slug": cls.ztc_service.slug}
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

        self.configuration.ztc_service = service
        self.configuration.save()

        url = reverse("api:zaaktypen-list", kwargs={"service_slug": service.slug})

        with self.vcr_raises(RequestException):
            response = self.client.get(url)
        self.assertEqual(response.data["code"], "service_unavailable")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["title"], "External service unreachable")
        self.assertEqual(response.data["detail"], "External service error")

        with self.vcr_raises(TimeoutError):
            response = self.client.get(url)
        self.assertEqual(response.data["code"], "service_unavailable")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["title"], "External service unreachable")
        self.assertEqual(response.data["detail"], "External service timeout")

        # wrong service_slug
        url = reverse("api:zaaktypen-list", kwargs={"service_slug": "test"})
        response = self.client.get(url)
        self.assertEqual(response.data["code"], "not_found")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["title"], "Niet gevonden.")
        self.assertEqual(response.data["detail"], "Niet gevonden.")

        # missing service_slug
        with self.assertRaises(NoReverseMatch):
            url = reverse("api:zaken-list", kwargs={})

        # empty service_slug
        with self.assertRaises(NoReverseMatch):
            url = reverse("api:zaken-list", kwargs={"service_slug": ""})

    def test_service_configuration(self):
        service = ServiceFactory.create(
            label="Catalogi API 2",
            slug="catalogi-api-2",
            api_root="http://testserver",
            api_type=APITypes.ztc,
        )

        response = self.client.get(
            reverse("api:zaaktypen-list", kwargs={"service_slug": service.slug})
        )
        self.assertEqual(response.data["code"], "zgw_group_missing")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(
            response.data["title"],
            "No ZGW Configuration Group found for the given ztc service",
        )
        self.assertEqual(
            response.data["detail"],
            "No configuration group was found containing this ZTC service: 'catalogi-api-2'",
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
                "url": "http://localhost:8003/catalogi/api/v1/zaaktypen/f609b6fe-449a-46dc-a0af-de55dc5f6774",
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


class ZaakTypeFiltersTests(VCRMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.service = ServiceFactory.create(for_ztc_service_docker_compose=True)
        cls.configuration = ZGWApiGroupConfigFactory.create(ztc_service=cls.service)
        cls.list_url = reverse(
            "api:zaaktypen-list", kwargs={"service_slug": cls.service.slug}
        )

    def test_search(self):
        # no params
        response = self.client.get(self.list_url, query_params={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 7)  # from openzaak container

        # search random value
        response = self.client.get(self.list_url, query_params={"search": "random"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 0)

        # search exact value
        response = self.client.get(
            self.list_url, query_params={"search": "ZAAKTYPE-2020-0000000002"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(
            response.json(),
            {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "uuid": "a516793a-cb5f-446d-bfa3-56077c1897be",
                        "url": "http://localhost:8003/catalogi/api/v1/zaaktypen/a516793a-cb5f-446d-bfa3-56077c1897be",
                        "catalogus": "http://localhost:8003/catalogi/api/v1/catalogussen/e035387e-6374-4eb9-b3d1-416294402bae",
                        "identificatie": "ZAAKTYPE-2020-0000000002",
                        "omschrijving": "Case type for children component",
                        "beginGeldigheid": "2020-06-20",
                        "eindeGeldigheid": None,
                    }
                ],
            },
        )

        # search multiple result
        response = self.client.get(
            self.list_url, query_params={"search": "ZAAKTYPE-2020"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 2)

        ids = [record["identificatie"] for record in response.json()["results"]]
        self.assertIn("ZAAKTYPE-2020-0000000001", ids)
        self.assertIn("ZAAKTYPE-2020-0000000002", ids)

        uuids = [record["uuid"] for record in response.json()["results"]]
        self.assertIn("a516793a-cb5f-446d-bfa3-56077c1897be", uuids)
        self.assertIn("77543c85-e5cd-4b3e-b7a5-27165e1334b1", uuids)

    def test_not_valid_search_param(self):
        response = self.client.get(self.list_url, query_params={"test": "random"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["invalidParams"][0]["code"], "unknown-parameters"
        )
        self.assertEqual(
            response.json()["invalidParams"][0]["reason"],
            "Unexpected parameters: test. Only 'search' is allowed.",
        )
