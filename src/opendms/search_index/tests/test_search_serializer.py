"""
Unit test the serializer used for the search endpoint.
"""

from django.test import SimpleTestCase

from ..api.serializers import SearchSerializer


class SerializerValidationTests(SimpleTestCase):
    def test_validate_creatiedatum(self):
        with self.subTest("no dates given", result_type="document"):
            serializer1 = SearchSerializer(
                data={
                    "creatiedatum_vanaf": None,
                    "creatiedatum_tot_en_met": None,
                }
            )

            self.assertTrue(serializer1.is_valid())

        with self.subTest("from date given", result_type="document"):
            serializer2 = SearchSerializer(
                data={
                    "creatiedatum_vanaf": "2024-01-01",
                    "creatiedatum_tot_en_met": None,
                }
            )

            self.assertTrue(serializer2.is_valid())

        with self.subTest("to date given", result_type="document"):
            serializer3 = SearchSerializer(
                data={
                    "creatiedatum_vanaf": None,
                    "creatiedatum_tot_en_met": "2024-01-01",
                }
            )

            self.assertTrue(serializer3.is_valid())
