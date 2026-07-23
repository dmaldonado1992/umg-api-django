from rest_framework import serializers
from .models import LogEntry


class LogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEntry
        fields = ['umg_id', 'umg_user', 'umg_accion', 'umg_modulo', 'umg_descripcion', 'umg_fecha_registro']