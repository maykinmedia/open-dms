from maykin_common.vcr import VCRMixin
from rest_framework import status
from vng_api_common.tests import reverse

from opendms.api.tests.factories import ServiceFactory

from .api_testcase import APITestCase


class InformatieObjectTypeViewSetTests(VCRMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.ztc_service = ServiceFactory.create(
            for_ztc_service_docker_compose=True,
        )

        cls.list_url = reverse(
            "api:informatieobjecttypen-list",
            kwargs={
                "service_slug": cls.ztc_service.slug,
            },
        )

    def test_list_informatieobjecttypen(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(data["count"], 1)
        self.assertEqual(len(data["results"]), 1)

        result = data["results"][0]

        self.assertEqual(
            result["uuid"],
            "7f420939-2866-4582-8b94-f21d3891daab",
        )
        self.assertEqual(
            result["omschrijving"],
            "aanvraag formulier",
        )
        self.assertEqual(
            result["informatieobjectcategorie"],
            "producten",
        )
        self.assertFalse(result["concept"])

        self.assertEqual(len(result["zaaktypen"]), 2)

    def test_read_only(self):
        response = self.client.post(self.list_url, {})

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_retrieve_informatieobjecttype(self):
        url = reverse(
            "api:informatieobjecttypen-detail",
            kwargs={
                "service_slug": self.ztc_service.slug,
                "informatieobjecttype_uuid": ("7f420939-2866-4582-8b94-f21d3891daab"),
            },
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(
            data["omschrijving"],
            "aanvraag formulier",
        )
        self.assertEqual(
            data["informatieobjectcategorie"],
            "producten",
        )
