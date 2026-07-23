from rest_framework import serializers
from .models import Usuario, Rol


class UsuarioListSerializer(serializers.ModelSerializer):
    UMG_ID = serializers.IntegerField(source='umg_id', read_only=True)
    UMG_Usuario = serializers.CharField(source='umg_usuario', read_only=True)
    UMG_Nombre = serializers.CharField(source='umg_nombre', read_only=True)
    UMG_Apellido = serializers.CharField(source='umg_apellido', read_only=True)
    UMG_Rol_ID = serializers.IntegerField(source='umg_rol.umg_id', read_only=True)
    UMG_Rol_Nombre = serializers.CharField(source='umg_rol.umg_nombre', read_only=True)
    UMG_Estado = serializers.IntegerField(source='umg_estado', read_only=True)
    UMG_Ingreso = serializers.IntegerField(source='umg_ingreso', read_only=True)
    UMG_Fecha_Creacion = serializers.DateTimeField(source='umg_fecha_creacion', read_only=True)
    UMG_Ultimo_Acceso = serializers.DateTimeField(source='umg_ultimo_acceso', read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'UMG_ID', 'UMG_Usuario', 'UMG_Nombre', 'UMG_Apellido',
            'UMG_Rol_ID', 'UMG_Rol_Nombre', 'UMG_Estado', 'UMG_Ingreso',
            'UMG_Fecha_Creacion', 'UMG_Ultimo_Acceso'
        ]