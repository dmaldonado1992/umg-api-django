"""Schema OpenAPI automatico para las vistas del proyecto."""

import ast
import inspect
import sys
import textwrap
from datetime import date, datetime, time

from drf_spectacular.openapi import AutoSchema
from rest_framework import serializers


class DynamicAutoSchema(AutoSchema):
    """Descubre serializers y ejemplos de entrada sin repetir JSON."""

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

    def _view_source(self, method):
        handler = getattr(self.view, method.lower(), None)
        for cell in getattr(handler, '__closure__', ()):
            if inspect.isfunction(cell.cell_contents):
                return textwrap.dedent(inspect.getsource(cell.cell_contents))
        return ''

    @staticmethod
    def _request_keys(source):
        tree = ast.parse(source)
        keys = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                target = node.func.value
                if node.func.attr == 'get' and isinstance(target, ast.Attribute):
                    if isinstance(target.value, ast.Name) and target.value.id == 'request' and target.attr == 'data':
                        if node.args and isinstance(node.args[0], ast.Constant):
                            keys.append(node.args[0].value)
            if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute):
                if isinstance(node.value.value, ast.Name) and node.value.value.id == 'request' and node.value.attr == 'data':
                    key = node.slice.value if isinstance(node.slice, ast.Constant) else None
                    if key:
                        keys.append(key)
        return list(dict.fromkeys(keys))

    @staticmethod
    def _value_for(key):
        name = key.lower()
        if 'fecha' in name:
            return date.today().isoformat()
        if 'hora' in name:
            return time(8, 0).isoformat()
        if 'id' in name or 'estado' in name:
            return 1
        if 'correo' in name or 'usuario' in name:
            return 'ejemplo@umg.edu.gt'
        if 'contrasena' in name:
            return 'Cambiar123'
        return 'string'

    def _request_example(self, method):
        keys = self._request_keys(self._view_source(method))
        if keys:
            return {key: self._value_for(key) for key in keys}

        serializer = self._get_serializer()
        if serializer is None:
            return None
        example = {
            name: self._value_for(name)
            for name, field in serializer.fields.items()
            if not field.read_only
        }
        return example or None

    def get_operation(self, path, path_regex, path_prefix, method, registry):
        operation = super().get_operation(
            path, path_regex, path_prefix, method, registry
        )
        if method not in {'POST', 'PUT'} or not operation:
            return operation
        request_body = operation.get('requestBody')
        if not request_body:
            return operation

        example = self._request_example(method)
        if example is None:
            return operation
        for media in request_body.get('content', {}).values():
            media.setdefault('examples', {})['auto-generated'] = {
                'summary': 'Estructura base generada automáticamente',
                'value': example,
            }
        return operation