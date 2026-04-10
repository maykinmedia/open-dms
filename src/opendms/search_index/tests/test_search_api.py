from datetime import date

from maykin_common.vcr import VCRMixin
from rest_framework import status
from vng_api_common.tests import reverse

from opendms.api.tests.factories import ServiceFactory

from ..client import get_elasticsearch_client
from .base import ElasticSearchAPITestCase
from .factories import IndexDocumentFactory, IndexZaakFactory


class SearchApiTest(VCRMixin, ElasticSearchAPITestCase):
    url = reverse("api:search")
    maxDiff = None

    def test_no_body(self):
        doc = IndexDocumentFactory.build(uuid="525747fd-7e58-4005-8efa-59bcf4403385")

        self.index_document(doc)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data["count"], 1)
        results = data["results"]

        self.assertEqual(results[0]["data"]["uuid"], doc["uuid"])

    def test_pagination_next_and_previous(self):
        doc1 = IndexDocumentFactory.build(uuid="85a095ea-e1fa-438c-9e05-1862874f57a0")
        doc2 = IndexDocumentFactory.build(uuid="48981334-b480-4e7d-8c8d-925bbc67a969")

        self.index_document(doc1)
        self.index_document(doc2)

        response = self.client.post(self.url, {"page": 1, "pageSize": 1})
        data = response.json()

        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["results"]), 1)

    def test_pagination_previous(self):
        doc1 = IndexDocumentFactory.build(
            uuid="80485d67-0b97-4ed5-8483-f2d03d012e19",
            creatiedatum=date(2026, 1, 1),  # old
        )
        doc2 = IndexDocumentFactory.build(
            uuid="48981334-b480-4e7d-8c8d-925bbc67a969",
            creatiedatum=date(2026, 2, 1),  # new
        )

        self.index_document(doc1)
        self.index_document(doc2)

        response = self.client.post(self.url, {"page": 2, "pageSize": 1})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(data["count"], 2)
        # test if results have the same length as the count
        # ordered by creatiedatum
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(
            data["results"][0]["data"]["uuid"],
            "80485d67-0b97-4ed5-8483-f2d03d012e19",
        )

    def test_sort_chronological(self):
        doc1 = IndexDocumentFactory.build(
            uuid="80485d67-0b97-4ed5-8483-f2d03d012e19",
            creatiedatum=date(2026, 1, 1),  # old
        )
        doc2 = IndexDocumentFactory.build(
            uuid="48981334-b480-4e7d-8c8d-925bbc67a969",
            creatiedatum=date(2026, 2, 1),  # new
        )
        doc3 = IndexDocumentFactory.build(
            uuid="6a7a0f60-eeb7-4a99-8a88-7e49cea15f20",
            creatiedatum=date(2026, 3, 1),  # new
        )

        self.index_document(doc1)
        self.index_document(doc2)
        self.index_document(doc3)

        response = self.client.post(self.url, {"sort": "chronological"})
        data = response.json()

        self.assertEqual(data["count"], 3)

        self.assertEqual(data["results"][0]["data"]["uuid"], doc3["uuid"])
        self.assertEqual(data["results"][1]["data"]["uuid"], doc2["uuid"])
        self.assertEqual(data["results"][2]["data"]["uuid"], doc1["uuid"])

        # test if results have the same length as the count
        self.assertEqual(len(data["results"]), 3)

    def test_query(self):
        doc1 = IndexDocumentFactory.build(
            uuid="6dd95a10-cc97-4f19-b7e4-2c85358acb98",
            titel="Unique Document",
            identificatie="document1",
        )
        doc2 = IndexDocumentFactory.build(
            uuid="6ad95a10-cc97-4f19-b7e4-2c85358acb98",
            titel="Unique Document2",
            identificatie="document2",
        )
        self.index_document(doc1)
        self.index_document(doc2)

        response = self.client.post(self.url, {"query": "document1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(len(data["results"]), 1)
        hit = data["results"][0]["data"]
        self.assertEqual(hit["uuid"], doc1["uuid"])
        self.assertEqual(hit["titel"], doc1["titel"])
        self.assertEqual(hit["identificatie"], doc1["identificatie"])

    def test_query_field_boosts(self):
        ServiceFactory.create(for_download_url_mock_service=True)
        self.index_document(
            IndexDocumentFactory.build(
                uuid="3916925a-4260-4505-bfbb-0942113efd49",
                identificatie="snowflake",
            )
        )
        self.index_document(
            IndexDocumentFactory.build(
                uuid="d49bc304-01a1-4eda-a914-a8dda5c901e2",
                identificatie="document2",
                titel="snowflake",
            )
        )
        self.index_document(
            IndexDocumentFactory.build(
                uuid="bdcc4cea-b186-425e-8dcd-9fecb6818563",
                identificatie="document3",
                bestandsnaam="snowflake",
            )
        )
        self.index_document(
            IndexDocumentFactory.build(
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
        uuids = [value["data"]["uuid"] for value in data["results"]]
        self.assertIn("3916925a-4260-4505-bfbb-0942113efd49", uuids)
        self.assertIn("d49bc304-01a1-4eda-a914-a8dda5c901e2", uuids)
        self.assertIn("bdcc4cea-b186-425e-8dcd-9fecb6818563", uuids)
        self.assertIn("7eade718-bccb-4876-9f00-a095beebc360", uuids)

    def test_query_default_search_uses_AND_instead_of_OR(self):
        self.index_document(
            IndexDocumentFactory.build(
                uuid="9c3360b8-2ce7-4742-9051-e586b686fc48",
            )
        )
        self.index_document(
            IndexDocumentFactory.build(
                uuid="37eb1144-a3da-48d1-b2fb-88075f781611",
                titel="Document one of many",
            )
        )
        self.index_document(
            IndexDocumentFactory.build(
                uuid="da45268a-ab21-4a81-bfc4-b0430edf339b",
                titel="Document two of many",
            )
        )

        response = self.client.post(self.url, {"query": "document two"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(data["count"], 1)
        self.assertEqual(
            data["results"][0]["data"]["uuid"], "da45268a-ab21-4a81-bfc4-b0430edf339b"
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
        self.index_document(
            IndexDocumentFactory.build(
                uuid="d6eacab4-cb9f-42f7-abdf-719b358da923",
                beschrijving="Document one, on which we expect an exact phrase match.",
                # leave empty to avoid accidental hits
                titel="",
            )
        )
        self.index_document(
            IndexDocumentFactory.build(
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
                data["results"][0]["data"]["uuid"],
                "d6eacab4-cb9f-42f7-abdf-719b358da923",
            )

        with self.subTest("general search"):
            response = self.client.post(self.url, {"query": "document one"})

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            data = response.json()

            self.assertEqual(len(data["results"]), 2)
            uuids = {result["data"]["uuid"] for result in data["results"]}
            self.assertEqual(
                uuids,
                {
                    "d6eacab4-cb9f-42f7-abdf-719b358da923",
                    "a8fce14e-88d1-4f60-a69b-bbcc7033afe9",
                },
            )

    def test_query_boolean_operators(self):
        self.index_document(
            IndexDocumentFactory.build(
                uuid="d6eacab4-cb9f-42f7-abdf-719b358da923",
                beschrijving="snowflake1",
                titel="Document one",
            )
        )
        self.index_document(
            IndexDocumentFactory.build(
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
                data["results"][0]["data"]["uuid"],
                "d6eacab4-cb9f-42f7-abdf-719b358da923",
            )

        with self.subTest("AND behaviour", operator="AND"):
            response = self.client.post(self.url, {"query": "document AND one"})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertEqual(len(data["results"]), 1)
            self.assertEqual(
                data["results"][0]["data"]["uuid"],
                "d6eacab4-cb9f-42f7-abdf-719b358da923",
            )

        with self.subTest("OR behaviour", operator="|"):
            response = self.client.post(self.url, {"query": "one | two"})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertEqual(len(data["results"]), 2)
            uuids = {result["data"]["uuid"] for result in data["results"]}
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
            uuids = {result["data"]["uuid"] for result in data["results"]}
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
            uuids = {result["data"]["uuid"] for result in data["results"]}
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
        self.index_document(doc1)
        self.index_document(doc2)
        self.index_document(doc3)

        with self.subTest(
            creatiedatum_vanaf="2024-02-11", creatiedatum_tot_en_met=None
        ):
            response = self.client.post(self.url, {"creatiedatumVanaf": "2024-02-11"})

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["count"], 2)
            expected_ids = {
                "6aac4fb2-d532-490b-bd6b-87b0257c0236",
                "ef1dead2-e0f8-45be-acf7-3583adc14906",
            }
            ids = set(result["data"]["uuid"] for result in data["results"])
            self.assertEqual(ids, expected_ids)

        with self.subTest(
            creatiedatum_vanaf=None, creatiedatum_tot_en_met="2022-12-10"
        ):
            response = self.client.post(
                self.url, {"creatiedatumTotEnMet": "2022-12-10"}
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["count"], 1)
            expected_ids = {"62fceb92-98bd-475c-b184-49ee8a274787"}
            ids = set(result["data"]["uuid"] for result in data["results"])
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
            ids = set(result["data"]["uuid"] for result in data["results"])
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

        self.index_document(
            IndexDocumentFactory.build(
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

    def test_search_zaak_referenties(self):
        doc = IndexDocumentFactory.build(
            uuid="12fceb92-98bd-475c-b184-49ee8a274787",
            titel="Document with zaak",
            beschrijving="Some description",
            creatiedatum=date(2024, 2, 11),
            zaak_referenties=[
                {
                    "url": "http://example.com/zaak/62fceb92-98bd-475c-b184-49ee8a274787",
                    "uuid": "62fceb92-98bd-475c-b184-49ee8a274787",
                    "identificatie": "ZA123",
                    "omschrijving": "This is a test zaak",
                    "toelichting": "Extra info",
                    "status": "open",
                    "registratiedatum": date(2026, 1, 1),
                    "startdatum": date(2024, 2, 11),
                    "zaaktype": "http://example.com/zaaktype/52fceb92-98bd-475c-b184-49ee8a274787",
                    "object_type": "objectX",
                    "bronorganisatie": "org1",
                    "verantwoordelijkeOrganisatie": "org1",
                }
            ],
        )
        self.index_document(doc)

        with self.subTest("Query by nested field 'identificatie"):
            response = self.client.post(self.url, {"query": "ZA123"})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["count"], 1)
            self.assertEqual(
                data["results"][0]["data"]["uuid"],
                "12fceb92-98bd-475c-b184-49ee8a274787",
            )

        with self.subTest("Ensure nested zaak_referenties is returned correctly"):
            zaak_refs = data["results"][0]["data"].get("zaakReferenties", [])
            self.assertTrue(zaak_refs, "zaakReferenties should not be empty")
            self.assertEqual(
                zaak_refs[0]["uuid"], "62fceb92-98bd-475c-b184-49ee8a274787"
            )
            self.assertEqual(zaak_refs[0]["identificatie"], "ZA123")
            self.assertEqual(zaak_refs[0]["omschrijving"], "This is a test zaak")
            self.assertEqual(zaak_refs[0]["toelichting"], "Extra info")

        with self.subTest("Query by nested field 'omschrijving'"):
            response = self.client.post(self.url, {"query": "test zaak"})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["count"], 1)
            self.assertEqual(
                data["results"][0]["data"]["uuid"],
                "12fceb92-98bd-475c-b184-49ee8a274787",
            )

        with self.subTest("Query by nested field 'toelichting'"):
            response = self.client.post(self.url, {"query": "Extra info"})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["count"], 1)
            self.assertEqual(
                data["results"][0]["data"]["uuid"],
                "12fceb92-98bd-475c-b184-49ee8a274787",
            )

    def test_nested_zaak_query_boosts_and_operators(self):
        doc = IndexDocumentFactory.build(
            uuid="99999999-aaaa-bbbb-cccc-000000000001",
            titel="Document with nested zaak",
            beschrijving="Contains zaak info",
            zaak_referenties=[
                {
                    "url": "http://example.com/zaak/62fceb92-98bd-475c-b184-49ee8a274787",
                    "uuid": "11111111-2222-3333-4444-555555555555",
                    "identificatie": "ZA-BOOST-1",
                    "omschrijving": "Important nested zaak",
                    "toelichting": "Extra nested info",
                    "status": "open",
                    "registratiedatum": date(2026, 1, 1),
                    "startdatum": date(2024, 1, 1),
                    "zaaktype": "http://example.com/zaaktype/boost",
                    "object_type": "zaak",
                    "bronorganisatie": "org1",
                    "verantwoordelijkeOrganisatie": "org1",
                }
            ],
        )
        self.index_document(doc)

        # Search by nested 'identificatie'
        with self.subTest("Query nested identificate with boost"):
            response = self.client.post(self.url, {"query": "ZA-BOOST-1"})
            data = response.json()
            self.assertEqual(data["count"], 1)
            self.assertEqual(data["results"][0]["data"]["uuid"], doc["uuid"])

        # Search by nested 'omschrijving'
        with self.subTest("Query nested omschrijving with boost"):
            response = self.client.post(self.url, {"query": "Important nested zaak"})
            data = response.json()
            self.assertEqual(data["count"], 1)
            self.assertEqual(data["results"][0]["data"]["uuid"], doc["uuid"])

        # Search by nested 'toelichting'
        with self.subTest("Query nested toelichting"):
            response = self.client.post(self.url, {"query": "Extra nested info"})
            data = response.json()
            self.assertEqual(data["count"], 1)
            self.assertEqual(data["results"][0]["data"]["uuid"], doc["uuid"])

        # Boolean operator AND inside nested field
        with self.subTest("Boolean AND in nested field"):
            response = self.client.post(
                self.url, {"query": '"Important nested" AND zaak'}
            )
            data = response.json()
            self.assertEqual(data["count"], 1)
            self.assertEqual(data["results"][0]["data"]["uuid"], doc["uuid"])

        # Boolean operator OR inside nested field
        with self.subTest("Boolean OR in nested field"):
            response = self.client.post(self.url, {"query": "zaak OR nonmatch"})
            data = response.json()
            self.assertEqual(data["count"], 1)
            self.assertEqual(data["results"][0]["data"]["uuid"], doc["uuid"])

        # Exact phrase search
        with self.subTest("Exact phrase search in nested field"):
            response = self.client.post(self.url, {"query": '"Important nested zaak"'})
            data = response.json()
            self.assertEqual(data["count"], 1)
            self.assertEqual(data["results"][0]["data"]["uuid"], doc["uuid"])


class SearchLastDocumentCreatiedatumTests(VCRMixin, ElasticSearchAPITestCase):
    def test_returns_latest_creatiedatum(self):
        with get_elasticsearch_client() as client:
            client.index_document(
                IndexDocumentFactory.build(
                    uuid="62fdeb92-98ad-475c-b184-49ee8a274787",
                    creatiedatum=date(2024, 1, 1),
                )
            )
            client.index_document(
                IndexDocumentFactory.build(
                    uuid="13fceb92-98bd-475c-b184-49ee8a274787",
                    creatiedatum=date(2025, 2, 1),
                )
            )
            result = client.get_last_document_creatiedatum()

        self.assertEqual(result, "2025-02-01")

    def test_returns_none_when_no_documents(self):
        with get_elasticsearch_client() as client:
            result = client.get_last_document_creatiedatum()

        self.assertEqual(result, "")


class SearchZaakDocumentTests(VCRMixin, ElasticSearchAPITestCase):
    url = reverse("api:search")

    def test_returns_mixed_document_and_zaak(self):
        doc = IndexDocumentFactory.build(
            uuid="12fceb92-98bd-475c-b184-49ee8a274787",
            titel="Document match",
        )
        zaak = IndexZaakFactory.build(
            uuid="13fceb92-98bd-475c-b184-49ee8a274787",
            omschrijving="Zaak match",
        )

        self.index_document(doc)
        self.index_zaak(zaak)

        response = self.client.post(self.url, {"query": "match"})
        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["count"], 2)

        types = {result["type"] for result in data["results"]}
        self.assertEqual(types, {"document", "zaak"})

    def test_returns_only_documents(self):
        doc1 = IndexDocumentFactory.build(
            uuid="12fceb92-98bd-475c-b184-49ee8a274787", titel="Alpha Document"
        )
        doc2 = IndexDocumentFactory.build(
            uuid="13fceb92-98bd-475c-b184-49ee8a274787", titel="Beta Document"
        )
        zaak = IndexZaakFactory.build(
            uuid="14fceb92-98bd-475c-b184-49ee8a274787", omschrijving="Gamma Zaak"
        )

        self.index_document(doc1)
        self.index_document(doc2)
        self.index_zaak(zaak)

        response = self.client.post(self.url, {"query": "Document"})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["count"], 2)

        types = {result["type"] for result in data["results"]}
        self.assertEqual(types, {"document"})

    def test_returns_only_zaken(self):
        zaak1 = IndexZaakFactory.build(
            uuid="12fceb92-98bd-475c-b184-49ee8a274787", omschrijving="Finance Zaak"
        )
        zaak2 = IndexZaakFactory.build(
            uuid="13fceb92-98bd-475c-b184-49ee8a274787", omschrijving="HR Zaak"
        )
        doc = IndexDocumentFactory.build(
            uuid="14fceb92-98bd-475c-b184-49ee8a274787", titel="Marketing Document"
        )

        self.index_zaak(zaak1)
        self.index_zaak(zaak2)
        self.index_document(doc)

        response = self.client.post(self.url, {"query": "Zaak"})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["count"], 2)

        types = {result["type"] for result in data["results"]}
        self.assertEqual(types, {"zaak"})

    def test_pagination_mixed_results(self):
        doc1 = IndexDocumentFactory.build(
            uuid="12fceb92-98bd-475c-b184-49ee8a274787", titel="Doc 1"
        )
        doc2 = IndexDocumentFactory.build(
            uuid="13fceb92-98bd-475c-b184-49ee8a274787", titel="Doc 2"
        )
        zaak1 = IndexZaakFactory.build(
            uuid="14fceb92-98bd-475c-b184-49ee8a274787", omschrijving="Zaak 1"
        )
        zaak2 = IndexZaakFactory.build(
            uuid="15fceb92-98bd-475c-b184-49ee8a274787", omschrijving="Zaak 2"
        )

        self.index_document(doc1)
        self.index_document(doc2)
        self.index_zaak(zaak1)
        self.index_zaak(zaak2)

        response = self.client.post(self.url, {"query": "1", "page": 1, "pageSize": 2})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["results"]), 2)

    def test_handles_empty_query(self):
        doc = IndexDocumentFactory.build(
            uuid="12fceb92-98bd-475c-b184-49ee8a274787", titel="Any Document"
        )
        zaak = IndexZaakFactory.build(
            uuid="13fceb92-98bd-475c-b184-49ee8a274787", omschrijving="Any Zaak"
        )

        self.index_document(doc)
        self.index_zaak(zaak)

        response = self.client.post(self.url, {"query": ""})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["count"], 2)
        types = {result["type"] for result in data["results"]}
        self.assertEqual(types, {"document", "zaak"})

    def test_nested_zaak_referenties_returned_correctly(self):
        doc = IndexDocumentFactory.build(
            uuid="doc-100",
            titel="Document with zaak",
            zaak_referenties=[
                {
                    "url": "http://example.com/zaak/62fceb92-98bd-475c-b184-49ee8a274787",
                    "uuid": "11111111-2222-3333-4444-555555555555",
                    "identificatie": "ZA-BOOST-1",
                    "omschrijving": "Important nested zaak",
                    "toelichting": "Extra nested info",
                    "status": "open",
                    "registratiedatum": date(2026, 1, 1),
                    "startdatum": date(2024, 1, 1),
                    "zaaktype": "http://example.com/zaaktype/boost",
                    "object_type": "zaak",
                    "bronorganisatie": "org1",
                    "verantwoordelijkeOrganisatie": "org1",
                }
            ],
        )
        self.index_document(doc)

        response = self.client.post(self.url, {"query": "ZA-BOOST-1"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 1)

        zaak_refs = data["results"][0]["data"].get("zaakReferenties", [])
        self.assertTrue(zaak_refs)
        self.assertEqual(zaak_refs[0]["uuid"], "11111111-2222-3333-4444-555555555555")
        self.assertEqual(zaak_refs[0]["identificatie"], "ZA-BOOST-1")
        self.assertEqual(zaak_refs[0]["omschrijving"], "Important nested zaak")
        self.assertEqual(zaak_refs[0]["toelichting"], "Extra nested info")

    def test_zaak_query_fields(self):
        zaak = IndexZaakFactory.build(
            uuid="12fceb92-98bd-475c-b184-49ee8a274787",
            identificatie="ZAAK-IDENT",
            omschrijving="Unieke omschrijving",
            toelichting="Extra toelichting tekst",
            status="open",
        )
        self.index_zaak(zaak)

        with self.subTest("identificatie"):
            response = self.client.post(self.url, {"query": "ZAAK-IDENT"})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["count"], 1)
            self.assertEqual(data["results"][0]["data"]["uuid"], zaak["uuid"])

        with self.subTest("omschrijving"):
            response = self.client.post(self.url, {"query": "Unieke omschrijving"})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["count"], 1)

        with self.subTest("toelichting"):
            response = self.client.post(self.url, {"query": "Extra toelichting"})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["count"], 1)

        with self.subTest("status"):
            response = self.client.post(self.url, {"query": "open"})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["count"], 1)

    def test_zaak_query_default_and_behavior(self):
        zaak1 = IndexZaakFactory.build(
            uuid="12fceb92-98bd-475c-b184-49ee8a274787",
            omschrijving="alpha beta",
        )
        zaak2 = IndexZaakFactory.build(
            uuid="13fceb92-98bd-475c-b184-49ee8a274787",
            omschrijving="alpha",
        )

        self.index_zaak(zaak1)
        self.index_zaak(zaak2)

        response = self.client.post(self.url, {"query": "alpha beta"})
        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["count"], 1)
        self.assertEqual(
            data["results"][0]["data"]["uuid"], "12fceb92-98bd-475c-b184-49ee8a274787"
        )
        self.assertEqual(data["results"][0]["data"]["serviceSlug"], "test-service")
        self.assertEqual(data["results"][0]["data"]["groupSlug"], "test-group")

    def test_zaak_query_exact_match(self):
        zaak1 = IndexZaakFactory.build(
            uuid="12fceb92-98bd-475c-b184-49ee8a274787",
            omschrijving="exact phrase match",
        )
        zaak2 = IndexZaakFactory.build(
            uuid="13fceb92-98bd-475c-b184-49ee8a274787",
            omschrijving="exact phrase something else",
        )

        self.index_zaak(zaak1)
        self.index_zaak(zaak2)

        with self.subTest("exact match"):
            response = self.client.post(self.url, {"query": '"exact phrase match"'})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["count"], 1)
            self.assertEqual(
                data["results"][0]["data"]["uuid"],
                "12fceb92-98bd-475c-b184-49ee8a274787",
            )

        with self.subTest("non exact"):
            response = self.client.post(self.url, {"query": "exact phrase"})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["count"], 2)

    def test_zaak_query_boolean_operators(self):
        zaak1 = IndexZaakFactory.build(
            uuid="12fceb92-98bd-475c-b184-49ee8a274787",
            omschrijving="alpha one",
        )
        zaak2 = IndexZaakFactory.build(
            uuid="13fceb92-98bd-475c-b184-49ee8a274787",
            omschrijving="beta two",
        )

        self.index_zaak(zaak1)
        self.index_zaak(zaak2)

        with self.subTest("AND"):
            response = self.client.post(self.url, {"query": "alpha AND one"})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["count"], 1)
            self.assertEqual(
                data["results"][0]["data"]["uuid"],
                "12fceb92-98bd-475c-b184-49ee8a274787",
            )

        with self.subTest("OR"):
            response = self.client.post(self.url, {"query": "one OR two"})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["count"], 2)

    def test_zaak_recency_boosting(self):
        old = IndexZaakFactory.build(
            uuid="12fceb92-98bd-475c-b184-49ee8a274787",
            omschrijving="test omschrijving",
            registratiedatum=date(2024, 1, 1),
        )
        new = IndexZaakFactory.build(
            uuid="13fceb92-98bd-475c-b184-49ee8a274787",
            omschrijving="test omschrijving",
            registratiedatum=date(2026, 1, 1),
        )

        self.index_zaak(old)
        self.index_zaak(new)

        response = self.client.post(self.url, {"query": "test omschrijving"})
        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["count"], 2)
        self.assertEqual(
            data["results"][0]["data"]["uuid"], "13fceb92-98bd-475c-b184-49ee8a274787"
        )

    def test_zaak_vs_document_relevance(self):
        doc = IndexDocumentFactory.build(
            uuid="doc-1",
            titel="commonterm",
        )
        zaak = IndexZaakFactory.build(
            uuid="zaak-1",
            identificatie="commonterm",
        )

        self.index_document(doc)
        self.index_zaak(zaak)

        response = self.client.post(self.url, {"query": "commonterm"})
        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["count"], 2)

        # Zaak should rank higher due to identificatie boost
        self.assertEqual(data["results"][0]["type"], "zaak")
        self.assertEqual(data["results"][0]["data"]["uuid"], "zaak-1")
