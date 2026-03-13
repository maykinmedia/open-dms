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

    def get_paginated_response_schema(self, schema) -> dict:
        return {
            "type": "object",
            "required": ["count", "results"],
            "properties": {
                "count": {
                    "type": "integer",
                    "example": 123,
                },
                "results": schema,
            },
        }
