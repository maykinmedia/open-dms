from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from rest_framework import serializers
from rest_framework.test import APIRequestFactory

from ...tests.factories import UserFactory
from ..serializers import AuthSerializer, UserSerializer, WhoAmISerializer

User = get_user_model()


class AuthSerializerTest(TestCase):
    def test_incorrect_login(self):
        request = APIRequestFactory().get("/")
        serializer = AuthSerializer(
            data={"username": "johndoe", "password": "incorrect"},
            context={"request": request},
        )

        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_correct_login(self):
        user = UserFactory.create(username="johndoe", password="s3cret")
        request = APIRequestFactory().get("/")
        serializer = AuthSerializer(
            data={"username": "johndoe", "password": "s3cret"},
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.validated_data["user"], user)


class UserSerializerTest(TestCase):
    def test_user_serialization(self):
        user = UserFactory.create()
        serializer = UserSerializer(user)
        data = serializer.data

        self.assertEqual(data["username"], user.username)
        self.assertEqual(data["email"], user.email)
        self.assertEqual(data["first_name"], user.first_name)
        self.assertEqual(data["last_name"], user.last_name)
        self.assertEqual(data["pk"], user.pk)


class WhoAmISerializerTest(TestCase):
    def test_anonymous_user_serialization(self):
        user = AnonymousUser()
        serializer = WhoAmISerializer(user)
        data = serializer.data

        self.assertFalse(data["is_authenticated"])
        self.assertIsNone(data["user"])

    def test_authenticated_user_serialization(self):
        user = UserFactory.build()
        serializer = WhoAmISerializer(user)
        data = serializer.data

        self.assertTrue(data["is_authenticated"])
        self.assertEqual(data["user"]["username"], user.username)
        self.assertEqual(data["user"]["email"], user.email)
        self.assertEqual(data["user"]["first_name"], user.first_name)
        self.assertEqual(data["user"]["last_name"], user.last_name)
        self.assertEqual(data["user"]["pk"], user.pk)
