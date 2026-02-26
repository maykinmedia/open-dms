from uuid import UUID

from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from opendms.api.serializers import CeleryTaskIdSerializer

from ..tasks import index_document, remove_document_from_index
from ..typing import DocumentIndexType
from .serializers import DocumentIndexSerializer


@extend_schema(tags=["index"])
class DocumentViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = DocumentIndexSerializer
    lookup_field = "uuid"

    @extend_schema(
        summary=_("Index document metadata."),
        description=_(
            "Index the received document metadata from the Register API in "
            "Elasticsearch."
        ),
        responses={202: CeleryTaskIdSerializer},
    )
    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data: DocumentIndexType = serializer.validated_data

        # Schedule indexing task
        save_document_task = index_document.delay(
            uuid=validated_data["uuid"],
            url=validated_data["url"],
            identificatie=validated_data["identificatie"],
            bronorganisatie=validated_data["bronorganisatie"],
            creatiedatum=validated_data["creatiedatum"],
            titel=validated_data["titel"],
            auteur=validated_data["auteur"],
            taal=validated_data["taal"],
            begin_registratie=validated_data["begin_registratie"],
            informatieobjecttype=validated_data["informatieobjecttype"],
            vertrouwelijkheidaanduiding=validated_data.get(
                "vertrouwelijkheidaanduiding"
            ),
            status=validated_data.get("status"),
            formaat=validated_data.get("formaat"),
            bestandsnaam=validated_data.get("bestandsnaam"),
            link=validated_data.get("link"),
            beschrijving=validated_data.get("beschrijving"),
            ontvangstdatum=validated_data.get("ontvangstdatum"),
            verzenddatum=validated_data.get("verzenddatum"),
            verschijningsvorm=validated_data.get("verschijningsvorm"),
            bestandsomvang=validated_data.get("bestandsomvang"),
            inhoud=validated_data.get("inhoud", ""),
        )

        return Response(
            data={"task_id": save_document_task.id},
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        summary=_("Remove document from index."),
        description=_(
            "Remove the referenced document data from the index.\n"
            "This schedules a background task to perform the actual removal."
        ),
        responses={202: CeleryTaskIdSerializer},
        parameters=[
            OpenApiParameter(
                name="uuid",
                type=UUID,
                location=OpenApiParameter.PATH,
                description=_("UUID of the document to remove"),
            )
        ],
    )
    def destroy(self, request: Request, uuid: str, *args, **kwargs):
        result = remove_document_from_index.delay(uuid=uuid)
        return Response(data={"task_id": result.id}, status=status.HTTP_202_ACCEPTED)
