from rest_framework import serializers
from zgw_consumers.models import Service


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = (
            "slug",
            "label",
        )


class ValidationErrorsSerializer(serializers.Serializer):
    non_field_errors = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    field_errors = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()), required=False
    )
