from rest_framework.request import Request
from rest_framework.response import Response


class ReadOnlyViewSetMixin:
    def get_serializer_context(self):
        return {"request": self.request, "format": self.format_kwarg, "view": self}

    def get_serializer(self, *args, **kwargs):
        kwargs["context"] = self.get_serializer_context()
        return self.serializer_class(*args, **kwargs)

    def list(self, request: Request, *args, **kwargs) -> Response:
        items = self.get_queryset(request.query_params)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(items, request)
        if page is not None:
            serializer = self.serializer_class(
                page, many=True, context=self.get_serializer_context()
            )
            return paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
