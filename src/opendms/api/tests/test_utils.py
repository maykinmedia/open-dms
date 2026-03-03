from django.test import SimpleTestCase

from ..utils.validators import extract_uuid


class UUIDValidatorsTestCase(SimpleTestCase):
    def test_extract_uuid(self):

        valid = [
            (
                "http://testserver/catalogi/api/v1/catalogussen/e035387e-6374-4eb9-b3d1-416294402bae",
                "e035387e-6374-4eb9-b3d1-416294402bae",
            ),
            (
                "http://testserver/e035387e-6374-4eb9-b3d1-416294402bae",
                "e035387e-6374-4eb9-b3d1-416294402bae",
            ),
        ]

        for value in valid:
            with self.subTest(value=value):
                assert extract_uuid(value[0]) == value[1]

    def test_invalid_extract_uuid(self):

        valid = [
            "http://testserver/catalogi/api/v1/catalogussen/test",
            "http://testserver/catalogi/api/v1/catalogussen/123",
            "test",
            "http://testserver/e035387e-6374-4eb9",
        ]

        for value in valid:
            with self.subTest(value=value):
                assert extract_uuid(value) is None
