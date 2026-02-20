from django.utils.translation import gettext_lazy as _

from drf_polymorphic.serializers import PolymorphicSerializer
from rest_framework import serializers

from ...client import SearchResult, SearchResults
from ...constants import SortChoices
from . import DocumentSerializer


class SearchSerializer(serializers.Serializer):
    query = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_(
            "Filtering records based on the provided search term. "
            "This search is applied to the following fields:\n\n"
            "- `identificatie`\n"
            "- `titel`\n"
            "- `bronorganisatie`\n"
            "- `bestandsnaam`\n"
            "- `document_data.attachment.content`\n\n"
            "You can use double quotes for exact matches and `AND`/`OR` syntax for complex queries."
        ),
        default="",
    )
    page = serializers.IntegerField(default=1, help_text=_("Page number."))
    page_size = serializers.IntegerField(
        default=10, help_text=_("Number of results per page.")
    )
    sort = serializers.ChoiceField(
        choices=SortChoices.choices, default=SortChoices.relevance
    )
    creatiedatum_vanaf = serializers.DateField(
        required=False,
        allow_null=True,
        default=None,
        help_text=_("Filter documents created on or after this date."),
    )
    creatiedatum_tot_en_met = serializers.DateField(
        required=False,
        allow_null=True,
        default=None,
        help_text=_("Filter documents created on or before this date."),
    )


class DocumentResultSerializer(serializers.Serializer[SearchResult]):
    record = DocumentSerializer(read_only=True)


class SearchResultsSerializer(PolymorphicSerializer):
    type = serializers.CharField()
    discriminator_field = "type"
    serializer_mapping = {
        "document": DocumentResultSerializer,
    }


class SearchResponseSerializer(serializers.Serializer[SearchResults]):
    count = serializers.IntegerField(source="total_count")
    next = serializers.SerializerMethodField()
    previous = serializers.SerializerMethodField()
    results = SearchResultsSerializer(many=True)

    def get_next(self, instance: SearchResults) -> bool:
        page: int = self.context.get("page", 1)
        page_size: int = self.context.get("page_size", 10)
        return page * page_size < instance.total_count

    def get_previous(self, instance: SearchResults) -> bool:
        return self.context.get("page", 1) > 1
