"""Schema automatico para las vistas basadas en funciones del proyecto."""

import inspect
import sys

from rest_framework import serializers
from drf_spectacular.openapi import AutoSchema


class DynamicAutoSchema(AutoSchema):
    """Reutiliza automaticamente el serializer del modulo de cada vista."""

    def _get_serializer(self):
        serializer = super()._get_serializer()
        if serializer is not None:
            return serializer

        module = inspect.getmodule(self.view.__class__)
        if module is None:
            return None

        candidates = [
            value
            for value in vars(sys.modules[module.__name__]).values()
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
