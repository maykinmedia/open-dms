from rest_framework import status
from vng_api_common.tests import reverse
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service
from zgw_consumers.test.factories import ServiceFactory

from .api_testcase import APITestCase


class ServiceTests(APITestCase):
    list_url = reverse("api:service-list")
    maxDiff = None

    def test_list(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 0)
        self.assertFalse(Service.objects.exists())

        # create Service
        ServiceFactory.create(
            label="label-test", slug="slug-test", api_type=APITypes.ztc
        )
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(Service.objects.all().count(), 1)

        self.assertEqual(
            response.json(),
            {
                "count": 1,
                "results": [{"slug": "slug-test", "label": "label-test"}],
            },
        )
        # should be displayed
        ServiceFactory.create(api_type=APITypes.ztc)
        ServiceFactory.create(api_type=APITypes.ztc)

        # should not be displayed
        ServiceFactory.create(api_type=APITypes.orc)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 3)
        self.assertEqual(Service.objects.all().count(), 4)

    def test_list_pagination_pagesize_param(self):
        ServiceFactory.create_batch(10, api_type=APITypes.ztc)
        response = self.client.get(self.list_url, {"pageSize": 5})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["count"], 10)
        self.assertEqual(len(data["results"]), 5)

    def test_detail(self):
        # create Service
        service = ServiceFactory.create(
            label="label-test", slug="slug-test", api_type=APITypes.ztc
        )

        detail_url = reverse("api:service-detail", kwargs={"slug": service.slug})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {"slug": "slug-test", "label": "label-test"},
        )

    def test_detail_service_not_found(self):
        detail_url = reverse("api:service-detail", kwargs={"slug": "test"})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["code"], "not_found")
        self.assertEqual(response.data["detail"], "Niet gevonden.")

    def test_read_only(self):
        service = ServiceFactory.create()
        detail_url = reverse("api:service-detail", kwargs={"slug": service.slug})

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


class ServicePermissionTests(APITestCase):
    list_url = reverse("api:service-list")
    maxDiff = None

    def test_list_permissions(self):
        # logout first
        self.client.logout()

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["code"], "not_authenticated")
        self.assertEqual(
            response.data["detail"], "Authenticatiegegevens zijn niet opgegeven."
        )

        # login
        self.client.force_login(self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_permissions(self):
        service = ServiceFactory.create(api_type=APITypes.ztc)
        detail_url = reverse("api:service-detail", kwargs={"slug": service.slug})

        # logout first
        self.client.logout()

        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["code"], "not_authenticated")
        self.assertEqual(
            response.data["detail"], "Authenticatiegegevens zijn niet opgegeven."
        )

        # login
        self.client.force_login(self.user)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ServiceFiltersTests(APITestCase):
    list_url = reverse("api:service-list")
    maxDiff = None

    def test_search(self):
        # should be displayed
        service_0 = ServiceFactory.create(
            api_type=APITypes.ztc,
            slug="foo",
            api_root="http://www.example.com/bar",
            label="bar",
        )
        service_1 = ServiceFactory.create(
            api_type=APITypes.ztc,
            slug="bar1",
            api_root="http://www.example.com/foo",
            label="bar",
        )
        service_2 = ServiceFactory.create(
            api_type=APITypes.ztc,
            slug="bar2",
            api_root="http://www.example.com/bar2",
            label="foo",
        )

        # should not be displayed
        ServiceFactory.create(
            api_type=APITypes.ztc,
            slug="bar3",
            api_root="http://www.example.com/bar3",
            label="bar",
        )
        ServiceFactory.create(
            api_type=APITypes.ztc,
            slug="bar4",
            api_root="http://www.example.com/bar4",
            label="bar",
        )
        ServiceFactory.create(
            api_type=APITypes.ztc,
            slug="bar5",
            api_root="http://www.example.com/bar5",
            label="bar",
        )

        response = self.client.get(self.list_url, query_params={"search": "fo"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 3)
        self.assertEqual(Service.objects.all().count(), 6)
        self.assertEqual(response.json()["results"][0]["slug"], service_0.slug)
        self.assertEqual(response.json()["results"][1]["slug"], service_1.slug)
        self.assertEqual(response.json()["results"][2]["slug"], service_2.slug)
