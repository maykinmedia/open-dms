from rest_framework import serializers


class NonFieldErrorsSerializer(serializers.Serializer):
    nonFieldErrors = serializers.ListField(child=serializers.CharField())
