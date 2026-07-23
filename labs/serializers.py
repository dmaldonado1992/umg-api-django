from rest_framework import serializers
from .models import Lab


class LabSerializer(serializers.ModelSerializer):
    UMG_ID = serializers.IntegerField(source='umg_id', read_only=True)
    UMG_Nombre = serializers.CharField(source='umg_nombre')
    UMG_Estado = serializers.IntegerField(source='umg_estado')
    UMG_Reserva = serializers.CharField(source='umg_reserva', read_only=True)
    UMG_Fecha_Registro = serializers.DateTimeField(source='umg_fecha_registro', read_only=True)

    class Meta:
        model = Lab
        fields = ['UMG_ID', 'UMG_Nombre', 'UMG_Estado', 'UMG_Reserva', 'UMG_Fecha_Registro']