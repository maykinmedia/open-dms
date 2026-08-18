from unittest.mock import Mock, patch

from django.urls import NoReverseMatch

from maykin_common.vcr import VCRMixin
from requests import HTTPError
from requests.exceptions import RequestException
from rest_framework import status
from vng_api_common.tests import reverse
from zgw_consumers.constants import APITypes

from opendms.api.tests.factories import ServiceFactory, ZGWApiGroupConfigFactory

from ..clients.documenten import CRS_HEADERS
from ..clients.zaken import get_zaken_client
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

        cls.zaaktype_uuid = "d5080f2c-f2f3-4b97-b587-0150f2dced1d"
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
        self.assertEqual(len(response.json()["results"]), 12)  # from openzaak container

    def test_list_can_expand_status(self):
        response = self.client.get(self.list_url, {"expand": "status"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 12)  # from openzaak container

        # expansion should contain fields needed for "per Zaaktype" Kanban
        self.assertTrue(
            all(
                "_expand" in zaak
                and "status" in zaak["_expand"]
                and {"datumStatusGezet", "statustype"} & set(zaak["_expand"]["status"])
                for zaak in results
            )
        )

    def test_pagination(self):
        multiple_zaken_url = reverse(
            "api:zaken-list",
            kwargs={
                "service_slug": self.ztc_service.slug,
                "zaaktypen_zaaktype_uuid": self.zaaktype_uuid,
            },
        )
        # no params, open-zaak default pageSize = 100
        response = self.client.get(multiple_zaken_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 12)  # from openzaak container

        # pageSize=5 & page=1
        response = self.client.get(multiple_zaken_url, query_params={"pageSize": 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 5)

        # pageSize=1 & page=1
        response = self.client.get(multiple_zaken_url, query_params={"pageSize": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(
            response.json(),
            {
                "count": 12,
                "results": [
                    {
                        "uuid": "2c8c15af-4fdc-4b6a-a29c-75df40df38ed",
                        "url": "http://localhost:8003/zaken/api/v1/zaken/2c8c15af-4fdc-4b6a-a29c-75df40df38ed",
                        "identificatie": "ZAAK-2026-0000000010",
                        "zaaktype": f"http://localhost:8003/catalogi/api/v1/zaaktypen/{str(self.zaaktype_uuid)}",
                        "bronorganisatie": "000000231",
                        "verantwoordelijkeOrganisatie": "000000292",
                        "registratiedatum": "2026-03-25",
                        "startdatum": "2026-01-15",
                        "omschrijving": "",
                        "toelichting": "",
                        "_expand": {},
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
                "count": 12,
                "results": [
                    {
                        "uuid": "511f30e1-7538-48c0-af85-41e76a38cd24",
                        "url": "http://localhost:8003/zaken/api/v1/zaken/511f30e1-7538-48c0-af85-41e76a38cd24",
                        "identificatie": "ZAAK-2026-0000000009",
                        "zaaktype": f"http://localhost:8003/catalogi/api/v1/zaaktypen/{str(self.zaaktype_uuid)}",
                        "bronorganisatie": "000000061",
                        "verantwoordelijkeOrganisatie": "000000309",
                        "registratiedatum": "2026-03-25",
                        "startdatum": "2026-02-14",
                        "omschrijving": "",
                        "toelichting": "",
                        "_expand": {},
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
            reverse(
                "api:zaken-list", kwargs={"zaaktypen_zaaktype_uuid": self.zaaktype_uuid}
            )

        # empty service_slug
        with self.assertRaises(NoReverseMatch):
            reverse(
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
                    "zaak_uuid": "f609b6fe-449a-46dc-a0af-de55dc5f6774",  # random uuid
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # ok response
        zaak_uuid = "da18b89e-e7ac-49b2-9f5d-d6ef327e1b1d"
        response = self.client.get(
            reverse(
                "api:zaken-detail",
                kwargs={
                    "service_slug": self.ztc_service.slug,
                    "zaaktypen_zaaktype_uuid": self.zaaktype_uuid,
                    "zaak_uuid": zaak_uuid,
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "uuid": zaak_uuid,
                "url": "http://localhost:8003/zaken/api/v1/zaken/da18b89e-e7ac-49b2-9f5d-d6ef327e1b1d",
                "identificatie": "ZAAK-2026-0000000001",
                "zaaktype": "http://localhost:8003/catalogi/api/v1/zaaktypen/d5080f2c-f2f3-4b97-b587-0150f2dced1d",
                "bronorganisatie": "000000103",
                "verantwoordelijkeOrganisatie": "000000152",
                "registratiedatum": "2026-03-25",
                "startdatum": "2026-03-03",
                "omschrijving": "",
                "toelichting": "",
                "_expand": {},
            },
        )

    def test_read_only(self):
        zaak_uuid = "da18b89e-e7ac-49b2-9f5d-d6ef327e1b1d"
        detail_url = reverse(
            "api:zaken-detail",
            kwargs={
                "service_slug": self.ztc_service.slug,
                "zaaktypen_zaaktype_uuid": self.zaaktype_uuid,
                "zaak_uuid": zaak_uuid,
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

    def test_list_without_zaaktype(self):
        url = reverse(
            "api:service-zaken-list",
            kwargs={
                "service_slug": self.ztc_service.slug,
            },
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertGreater(data["count"], 0)
        self.assertGreater(len(data["results"]), 0)

        zaaktypes = {item["zaaktype"] for item in data["results"]}

        self.assertGreater(len(zaaktypes), 1)

    def test_list_without_zaaktype_filter_omschrijving(self):
        url = reverse(
            "api:service-zaken-list",
            kwargs={
                "service_slug": self.ztc_service.slug,
            },
        )

        response = self.client.get(
            url,
            query_params={"omschrijving": "verklaring"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 2)
        self.assertEqual(len(response.json()["results"]), 2)


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

        cls.zaaktype_uuid = "d5080f2c-f2f3-4b97-b587-0150f2dced1d"
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
        self.assertEqual(len(response.json()["results"]), 12)  # from openzaak container

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
        self.assertEqual(len(response.json()["results"]), 7)
        results = [record["identificatie"] for record in response.json()["results"]]
        self.assertIn("ZAAK-2026-0000000001", results)
        self.assertIn("ZAAK-2026-0000000001", results)

    def test_omschrijving(self):
        # no params
        response = self.client.get(self.list_url, query_params={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 12)  # from openzaak container

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
        self.assertEqual(len(response.json()["results"]), 1)

        # search contains value
        response = self.client.get(
            self.list_url,
            query_params={"omschrijving": "verklaring"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)

    def test_startdatum_gte(self):
        # no params
        response = self.client.get(self.list_url, query_params={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 12)  # from openzaak container

        # search wrong value
        response = self.client.get(self.list_url, query_params={"startdatum": "random"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # search gt
        response = self.client.get(
            self.list_url,
            query_params={"startdatum__gte": "2026-01-01"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 7)

        # search gte
        response = self.client.get(
            self.list_url,
            query_params={"startdatum__gte": "2026-03-05"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 0)

        response = self.client.get(
            self.list_url,
            query_params={"startdatum__gte": "2026-02-14"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 3)

        response = self.client.get(
            self.list_url,
            query_params={"startdatum__gte": "2026-12-31"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 0)


class ServiceZaakViewSetTests(VCRMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.ztc_service = ServiceFactory.create(for_ztc_service_docker_compose=True)
        cls.zrc_service = ServiceFactory.create(for_zrc_service_docker_compose=True)

        cls.configuration = ZGWApiGroupConfigFactory.create(
            ztc_service=cls.ztc_service,
            zrc_service=cls.zrc_service,
        )

        cls.list_url = reverse(
            "api:service-zaken-list",
            kwargs={"service_slug": cls.ztc_service.slug},
        )

        cls.zaaktype_url = (
            "http://localhost:8003/catalogi/api/v1/zaaktypen/"
            "d5080f2c-f2f3-4b97-b587-0150f2dced1d"
        )

    def test_list_service_zaken(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertGreater(data["count"], 0)
        self.assertGreater(len(data["results"]), 0)

    def test_create_zaak_requires_required_fields(self):
        payload = {
            "zaaktype": self.zaaktype_url,
        }

        response = self.client.post(
            self.list_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        invalid_params = response.json()["invalidParams"]

        invalid_param_names = {param["name"] for param in invalid_params}

        self.assertIn("startdatum", invalid_param_names)
        self.assertIn("bronorganisatie", invalid_param_names)
        self.assertIn(
            "verantwoordelijkeOrganisatie",
            invalid_param_names,
        )

    def test_create_zaak(self):
        payload = {
            "zaaktype": self.zaaktype_url,
            "omschrijving": "Test zaak",
            "startdatum": "2026-05-21",
            "bronorganisatie": "000000000",
            "verantwoordelijke_organisatie": "000000000",
        }

        response = self.client.post(
            self.list_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()

        self.assertEqual(data["omschrijving"], "Test zaak")
        self.assertEqual(data["bronorganisatie"], "000000000")
        self.assertEqual(data["startdatum"], "2026-05-21")
        self.assertEqual(data["zaaktype"], self.zaaktype_url)

        self.assertIn("uuid", data)
        self.assertIn("url", data)


class ServiceZaakInformatieObjectViewSetTests(VCRMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.ztc_service = ServiceFactory.create(for_ztc_service_docker_compose=True)
        cls.zrc_service = ServiceFactory.create(for_zrc_service_docker_compose=True)

        cls.configuration = ZGWApiGroupConfigFactory.create(
            ztc_service=cls.ztc_service,
            zrc_service=cls.zrc_service,
        )

        cls.list_url = reverse(
            "api:service-zaakinformatieobjecten-list",
            kwargs={"service_slug": cls.ztc_service.slug},
        )

    def test_list_zaakinformatieobjecten(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertGreater(data["count"], 0)
        self.assertGreater(len(data["results"]), 0)

    def test_create_requires_required_fields(self):
        response = self.client.post(
            self.list_url,
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        invalid_params = response.json()["invalidParams"]
        invalid_param_names = {param["name"] for param in invalid_params}

        self.assertIn("zaak", invalid_param_names)
        self.assertIn("informatieobject", invalid_param_names)

    def test_create_zaakinformatieobject(self):
        payload = {
            "zaak": "http://localhost:8003/zaken/api/v1/zaken/840a1355-dd6d-48a4-a849-38fbf832db44",
            "informatieobject": "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/ea16fa8c-4bab-4065-a28a-f6574625205d",
        }

        response = self.client.post(
            self.list_url,
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()

        self.assertEqual(data["zaak"], payload["zaak"])
        self.assertEqual(
            data["informatieobject"],
            payload["informatieobject"],
        )

    @patch("opendms.api.viewsets.get_zaken_client")
    def test_create_forwards_remote_validation_errors(
        self,
        mock_get_zaken_client,
    ):
        response_mock = Mock()
        response_mock.status_code = 400
        response_mock.json.return_value = {
            "invalidParams": [
                {
                    "name": "nonFieldErrors",
                    "code": "unique",
                }
            ]
        }

        client = Mock()
        client.create_zaakinformatieobject.side_effect = HTTPError(
            response=response_mock
        )
        mock_get_zaken_client.return_value.__enter__.return_value = client

        response = self.client.post(
            self.list_url,
            {
                "zaak": "http://example.com/zaak",
                "informatieobject": "http://example.com/document",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["invalidParams"][0]["code"],
            "unique",
        )

    def test_detail_zaakinformatieobject(self):
        zio_uuid = "f931b3f6-f92e-4c46-b484-f68aa68acc18"

        detail_url = reverse(
            "api:service-zaakinformatieobjecten-detail",
            kwargs={
                "service_slug": self.ztc_service.slug,
                "pk": zio_uuid,
            },
        )

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["zaak"],
            "http://localhost:8003/zaken/api/v1/zaken/840a1355-dd6d-48a4-a849-38fbf832db44",
        )

    def test_detail_not_found(self):
        response = self.client.get(
            reverse(
                "api:service-zaakinformatieobjecten-detail",
                kwargs={
                    "service_slug": self.ztc_service.slug,
                    "pk": "00000000-0000-0000-0000-000000000000",
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    @patch("opendms.api.clients.zaken.ZaakClient.make_request")
    def test_get_zaakinformatieobject(self, mock_make_request):
        mock_make_request.return_value = {
            "zaak": "http://example.com/zaak",
            "informatieobject": "http://example.com/document",
        }

        with get_zaken_client(self.zrc_service) as client:
            result = client.get_zaakinformatieobject(
                "123e4567-e89b-12d3-a456-426614174000"
            )

        mock_make_request.assert_called_once_with(
            "zaakinformatieobjecten/123e4567-e89b-12d3-a456-426614174000",
            headers=CRS_HEADERS,
        )

        self.assertEqual(
            result["zaak"],
            "http://example.com/zaak",
        )


class ServiceDocumentRegistrerenViewSetTests(VCRMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.ztc_service = ServiceFactory.create(for_ztc_service_docker_compose=True)
        cls.zrc_service = ServiceFactory.create(for_zrc_service_docker_compose=True)

        cls.drc_service = ServiceFactory.create(for_drc_service_docker_compose=True)

        cls.configuration = ZGWApiGroupConfigFactory.create(
            ztc_service=cls.ztc_service,
            zrc_service=cls.zrc_service,
            drc_service=cls.drc_service,
        )

        cls.list_url = reverse(
            "api:service-document-registreren-list",
            kwargs={"service_slug": cls.ztc_service.slug},
        )

    def test_document_registreren(self):
        url = reverse(
            "api:service-document-registreren-list",
            kwargs={"service_slug": self.ztc_service.slug},
        )

        payload = {
            "enkelvoudiginformatieobject": {
                "bronorganisatie": "000000280",
                "creatiedatum": "2026-06-10",
                "titel": "Test document via Open DMS",
                "auteur": "Alfvin Rudy",
                "taal": "nld",
                "informatieobjecttype": (
                    "http://localhost:8003/catalogi/api/v1/"
                    "informatieobjecttypen/7f420939-2866-4582-8b94-f21d3891daab"
                ),
            },
            "zaakinformatieobject": {
                "zaak": (
                    "http://localhost:8003/zaken/api/v1/zaken/"
                    "14f68708-d50d-42c8-abfc-9a186485999a"
                )
            },
        }

        response = self.client.post(
            url,
            data=payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()

        self.assertEqual(
            data["enkelvoudiginformatieobject"]["titel"],
            "Test document via Open DMS",
        )

        self.assertEqual(
            data["zaakinformatieobject"]["zaak"],
            payload["zaakinformatieobject"]["zaak"],
        )

    def test_document_registreren_requires_required_fields(self):
        response = self.client.post(
            self.list_url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        invalid_params = response.json()["invalidParams"]
        invalid_param_names = {p["name"] for p in invalid_params}

        self.assertIn(
            "enkelvoudiginformatieobject",
            invalid_param_names,
        )
        self.assertIn(
            "zaakinformatieobject",
            invalid_param_names,
        )

    @patch("opendms.api.viewsets.get_documenten_client")
    def test_document_registreren_forwards_remote_validation_errors(
        self,
        mock_get_documenten_client,
    ):
        response_mock = Mock()
        response_mock.status_code = 400
        response_mock.json.return_value = {
            "invalidParams": [
                {
                    "name": "titel",
                    "code": "required",
                }
            ]
        }

        client = Mock()
        client.document_registreren.side_effect = HTTPError(response=response_mock)

        mock_get_documenten_client.return_value.__enter__.return_value = client

        response = self.client.post(
            self.list_url,
            {
                "enkelvoudiginformatieobject": {},
                "zaakinformatieobject": {},
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
