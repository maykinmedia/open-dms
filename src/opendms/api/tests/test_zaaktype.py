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
        self.assertEqual(len(response.json()["results"]), 2)  # from openzaak container

    def test_pagination(self):
        # no params, open-zaak default pageSize = 100
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 2)  # from openzaak container

        # pageSize=2
        response = self.client.get(self.list_url, query_params={"pageSize": 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 2)

        # pageSize=2 & page=3
        response = self.client.get(
            self.list_url, query_params={"pageSize": 1, "page": 2}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)

        # pageSize=100 & page=20 not exists page
        response = self.client.get(
            self.list_url, query_params={"pageSize": 100, "page": 20}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

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
                    "zaaktype_uuid": "d5080f2c-f2f3-4b97-b587-0150f2dced1d",
                },
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "uuid": "d5080f2c-f2f3-4b97-b587-0150f2dced1d",
                "url": "http://localhost:8003/catalogi/api/v1/zaaktypen/d5080f2c-f2f3-4b97-b587-0150f2dced1d",
                "catalogus": "http://localhost:8003/catalogi/api/v1/catalogussen/15f9e22e-5bec-4d86-9b04-1e011b0a568e",
                "identificatie": "ZAAKTYPE-2026-0000000001",
                "omschrijving": "Aanvraag parkeervergunning",
                "beginGeldigheid": "2024-01-01",
                "eindeGeldigheid": None,
            },
        )

    def test_read_only(self):
        detail_url = reverse(
            "api:zaaktypen-detail",
            kwargs={
                "service_slug": "catalogi-api",
                "zaaktype_uuid": "d5080f2c-f2f3-4b97-b587-0150f2dced1d",
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
        self.assertEqual(len(response.json()["results"]), 2)  # from openzaak container

        # search random value
        response = self.client.get(self.list_url, query_params={"search": "random"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 0)

        # search exact value
        response = self.client.get(
            self.list_url, query_params={"search": "ZAAKTYPE-2026-0000000002"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(
            response.json(),
            {
                "count": 1,
                "results": [
                    {
                        "uuid": "dd8f86d3-33c5-40cd-9eb1-b45e2db64f03",
                        "url": "http://localhost:8003/catalogi/api/v1/zaaktypen/dd8f86d3-33c5-40cd-9eb1-b45e2db64f03",
                        "catalogus": "http://localhost:8003/catalogi/api/v1/catalogussen/15f9e22e-5bec-4d86-9b04-1e011b0a568e",
                        "identificatie": "ZAAKTYPE-2026-0000000002",
                        "omschrijving": "Aanvraag afvalpas",
                        "beginGeldigheid": "2024-01-01",
                        "eindeGeldigheid": None,
                    }
                ],
            },
        )

        # search multiple result
        response = self.client.get(
            self.list_url,
            query_params={"search": "ZAAKTYPE-2026"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 2)

        ids = [record["identificatie"] for record in response.json()["results"]]
        self.assertIn("ZAAKTYPE-2026-0000000001", ids)
        self.assertIn("ZAAKTYPE-2026-0000000002", ids)

    def test_not_valid_search_param(self):
        response = self.client.get(self.list_url, query_params={"test": "random"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["invalidParams"][0]["code"], "bad-request")
        self.assertEqual(
            response.json()["invalidParams"][0]["reason"],
            "Invalid or unsupported query parameters.",
        )

    def test_search_param_with_paginations(self):
        response = self.client.get(
            self.list_url, query_params={"search": "ZAAKTYPE-2026"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 2)

        response = self.client.get(
            self.list_url,
            query_params={"search": "ZAAKTYPE-2026", "pageSize": 1},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(
            response.json(),
            {
                "count": 2,
                "results": [
                    {
                        "uuid": "dd8f86d3-33c5-40cd-9eb1-b45e2db64f03",
                        "url": "http://localhost:8003/catalogi/api/v1/zaaktypen/dd8f86d3-33c5-40cd-9eb1-b45e2db64f03",
                        "catalogus": "http://localhost:8003/catalogi/api/v1/catalogussen/15f9e22e-5bec-4d86-9b04-1e011b0a568e",
                        "identificatie": "ZAAKTYPE-2026-0000000002",
                        "omschrijving": "Aanvraag afvalpas",
                        "beginGeldigheid": "2024-01-01",
                        "eindeGeldigheid": None,
                    }
                ],
            },
        )

        response = self.client.get(
            self.list_url,
            query_params={"search": "ZAAKTYPE-2026", "pageSize": 1, "page": 2},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(
            response.json(),
            {
                "count": 2,
                "results": [
                    {
                        "uuid": "d5080f2c-f2f3-4b97-b587-0150f2dced1d",
                        "url": "http://localhost:8003/catalogi/api/v1/zaaktypen/d5080f2c-f2f3-4b97-b587-0150f2dced1d",
                        "catalogus": "http://localhost:8003/catalogi/api/v1/catalogussen/15f9e22e-5bec-4d86-9b04-1e011b0a568e",
                        "identificatie": "ZAAKTYPE-2026-0000000001",
                        "omschrijving": "Aanvraag parkeervergunning",
                        "beginGeldigheid": "2024-01-01",
                        "eindeGeldigheid": None,
                    }
                ],
            },
        )
