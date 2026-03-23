from maykin_common.vcr import VCRMixin
from rest_framework import status
from vng_api_common.tests import reverse

from opendms.api.tests.factories import ServiceFactory, ZGWApiGroupConfigFactory
from opendms.search_index.tests.base import ElasticSearchAPITestCase

from .api_testcase import APITestCase


class DocumentTests(VCRMixin, ElasticSearchAPITestCase, APITestCase):
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

        cls.zaaktype_uuid = "1f41885e-23fc-4462-bbc8-80be4ae484dc"
        cls.zaak_uuid = "d3efda94-12a9-4969-80e2-bb9b20e3039e"
        cls.list_url = reverse(
            "api:documents-list",
            kwargs={
                "service_slug": cls.ztc_service.slug,
                "zaaktypen_zaaktype_uuid": cls.zaaktype_uuid,
                "zaken_zaak_uuid": cls.zaak_uuid,
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
                        "uuid": "51719a8e-a28f-4e6e-89a9-593c1e98f57c",
                        "url": "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/51719a8e-a28f-4e6e-89a9-593c1e98f57c",
                        "identificatie": "DOCUMENT-2026-0000000001",
                        "bronorganisatie": "123456782",
                        "creatiedatum": "2026-03-20",
                        "titel": "123456782",
                        "auteur": "123456782",
                        "taal": "123",
                        "beginRegistratie": "2026-03-20T10:14:19.275987Z",
                        "informatieobjecttype": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/7755ab0f-9e37-4834-8bbf-158f9f2da38e",
                        "vertrouwelijkheidaanduiding": "",
                        "status": "",
                        "formaat": "",
                        "bestandsnaam": "",
                        "link": "",
                        "beschrijving": "",
                        "verschijningsvorm": "",
                        "bestandsomvang": 123456782,
                        "inhoud": "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/51719a8e-a28f-4e6e-89a9-593c1e98f57c/download?versie=1",
                    }
                ],
            },
        )

    def test_detail(self):
        # not found response
        response = self.client.get(
            reverse(
                "api:documents-detail",
                kwargs={
                    "service_slug": self.ztc_service.slug,
                    "zaaktypen_zaaktype_uuid": self.zaaktype_uuid,
                    "zaken_zaak_uuid": self.zaak_uuid,
                    "document_uuid": "f609b6fe-449a-46dc-a0af-de55dc5f6774",  # random uuid
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # ok response
        document_uuid = "51719a8e-a28f-4e6e-89a9-593c1e98f57c"
        response = self.client.get(
            reverse(
                "api:documents-detail",
                kwargs={
                    "service_slug": self.ztc_service.slug,
                    "zaaktypen_zaaktype_uuid": self.zaaktype_uuid,
                    "zaken_zaak_uuid": self.zaak_uuid,
                    "document_uuid": document_uuid,
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "uuid": "51719a8e-a28f-4e6e-89a9-593c1e98f57c",
                "url": "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/51719a8e-a28f-4e6e-89a9-593c1e98f57c",
                "identificatie": "DOCUMENT-2026-0000000001",
                "bronorganisatie": "123456782",
                "creatiedatum": "2026-03-20",
                "titel": "123456782",
                "auteur": "123456782",
                "taal": "123",
                "beginRegistratie": "2026-03-20T10:14:19.275987Z",
                "informatieobjecttype": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/7755ab0f-9e37-4834-8bbf-158f9f2da38e",
                "vertrouwelijkheidaanduiding": "",
                "status": "",
                "formaat": "",
                "bestandsnaam": "",
                "link": "",
                "beschrijving": "",
                "verschijningsvorm": "",
                "bestandsomvang": 123456782,
                "inhoud": "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/51719a8e-a28f-4e6e-89a9-593c1e98f57c/download?versie=1",
            },
        )

    def test_read_only(self):
        document_uuid = "51719a8e-a28f-4e6e-89a9-593c1e98f57c"
        detail_url = reverse(
            "api:documents-detail",
            kwargs={
                "service_slug": self.ztc_service.slug,
                "zaaktypen_zaaktype_uuid": self.zaaktype_uuid,
                "zaken_zaak_uuid": self.zaak_uuid,
                "document_uuid": document_uuid,
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
