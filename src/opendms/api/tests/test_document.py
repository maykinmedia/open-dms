from maykin_common.vcr import VCRMixin
from rest_framework import status
from vng_api_common.tests import reverse

from opendms.api.tests.factories import ServiceFactory, ZGWApiGroupConfigFactory

from .api_testcase import APITestCase


class DocumentTests(VCRMixin, APITestCase):
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

        cls.zaaktype_uuid = "d5080f2c-f2f3-4b97-b587-0150f2dced1d"
        cls.zaak_uuid = "da18b89e-e7ac-49b2-9f5d-d6ef327e1b1d"
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
                        "uuid": "ea16fa8c-4bab-4065-a28a-f6574625205d",
                        "url": "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/ea16fa8c-4bab-4065-a28a-f6574625205d",
                        "identificatie": "DOCUMENT-2026-0000000001",
                        "bronorganisatie": "000000115",
                        "creatiedatum": "2026-01-15",
                        "titel": "aanvraag formulier",
                        "auteur": "Niek van den Berg",
                        "taal": "nld",
                        "beginRegistratie": "2026-03-25T13:51:49.784000Z",
                        "informatieobjecttype": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/7f420939-2866-4582-8b94-f21d3891daab",
                        "vertrouwelijkheidaanduiding": "confidentieel",
                        "status": "",
                        "formaat": "",
                        "bestandsnaam": "",
                        "link": "",
                        "beschrijving": "",
                        "verschijningsvorm": "",
                        "bestandsomvang": None,
                        "inhoud": "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/ea16fa8c-4bab-4065-a28a-f6574625205d/download?versie=1",
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
        document_uuid = "ea16fa8c-4bab-4065-a28a-f6574625205d"
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
                "uuid": document_uuid,
                "url": "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/ea16fa8c-4bab-4065-a28a-f6574625205d",
                "identificatie": "DOCUMENT-2026-0000000001",
                "bronorganisatie": "000000115",
                "creatiedatum": "2026-01-15",
                "titel": "aanvraag formulier",
                "auteur": "Niek van den Berg",
                "taal": "nld",
                "beginRegistratie": "2026-03-25T13:51:49.784000Z",
                "informatieobjecttype": "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/7f420939-2866-4582-8b94-f21d3891daab",
                "vertrouwelijkheidaanduiding": "confidentieel",
                "status": "",
                "formaat": "",
                "bestandsnaam": "",
                "link": "",
                "beschrijving": "",
                "verschijningsvorm": "",
                "bestandsomvang": None,
                "inhoud": "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/ea16fa8c-4bab-4065-a28a-f6574625205d/download?versie=1",
            },
        )

    # TODO add new tests for checking the versions
    def test_download(self):
        document_uuid = "ea16fa8c-4bab-4065-a28a-f6574625205d"
        response = self.client.get(
            reverse(
                "api:documents-download",
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
            b"".join(chunk for chunk in response.streaming_content),
            b"Test 1 -> OpenDMS\n",
        )

        # no document
        document_uuid = "819c31fc-81e0-4d96-990f-6221cbe987c6"
        response = self.client.get(
            reverse(
                "api:documents-download",
                kwargs={
                    "service_slug": self.ztc_service.slug,
                    "zaaktypen_zaaktype_uuid": self.zaaktype_uuid,
                    "zaken_zaak_uuid": "df01f13a-844d-4901-9fe4-dd19603557c2",
                    "document_uuid": document_uuid,
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_read_only(self):
        document_uuid = "ea16fa8c-4bab-4065-a28a-f6574625205d"
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
