from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from ..client import get_elasticsearch_client
from ..typing import SearchParameters
from .serializers import SearchResponseSerializer, SearchSerializer


class SearchView(APIView):
    # TODO make GET is not allowed
    # TODO check extend_schema
    @extend_schema(
        tags=["search"],
        summary=_("Search"),
        operation_id="search",
        description=_("Search the document records."),
        request=SearchSerializer,
        responses={200: SearchResponseSerializer(many=True)},
    )
    def post(self, request, *args, **kwargs):
        query_serializer = SearchSerializer(data=request.data)
        query_serializer.is_valid(raise_exception=True)
        params: SearchParameters = query_serializer.validated_data

        # TODO check if params are required or not

        with get_elasticsearch_client() as client:
            search_results = client.get_search_results(
                query=params["query"],
                creatiedatum_from=params["creatiedatum_vanaf"],
                creatiedatum_to=params["creatiedatum_tot_en_met"],
                page=(page := params["page"]),
                page_size=(page_size := params["page_size"]),
                sort=params["sort"],
            )

        response = SearchResponseSerializer(
            instance=search_results,
            context={"page": page, "page_size": page_size},
        )
        return Response(response.data)
