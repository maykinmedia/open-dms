from rest_framework import serializers


class ValidationErrorsSerializer(serializers.Serializer):
    non_field_errors = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    field_errors = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()), required=False
    )
