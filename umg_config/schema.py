"""Schema OpenAPI automatico para las vistas del proyecto."""

import inspect
import sys
from datetime import date, datetime, time

from drf_spectacular.openapi import AutoSchema
from rest_framework import serializers


class DynamicAutoSchema(AutoSchema):
    """Descubre serializers y genera ejemplos desde sus campos declarados."""

    def _module_serializer(self):
        module = inspect.getmodule(self.view.__class__)
        if module is None:
            return None

        candidates = [
            value for value in vars(sys.modules[module.__name__]).values()
            if inspect.isclass(value)
            and issubclass(value, serializers.BaseSerializer)
            and value is not serializers.BaseSerializer
        ]
        if len(candidates) == 1:
            return candidates[0]()

        preferred = [
            value for value in candidates
            if value.__name__.endswith(('ListSerializer', 'Serializer'))
        ]
        return preferred[0]() if len(preferred) == 1 else None

    def _get_serializer(self):
        serializer = self._module_serializer()
        return serializer if serializer is not None else super()._get_serializer()

    @staticmethod
    def _field_example(field):
        if isinstance(field, serializers.ChoiceField) and field.choices:
            return next(iter(field.choices))
        if isinstance(field, serializers.BooleanField):
            return True
        if isinstance(field, serializers.IntegerField):
            return 1
        if isinstance(field, serializers.FloatField):
            return 1.0
        if isinstance(field, serializers.DecimalField):
            return '10.00'
        if isinstance(field, serializers.DateTimeField):
            return datetime.now().isoformat()
        if isinstance(field, serializers.DateField):
            return date.today().isoformat()
        if isinstance(field, serializers.TimeField):
            return time(8, 0).isoformat()
        if isinstance(field, serializers.ListField):
            return []
        return 'string'

    def _request_example(self, serializer):
        if serializer is None:
            return None
        example = {
            name: self._field_example(field)
            for name, field in serializer.fields.items()
            if not field.read_only
        }
        return example or None

    def get_operation(self, path, path_regex, path_prefix, method, registry):
        operation = super().get_operation(
            path, path_regex, path_prefix, method, registry
        )
        request_body = operation.get('requestBody') if operation else None
        if not request_body:
            return operation

        example = self._request_example(self._get_serializer())
        if example is None:
            return operation

        for media in request_body.get('content', {}).values():
            media.setdefault('examples', {})['auto-generated'] = {
                'summary': 'Ejemplo generado automáticamente',
                'value': example,
            }
        return operation