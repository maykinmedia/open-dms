from maykin_common.vcr import VCRMixin
from requests.exceptions import RequestException
from rest_framework import status
from vng_api_common.tests import reverse
from zgw_consumers.constants import APITypes

from opendms.api.tests.factories import ServiceFactory, ZGWApiGroupConfigFactory

from .api_testcase import APITestCase


class NestedStatusTypeListTests(VCRMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.ztc_service = ServiceFactory.create(for_ztc_service_docker_compose=True)
        cls.configuration = ZGWApiGroupConfigFactory.create(ztc_service=cls.ztc_service)

        cls.list_url = reverse(
            "api:zaaktype-statustypen-list",
            kwargs={
                "service_slug": cls.ztc_service.slug,
                "zaaktypen_zaaktype_uuid": "d5080f2c-f2f3-4b97-b587-0150f2dced1d",
            },
        )

    def test_list(self):
        # not found response
        response = self.client.get(
            reverse(
                "api:zaaktype-statustypen-list",
                kwargs={
                    "service_slug": "test",
                    "zaaktypen_zaaktype_uuid": "d5080f2c-f2f3-4b97-b587-0150f2dced1d",
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # ok response
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.json())
        self.assertIn("count", response.json())

    def test_detail(self):
        response = self.client.get(
            reverse(
                "api:zaaktype-statustypen-detail",
                kwargs={
                    "service_slug": "catalogi-api",
                    "zaaktypen_zaaktype_uuid": "d5080f2c-f2f3-4b97-b587-0150f2dced1d",
                    "statustype_uuid": "ded960a6-4309-447d-bd2b-fa7b01dd8b81",
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("uuid", data)
        self.assertIn("url", data)
        self.assertIn("omschrijving", data)
        self.assertIn("volgnummer", data)
        self.assertIn("isEindstatus", data)

    def test_pagination(self):
        # no params, open-zaak default pageSize = 100
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertLessEqual(len(payload["results"]), payload["count"])

    def test_pagination_page_size(self):
        # pageSize=2
        response = self.client.get(self.list_url, query_params={"pageSize": 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        payload = response.json()
        self.assertLessEqual(len(payload["results"]), payload["count"])
        self.assertEqual(len(payload["results"]), 2)

    def test_service_connection(self):
        service = ServiceFactory.create(
            label="Catalogi API 2",
            slug="catalogi-api-2",
            api_root="http://testserver",
            api_type=APITypes.ztc,
        )

        self.configuration.ztc_service = service
        self.configuration.save()

        url = reverse(
            "api:zaaktype-statustypen-list",
            kwargs={
                "service_slug": service.slug,
                "zaaktypen_zaaktype_uuid": "d5080f2c-f2f3-4b97-b587-0150f2dced1d",
            },
        )

        with self.vcr_raises(RequestException):
            response = self.client.get(url)
        self.assertEqual(response.data["code"], "service_unavailable")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

        with self.vcr_raises(TimeoutError):
            response = self.client.get(url)
        self.assertEqual(response.data["code"], "service_unavailable")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_service_configuration(self):
        service = ServiceFactory.create(
            label="Catalogi API 2",
            slug="catalogi-api-2",
            api_root="http://testserver",
            api_type=APITypes.ztc,
        )

        response = self.client.get(
            reverse(
                "api:zaaktype-statustypen-list",
                kwargs={
                    "service_slug": service.slug,
                    "zaaktypen_zaaktype_uuid": "d5080f2c-f2f3-4b97-b587-0150f2dced1d",
                },
            )
        )
        self.assertEqual(response.data["code"], "zgw_group_missing")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_read_only(self):
        # POST
        data = {}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class StatusTypeDetailTests(VCRMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.ztc_service = ServiceFactory.create(for_ztc_service_docker_compose=True)
        cls.configuration = ZGWApiGroupConfigFactory.create(ztc_service=cls.ztc_service)

    def test_detail_not_found(self):
        response = self.client.get(
            reverse(
                "api:statustypen-detail",
                kwargs={
                    "service_slug": "catalogi-api",
                    "statustype_uuid": "d7301c39-4952-45e8-81df-0ad2fdf6f702",
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail(self):
        response = self.client.get(
            reverse(
                "api:statustypen-detail",
                kwargs={
                    "service_slug": "catalogi-api",
                    "statustype_uuid": "ded960a6-4309-447d-bd2b-fa7b01dd8b81",
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("uuid", data)
        self.assertIn("url", data)
        self.assertIn("omschrijving", data)
        self.assertIn("volgnummer", data)
        self.assertIn("isEindstatus", data)

    def test_read_only(self):
        detail_url = reverse(
            "api:statustypen-detail",
            kwargs={
                "service_slug": "catalogi-api",
                "statustype_uuid": "ded960a6-4309-447d-bd2b-fa7b01dd8b81",
            },
        )

        # POST
        data = {}
        response = self.client.post(detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # PATCH
        response = self.client.patch(detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # PUT
        response = self.client.put(detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # DELETE
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_service_connection(self):
        service = ServiceFactory.create(
            label="Catalogi API 2",
            slug="catalogi-api-2",
            api_root="http://testserver",
            api_type=APITypes.ztc,
        )

        self.configuration.ztc_service = service
        self.configuration.save()

        url = reverse(
            "api:statustypen-detail",
            kwargs={
                "service_slug": service.slug,
                "statustype_uuid": "ded960a6-4309-447d-bd2b-fa7b01dd8b81",
            },
        )

        with self.vcr_raises(RequestException):
            response = self.client.get(url)
        self.assertEqual(response.data["code"], "service_unavailable")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_service_configuration(self):
        service = ServiceFactory.create(
            label="Catalogi API 2",
            slug="catalogi-api-2",
            api_root="http://testserver",
            api_type=APITypes.ztc,
        )

        response = self.client.get(
            reverse(
                "api:statustypen-detail",
                kwargs={
                    "service_slug": service.slug,
                    "statustype_uuid": "ded960a6-4309-447d-bd2b-fa7b01dd8b81",
                },
            )
        )
        self.assertEqual(response.data["code"], "zgw_group_missing")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
