from typing import Any, Literal, TypedDict

type IndexName = Literal["document", "zaak"]


class SearchResultItem(TypedDict):
    type: IndexName
    data: dict[str, Any]
