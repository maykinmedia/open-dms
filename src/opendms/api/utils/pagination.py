from rest_framework.response import Response
from vng_api_common.pagination import DynamicPageSizePagination


class CountedPagination(DynamicPageSizePagination):
    """
    Pagination class that returns total count and results in a JSON response.
    """

    def get_paginated_response(self, data) -> Response:
        return Response(
            {
                "count": self.page.paginator.count,
                "results": data,
            }
        )
