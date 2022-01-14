import json
import logging
import typing

from django.conf import settings
from django.http import HttpRequest
from rest_framework import permissions

from .models import AbstractAPIKey, APIKey


class KeyParser:

    def get(self, request: HttpRequest) -> typing.Optional[str]:
        return self.get_from_body(request)

    def get_from_body(self, request: HttpRequest) -> typing.Optional[str]:
        body = request.body.decode('utf-8')
        body_data = json.loads(body)
        if 'api_key' in body_data:
            return body_data.get('api_key') if body_data.get('api_key') else None
        else:
            return None


class BaseHasAPIKey(permissions.BasePermission):
    model: typing.Optional[typing.Type[AbstractAPIKey]] = None
    key_parser = KeyParser()

    def get_key(self, request: HttpRequest) -> typing.Optional[str]:
        return self.key_parser.get(request)

    def has_permission(self, request: HttpRequest, view: typing.Any) -> bool:
        assert self.model is not None, (
            "%s must define `.model` with the API key model to use"
            % self.__class__.__name__
        )
        key = self.get_key(request)
        if not key:
            return False
        return self.model.objects.is_valid(key)

    def has_object_permission(
        self, request: HttpRequest, view: typing.Any, obj: AbstractAPIKey
    ) -> bool:
        return self.has_permission(request, view)


class HasAPIKey(BaseHasAPIKey):
    model = APIKey
