from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from maykin_common.vcr import VCRMixin
from rest_framework import status
from vng_api_common.tests import reverse

from opendms.api.tests.api_testcase import APITestCase
from opendms.api.tests.factories import ServiceFactory

from ..client import search_last_document_creatiedatum
from ..tasks import index_document
from .base import ElasticSearchAPITestCase
from .factories import IndexDocumentFactory


class SearchApiAuthenticationTest(APITestCase):
    url = reverse("api:search")

    @patch("opendms.search_index.api.views.get_search_results")
    def test_permissions(self, mock_search):
        mock_search.return_value = SimpleNamespace(total_count=0, results=[])

        # logout
        self.client.logout()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # login
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SearchApiTest(VCRMixin, ElasticSearchAPITestCase):
    url = reverse("api:search")
    maxDiff = None

    def test_no_body(self):
        doc = IndexDocumentFactory.build(
            uuid="525747fd-7e58-4005-8efa-59bcf4403385",
        )
        index_document(**doc)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data["count"], 1)

        results = data["results"]
        self.assertEqual(results[0]["record"]["uuid"], doc["uuid"])

    def test_pagination_next_and_previous(self):
        doc1 = IndexDocumentFactory.build(
            uuid="85a095ea-e1fa-438c-9e05-1862874f57a0",
        )
        doc2 = IndexDocumentFactory.build(
            uuid="48981334-b480-4e7d-8c8d-925bbc67a969",
        )
        index_document(**doc1)
        index_document(**doc2)

        response = self.client.post(self.url, {"page": 1, "pageSize": 1})
        data = response.json()

        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["results"]), 1)

    def test_pagination_previous(self):
        index_document(
            **IndexDocumentFactory.build(
                uuid="80485d67-0b97-4ed5-8483-f2d03d012e19",
            )
        )
        index_document(
            **IndexDocumentFactory.build(
                uuid="48981334-b480-4e7d-8c8d-925bbc67a969",
            )
        )

        response = self.client.post(self.url, {"page": 2, "pageSize": 1})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(data["count"], 2)
        # test if results have the same length as the count
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(
            data["results"][0]["record"]["uuid"], "80485d67-0b97-4ed5-8483-f2d03d012e19"
        )

    def test_sort_chronological(self):
        doc1 = IndexDocumentFactory.build(
            uuid="3b3f4514-7d8b-4e31-83ca-fa9376ff6522",
            creatiedatum=date(2026, 1, 2),
        )
        doc2 = IndexDocumentFactory.build(
            uuid="4b3f4514-7d8b-4e31-83ca-fa9376ff6523",
            creatiedatum=date(2026, 1, 3),
        )
        index_document(**doc1)
        index_document(**doc2)

        response = self.client.post(self.url, {"sort": "chronological"})
        data = response.json()

        self.assertEqual(data["count"], 2)

        self.assertEqual(data["results"][0]["record"]["uuid"], doc2["uuid"])
        self.assertEqual(data["results"][1]["record"]["uuid"], doc1["uuid"])
        # test if results have the same length as the count
        self.assertEqual(len(data["results"]), 2)

    def test_query(self):
        doc = IndexDocumentFactory.build(
            uuid="6dd95a10-cc97-4f19-b7e4-2c85358acb98",
            titel="Unique Document",
            identificatie="document1",
        )
        doc2 = IndexDocumentFactory.build(
            uuid="6ad95a10-cc97-4f19-b7e4-2c85358acb98",
            titel="Unique Document2",
            identificatie="document2",
        )
        index_document(**doc)
        index_document(**doc2)

        response = self.client.post(self.url, {"query": "document1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(len(data["results"]), 1)
        hit = data["results"][0]["record"]
        self.assertEqual(hit["uuid"], doc["uuid"])
        self.assertEqual(hit["titel"], doc["titel"])
        self.assertEqual(hit["identificatie"], doc["identificatie"])

    def test_query_field_boosts(self):
        ServiceFactory.create(for_download_url_mock_service=True)
        index_document(
            **IndexDocumentFactory.build(
                uuid="3916925a-4260-4505-bfbb-0942113efd49",
                identificatie="snowflake",
            )
        )
        index_document(
            **IndexDocumentFactory.build(
                uuid="d49bc304-01a1-4eda-a914-a8dda5c901e2",
                identificatie="document2",
                titel="snowflake",
            )
        )
        index_document(
            **IndexDocumentFactory.build(
                uuid="bdcc4cea-b186-425e-8dcd-9fecb6818563",
                identificatie="document3",
                bestandsnaam="snowflake",
            )
        )
        index_document(
            **IndexDocumentFactory.build(
                uuid="7eade718-bccb-4876-9f00-a095beebc360",
                identificatie="document4",
                beschrijving="snowflake",
            )
        )

        # Search for "snowflake"
        response = self.client.post(self.url, {"query": "snowflake"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Count should include all matches
        self.assertEqual(data["count"], 4)

        # Check the priority according to field boosts
        # Boost priority:
        # identificatie > titel > beschrijving > document_data.attachment.content > url
        self.assertEqual(
            data["results"][0]["record"]["uuid"], "3916925a-4260-4505-bfbb-0942113efd49"
        )
        self.assertEqual(
            data["results"][1]["record"]["uuid"], "d49bc304-01a1-4eda-a914-a8dda5c901e2"
        )
        self.assertEqual(
            data["results"][2]["record"]["uuid"], "bdcc4cea-b186-425e-8dcd-9fecb6818563"
        )
        self.assertEqual(
            data["results"][3]["record"]["uuid"], "7eade718-bccb-4876-9f00-a095beebc360"
        )

    def test_query_default_search_uses_AND_instead_of_OR(self):
        index_document(
            **IndexDocumentFactory.build(
                uuid="9c3360b8-2ce7-4742-9051-e586b686fc48",
            )
        )
        index_document(
            **IndexDocumentFactory.build(
                uuid="37eb1144-a3da-48d1-b2fb-88075f781611",
                titel="Document one of many",
            )
        )
        index_document(
            **IndexDocumentFactory.build(
                uuid="da45268a-ab21-4a81-bfc4-b0430edf339b",
                titel="Document two of many",
            )
        )

        response = self.client.post(self.url, {"query": "document two"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(data["count"], 1)
        self.assertEqual(
            data["results"][0]["record"]["uuid"], "da45268a-ab21-4a81-bfc4-b0430edf339b"
        )

    def test_broken_query_string_syntax(self):
        with self.subTest("Broken quotes and dangling AND"):
            response = self.client.post(self.url, {"query": '"document two AND'})

            self.assertEqual(response.status_code, status.HTTP_200_OK)

        with self.subTest("OR at end"):
            response = self.client.post(self.url, {"query": "document OR"})

            self.assertEqual(response.status_code, status.HTTP_200_OK)

        with self.subTest("Leading AND operator"):
            response = self.client.post(self.url, {"query": "AND document"})

            self.assertEqual(response.status_code, status.HTTP_200_OK)

        with self.subTest("Only boolean operators"):
            response = self.client.post(self.url, {"query": "AND OR AND"})

            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_query_with_exact_match_using_double_quotes(self):
        index_document(
            **IndexDocumentFactory.build(
                uuid="d6eacab4-cb9f-42f7-abdf-719b358da923",
                beschrijving="Document one, on which we expect an exact phrase match.",
                # leave empty to avoid accidental hits
                titel="",
            )
        )
        index_document(
            **IndexDocumentFactory.build(
                uuid="a8fce14e-88d1-4f60-a69b-bbcc7033afe9",
                beschrijving="Document two, the document that came after one.",
                # leave empty to avoid accidental hits
                titel="",
            )
        )

        with self.subTest("Exact search using double quotes"):
            response = self.client.post(self.url, {"query": '"document one"'})

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            data = response.json()

            self.assertEqual(len(data["results"]), 1)
            # Document one
            self.assertEqual(
                data["results"][0]["record"]["uuid"],
                "d6eacab4-cb9f-42f7-abdf-719b358da923",
            )

        with self.subTest("general search"):
            response = self.client.post(self.url, {"query": "document one"})

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            data = response.json()

            self.assertEqual(len(data["results"]), 2)
            uuids = {result["record"]["uuid"] for result in data["results"]}
            self.assertEqual(
                uuids,
                {
                    "d6eacab4-cb9f-42f7-abdf-719b358da923",
                    "a8fce14e-88d1-4f60-a69b-bbcc7033afe9",
                },
            )

    def test_query_boolean_operators(self):
        index_document(
            **IndexDocumentFactory.build(
                uuid="d6eacab4-cb9f-42f7-abdf-719b358da923",
                beschrijving="snowflake1",
                titel="Document one",
            )
        )
        index_document(
            **IndexDocumentFactory.build(
                uuid="a8fce14e-88d1-4f60-a69b-bbcc7033afe9",
                beschrijving="snowflake2",
                titel="Document two",
            )
        )

        with self.subTest("AND behaviour", operator="+"):
            response = self.client.post(self.url, {"query": "document + one"})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertEqual(len(data["results"]), 1)
            self.assertEqual(
                data["results"][0]["record"]["uuid"],
                "d6eacab4-cb9f-42f7-abdf-719b358da923",
            )

        with self.subTest("AND behaviour", operator="AND"):
            response = self.client.post(self.url, {"query": "document AND one"})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertEqual(len(data["results"]), 1)
            self.assertEqual(
                data["results"][0]["record"]["uuid"],
                "d6eacab4-cb9f-42f7-abdf-719b358da923",
            )

        with self.subTest("OR behaviour", operator="|"):
            response = self.client.post(self.url, {"query": "one | two"})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertEqual(len(data["results"]), 2)
            uuids = {result["record"]["uuid"] for result in data["results"]}
            self.assertEqual(
                uuids,
                {
                    "d6eacab4-cb9f-42f7-abdf-719b358da923",
                    "a8fce14e-88d1-4f60-a69b-bbcc7033afe9",
                },
            )

        with self.subTest("OR behaviour", operator="OR"):
            response = self.client.post(self.url, {"query": "one OR two"})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertEqual(len(data["results"]), 2)
            uuids = {result["record"]["uuid"] for result in data["results"]}
            self.assertEqual(
                uuids,
                {
                    "d6eacab4-cb9f-42f7-abdf-719b358da923",
                    "a8fce14e-88d1-4f60-a69b-bbcc7033afe9",
                },
            )

        with self.subTest("complex case with precedence rules"):
            query = '("snowflake1" AND  one) OR ("Document two")'
            response = self.client.post(self.url, {"query": query})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertEqual(len(data["results"]), 2)
            uuids = {result["record"]["uuid"] for result in data["results"]}
            self.assertEqual(
                uuids,
                {
                    "d6eacab4-cb9f-42f7-abdf-719b358da923",
                    "a8fce14e-88d1-4f60-a69b-bbcc7033afe9",
                },
            )


class SearchApiFilterTests(VCRMixin, ElasticSearchAPITestCase):
    url = reverse("api:search")
    maxDiff = None

    def test_filter_on_creatiedatum(self):
        doc1 = IndexDocumentFactory.build(
            uuid="6aac4fb2-d532-490b-bd6b-87b0257c0236",
            creatiedatum=date(2024, 2, 11),
        )
        doc2 = IndexDocumentFactory.build(
            uuid="62fceb92-98bd-475c-b184-49ee8a274787",
            creatiedatum=date(2022, 12, 10),
        )
        doc3 = IndexDocumentFactory.build(
            uuid="ef1dead2-e0f8-45be-acf7-3583adc14906",
            creatiedatum=date(2025, 1, 14),
        )
        index_document(**doc1)
        index_document(**doc2)
        index_document(**doc3)

        with self.subTest(
            creatiedatum_vanaf="2024-02-11", creatiedatum_tot_en_met=None
        ):
            response = self.client.post(
                self.url,
                {
                    "creatiedatumVanaf": "2024-02-11",
                },
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["count"], 2)
            expected_ids = {
                "6aac4fb2-d532-490b-bd6b-87b0257c0236",
                "ef1dead2-e0f8-45be-acf7-3583adc14906",
            }
            ids = set(result["record"]["uuid"] for result in data["results"])
            self.assertEqual(ids, expected_ids)

        with self.subTest(
            creatiedatum_vanaf=None, creatiedatum_tot_en_met="2022-12-10"
        ):
            response = self.client.post(
                self.url,
                {
                    "creatiedatumTotEnMet": "2022-12-10",
                },
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["count"], 1)
            expected_ids = {"62fceb92-98bd-475c-b184-49ee8a274787"}
            ids = set(result["record"]["uuid"] for result in data["results"])
            self.assertEqual(ids, expected_ids)

        with self.subTest(
            creatiedatum_vanaf="2024-01-01", creatiedatum_tot_en_met="2024-12-31"
        ):
            response = self.client.post(
                self.url,
                {
                    "creatiedatumVanaf": "2024-01-01",
                    "creatiedatumTotEnMet": "2024-12-31",
                },
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["count"], 1)
            expected_ids = {"6aac4fb2-d532-490b-bd6b-87b0257c0236"}
            ids = set(result["record"]["uuid"] for result in data["results"])
            self.assertEqual(ids, expected_ids)

    def test_dutch_analyzer(self):
        """
        Dutch analyzer test. Use a word which is present in the example of:
        https://snowballstem.org/algorithms/dutch/stemmer.html

        This way we have a clear reference point. for our test case we will use
        'lichamelijk'.
        So we are going to test that `lichamelijk`, `lichamelijke` and
        `lichamelijkheden` will result in a match.
        """

        index_document(
            **IndexDocumentFactory.build(
                uuid="828df354-b6dc-4693-815a-1b7d39b3bc95",
                titel="Dutch analyzer",
                beschrijving=""
                "Een document om de Nederlandse analyzer te testen. "
                "We doen dit door middel van een willekeurige stem (in ons geval "
                "'lichamelijk') in deze tekst te vermelden, zodat we kunnen zoeken met"
                "woorden die de zelfde stem bevatten.",
            )
        )

        with self.subTest("lichamelijk"):
            response = self.client.post(self.url, {"query": "lichamelijk"})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertEqual(data["count"], 1)

        with self.subTest("lichamelijke"):
            response = self.client.post(self.url, {"query": "lichamelijke"})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertEqual(data["count"], 1)

        with self.subTest("lichamelijkheden"):
            response = self.client.post(self.url, {"query": "lichamelijkheden"})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertEqual(data["count"], 1)

        with self.subTest("search without the use of a stem produces no results."):
            response = self.client.post(self.url, {"query": "lich"})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertEqual(data["count"], 0)


class SearchLastDocumentCreatiedatumTests(VCRMixin, ElasticSearchAPITestCase):
    def test_returns_latest_creatiedatum(self):
        index_document(
            **IndexDocumentFactory.build(
                uuid="62fdeb92-98ad-475c-b184-49ee8a274787",
                creatiedatum=date(2024, 1, 1),
            )
        )
        index_document(
            **IndexDocumentFactory.build(
                uuid="13fceb92-98bd-475c-b184-49ee8a274787",
                creatiedatum=date(2025, 2, 1),
            )
        )

        result = search_last_document_creatiedatum()

        self.assertEqual(result, "2025-02-01")

    def test_returns_none_when_no_documents(self):
        result = search_last_document_creatiedatum()

        self.assertIsNone(result)
