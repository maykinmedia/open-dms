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

        data = response.json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(
            data["results"][0]["uuid"], "ea16fa8c-4bab-4065-a28a-f6574625205d"
        )
        self.assertEqual(
            data["results"][0]["url"],
            "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/ea16fa8c-4bab-4065-a28a-f6574625205d",
        )
        self.assertEqual(
            data["results"][0]["identificatie"], "DOCUMENT-2026-0000000001"
        )
        self.assertEqual(data["results"][0]["creatiedatum"], "2026-01-15")
        self.assertEqual(data["results"][0]["titel"], "aanvraag formulier")
        self.assertEqual(data["results"][0]["auteur"], "Niek van den Berg")
        self.assertEqual(data["results"][0]["taal"], "nld")
        self.assertEqual(
            data["results"][0]["beginRegistratie"], "2026-03-25T13:51:49.784000Z"
        )
        self.assertEqual(
            data["results"][0]["informatieobjecttype"],
            "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/7f420939-2866-4582-8b94-f21d3891daab",
        )
        self.assertEqual(
            data["results"][0]["vertrouwelijkheidaanduiding"], "confidentieel"
        )
        self.assertEqual(
            data["results"][0]["inhoud"],
            "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/ea16fa8c-4bab-4065-a28a-f6574625205d/download?versie=1",
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

        data = response.json()
        self.assertEqual(data["uuid"], document_uuid)
        self.assertEqual(
            data["url"],
            "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/ea16fa8c-4bab-4065-a28a-f6574625205d",
        )
        self.assertEqual(data["identificatie"], "DOCUMENT-2026-0000000001")
        self.assertEqual(data["bronorganisatie"], "000000115")
        self.assertEqual(data["creatiedatum"], "2026-01-15")
        self.assertEqual(data["titel"], "aanvraag formulier")
        self.assertEqual(data["auteur"], "Niek van den Berg")
        self.assertEqual(data["taal"], "nld")
        self.assertEqual(data["beginRegistratie"], "2026-03-25T13:51:49.784000Z")
        self.assertEqual(
            data["informatieobjecttype"],
            "http://localhost:8003/catalogi/api/v1/informatieobjecttypen/7f420939-2866-4582-8b94-f21d3891daab",
        )
        self.assertEqual(data["vertrouwelijkheidaanduiding"], "confidentieel")
        self.assertEqual(data["status"], "")
        self.assertEqual(data["formaat"], "")
        self.assertEqual(data["bestandsnaam"], "")
        self.assertEqual(data["link"], "")
        self.assertEqual(data["beschrijving"], "")
        self.assertEqual(data["verschijningsvorm"], "")
        self.assertIsNone(data["bestandsomvang"])
        self.assertEqual(
            data["inhoud"],
            "http://localhost:8003/documenten/api/v1/enkelvoudiginformatieobjecten/ea16fa8c-4bab-4065-a28a-f6574625205d/download?versie=1",
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
            response.content,
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

        data = {}

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

    def test_create_document(self):
        payload = {
            "bronorganisatie": "000000000",
            "creatiedatum": "2026-06-02",
            "titel": "Test document",
            "auteur": "Test User",
            "taal": "nld",
            "informatieobjecttype": (
                "http://localhost:8003/catalogi/api/v1/"
                "informatieobjecttypen/7f420939-2866-4582-8b94-f21d3891daab"
            ),
            "bestandsnaam": "test.txt",
            "formaat": "text/plain",
            "beschrijving": "Test description",
        }

        response = self.client.post(
            self.list_url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        data = response.json()

        self.assertEqual(
            data["bronorganisatie"],
            payload["bronorganisatie"],
        )
        self.assertEqual(
            data["creatiedatum"],
            payload["creatiedatum"],
        )
        self.assertEqual(
            data["titel"],
            payload["titel"],
        )
        self.assertEqual(
            data["auteur"],
            payload["auteur"],
        )
        self.assertEqual(
            data["taal"],
            payload["taal"],
        )
        self.assertEqual(
            data["informatieobjecttype"],
            payload["informatieobjecttype"],
        )
        self.assertEqual(
            data["bestandsnaam"],
            payload["bestandsnaam"],
        )
        self.assertEqual(
            data["formaat"],
            payload["formaat"],
        )
        self.assertEqual(
            data["beschrijving"],
            payload["beschrijving"],
        )

        self.assertIn("uuid", data)
        self.assertIn("url", data)

    def test_create_document_invalid_payload(self):
        response = self.client.post(
            self.list_url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        invalid_params = response.data["invalid_params"]
        field_names = {param["name"] for param in invalid_params}

        self.assertEqual(
            field_names,
            {
                "bronorganisatie",
                "creatiedatum",
                "titel",
                "auteur",
                "taal",
                "informatieobjecttype",
            },
        )
