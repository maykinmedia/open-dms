from django.urls import NoReverseMatch

from maykin_common.vcr import VCRMixin
from requests.exceptions import RequestException
from rest_framework import status
from vng_api_common.tests import reverse
from zgw_consumers.constants import APITypes

from opendms.api.tests.factories import ServiceFactory, ZGWApiGroupConfigFactory

from .api_testcase import APITestCase


class ZaakTests(VCRMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.ztc_service = ServiceFactory.create(for_ztc_service_docker_compose=True)
        cls.zrc_service = ServiceFactory.create(for_zrc_service_docker_compose=True)
        cls.configuration = ZGWApiGroupConfigFactory.create(
            ztc_service=cls.ztc_service,
            zrc_service=cls.zrc_service,
        )

        cls.zaaktype_uuid = "1f41885e-23fc-4462-bbc8-80be4ae484dc"
        cls.list_url = reverse(
            "api:zaken-list",
            kwargs={
                "service_slug": cls.ztc_service.slug,
                "zaaktypen_zaaktype_uuid": cls.zaaktype_uuid,
            },
        )

    def test_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "count": 1,
                "results": [
                    {
                        "uuid": "5ff8b6a0-0a9c-4680-8974-8cfadfbdbadd",
                        "url": "http://localhost:8003/zaken/api/v1/zaken/5ff8b6a0-0a9c-4680-8974-8cfadfbdbadd",
                        "identificatie": "ZAAK-2026-0000000003",
                        "zaaktype": f"http://localhost:8003/catalogi/api/v1/zaaktypen/{self.zaaktype_uuid}",
                        "bronorganisatie": "123456782",
                        "verantwoordelijkeOrganisatie": "123456782",
                        "registratiedatum": "2026-03-11",
                        "startdatum": "2026-03-11",
                        "omschrijving": "verklaring van vernietiging",
                        "toelichting": 'Verklaring van vernietiging voor vernietigingslijst: "test".',
                    }
                ],
            },
        )

    def test_pagination(self):
        zaaktype_uuid = "f609b6fe-449a-46dc-a0af-de55dc5f6774"
        multiple_zaken_url = reverse(
            "api:zaken-list",
            kwargs={
                "service_slug": self.ztc_service.slug,
                "zaaktypen_zaaktype_uuid": zaaktype_uuid,
            },
        )
        # no params, open-zaak default pageSize = 100
        response = self.client.get(multiple_zaken_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 2)  # from openzaak container

        # pageSize=1 & page=1
        response = self.client.get(multiple_zaken_url, query_params={"pageSize": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(
            response.json(),
            {
                "count": 2,
                "results": [
                    {
                        "uuid": "d67efb65-9119-42b5-ba0b-8a0fa731f696",
                        "url": "http://localhost:8003/zaken/api/v1/zaken/d67efb65-9119-42b5-ba0b-8a0fa731f696",
                        "identificatie": "ZAAK-2026-0000000002",
                        "zaaktype": "http://localhost:8003/catalogi/api/v1/zaaktypen/f609b6fe-449a-46dc-a0af-de55dc5f6774",
                        "bronorganisatie": "123456782",
                        "verantwoordelijkeOrganisatie": "123456782",
                        "registratiedatum": "2026-03-11",
                        "startdatum": "2026-03-11",
                        "omschrijving": "verklaring van vernietiging",
                        "toelichting": 'Verklaring van vernietiging voor vernietigingslijst: "TEST".',
                    }
                ],
            },
        )

        # pageSize=1 & page=2
        response = self.client.get(
            multiple_zaken_url, query_params={"pageSize": 1, "page": 2}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(
            response.json(),
            {
                "count": 2,
                "results": [
                    {
                        "uuid": "376b1195-6d1e-48e3-a957-649d084a2627",
                        "url": "http://localhost:8003/zaken/api/v1/zaken/376b1195-6d1e-48e3-a957-649d084a2627",
                        "identificatie": "ZAAK-2026-0000000001",
                        "zaaktype": "http://localhost:8003/catalogi/api/v1/zaaktypen/f609b6fe-449a-46dc-a0af-de55dc5f6774",
                        "bronorganisatie": "123456782",
                        "verantwoordelijkeOrganisatie": "123456782",
                        "registratiedatum": "2026-03-05",
                        "startdatum": "2026-03-05",
                        "omschrijving": "verklaring van vernietiging",
                        "toelichting": "Verklaring van vernietiging voor vernietigingslijst",
                    }
                ],
            },
        )

        # pageSize=100 & page=20 not exists page
        response = self.client.get(
            multiple_zaken_url, query_params={"pageSize": 100, "page": 20}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_service_connection(self):
        zrc_service = ServiceFactory.create(
            label="Zaken API 2",
            slug="zaken-api-2",
            api_root="http://testserver",
            api_type=APITypes.zrc,
        )
        self.configuration.zrc_service = zrc_service
        self.configuration.save()

        url = reverse(
            "api:zaken-list",
            kwargs={
                "service_slug": self.ztc_service.slug,
                "zaaktypen_zaaktype_uuid": self.zaaktype_uuid,
            },
        )
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
        url = reverse(
            "api:zaken-list",
            kwargs={
                "service_slug": "test",
                "zaaktypen_zaaktype_uuid": self.zaaktype_uuid,
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.data["code"], "not_found")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["title"], "Niet gevonden.")
        self.assertEqual(response.data["detail"], "Niet gevonden.")

        # missing service_slug
        with self.assertRaises(NoReverseMatch):
            url = reverse(
                "api:zaken-list", kwargs={"zaaktypen_zaaktype_uuid": self.zaaktype_uuid}
            )

        # empty service_slug
        with self.assertRaises(NoReverseMatch):
            url = reverse(
                "api:zaken-list",
                kwargs={
                    "service_slug": "",
                    "zaaktypen_zaaktype_uuid": self.zaaktype_uuid,
                },
            )

    def test_service_configuration(self):
        service = ServiceFactory.create(
            label="Catalogi API 2",
            slug="catalogi-api-2",
            api_root="http://testserver",
            api_type=APITypes.ztc,
        )
        response = self.client.get(
            reverse(
                "api:zaken-list",
                kwargs={
                    "service_slug": service.slug,
                    "zaaktypen_zaaktype_uuid": self.zaaktype_uuid,
                },
            )
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
                "api:zaken-detail",
                kwargs={
                    "service_slug": self.ztc_service.slug,
                    "zaaktypen_zaaktype_uuid": self.zaaktype_uuid,
                    "zaken_uuid": "f609b6fe-449a-46dc-a0af-de55dc5f6774",  # random uuid
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # ok response
        zaak_uuid = "5ff8b6a0-0a9c-4680-8974-8cfadfbdbadd"
        response = self.client.get(
            reverse(
                "api:zaken-detail",
                kwargs={
                    "service_slug": self.ztc_service.slug,
                    "zaaktypen_zaaktype_uuid": self.zaaktype_uuid,
                    "zaken_uuid": zaak_uuid,
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "uuid": "5ff8b6a0-0a9c-4680-8974-8cfadfbdbadd",
                "url": f"http://localhost:8003/zaken/api/v1/zaken/{zaak_uuid}",
                "identificatie": "ZAAK-2026-0000000003",
                "zaaktype": f"http://localhost:8003/catalogi/api/v1/zaaktypen/{self.zaaktype_uuid}",
                "bronorganisatie": "123456782",
                "verantwoordelijkeOrganisatie": "123456782",
                "registratiedatum": "2026-03-11",
                "startdatum": "2026-03-11",
                "omschrijving": "verklaring van vernietiging",
                "toelichting": 'Verklaring van vernietiging voor vernietigingslijst: "test".',
            },
        )

    def test_read_only(self):
        zaak_uuid = "5ff8b6a0-0a9c-4680-8974-8cfadfbdbadd"
        detail_url = reverse(
            "api:zaken-detail",
            kwargs={
                "service_slug": self.ztc_service.slug,
                "zaaktypen_zaaktype_uuid": self.zaaktype_uuid,
                "zaken_uuid": zaak_uuid,
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


class ZaakFiltersTests(VCRMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.ztc_service = ServiceFactory.create(for_ztc_service_docker_compose=True)
        cls.zrc_service = ServiceFactory.create(for_zrc_service_docker_compose=True)
        cls.configuration = ZGWApiGroupConfigFactory.create(
            ztc_service=cls.ztc_service,
            zrc_service=cls.zrc_service,
        )

        cls.zaaktype_uuid = "f609b6fe-449a-46dc-a0af-de55dc5f6774"
        cls.list_url = reverse(
            "api:zaken-list",
            kwargs={
                "service_slug": cls.ztc_service.slug,
                "zaaktypen_zaaktype_uuid": cls.zaaktype_uuid,
            },
        )

    def test_identificatie_icontains(self):
        # no params
        response = self.client.get(self.list_url, query_params={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 2)  # from openzaak container

        # search random value
        response = self.client.get(
            self.list_url, query_params={"identificatie__icontains": "random"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 0)

        # search exact value
        response = self.client.get(
            self.list_url,
            query_params={"identificatie__icontains": "ZAAK-2026-0000000001"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(
            response.json()["results"][0]["identificatie"], "ZAAK-2026-0000000001"
        )

        # search multiple result
        response = self.client.get(
            self.list_url,
            query_params={"identificatie__icontains": "ZAAK-2026"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 2)
        results = [record["identificatie"] for record in response.json()["results"]]
        self.assertIn("ZAAK-2026-0000000001", results)
        self.assertIn("ZAAK-2026-0000000001", results)

    def test_omschrijving(self):
        # no params
        response = self.client.get(self.list_url, query_params={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 2)  # from openzaak container

        # search random value
        response = self.client.get(
            self.list_url, query_params={"omschrijving": "random"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 0)

        # search exact value
        response = self.client.get(
            self.list_url,
            query_params={"omschrijving": "verklaring van vernietiging"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 2)

        # search contains value
        response = self.client.get(
            self.list_url,
            query_params={"omschrijving": "verklaring"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 2)

    def test_startdatum_gte(self):
        # no params
        response = self.client.get(self.list_url, query_params={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 2)  # from openzaak container

        # search wrong value
        response = self.client.get(self.list_url, query_params={"startdatum": "random"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # search gt
        response = self.client.get(
            self.list_url,
            query_params={"startdatum__gte": "2026-01-01"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 2)

        # search gte
        response = self.client.get(
            self.list_url,
            query_params={"startdatum__gte": "2026-03-05"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 2)

        response = self.client.get(
            self.list_url,
            query_params={"startdatum__gte": "2026-03-11"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)

        response = self.client.get(
            self.list_url,
            query_params={"startdatum__gte": "2026-12-31"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 0)
