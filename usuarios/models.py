from django.db import models

class Rol(models.Model):
    umg_id = models.AutoField(primary_key=True, db_column='UMG_ID')
    umg_nombre = models.CharField(max_length=30, unique=True, db_column='UMG_Nombre')
    umg_descripcion = models.CharField(max_length=150, null=True, blank=True, db_column='UMG_Descripcion')
    umg_estado = models.IntegerField(default=1, db_column='UMG_Estado')
    umg_fecha_registro = models.DateTimeField(auto_now_add=True, db_column='UMG_Fecha_Registro')

    class Meta:
        db_table = 'UMG_ROLES'

    def __str__(self):
        return self.umg_nombre


class Usuario(models.Model):
    umg_id = models.AutoField(primary_key=True, db_column='UMG_ID')
    umg_usuario = models.CharField(max_length=100, unique=True, db_column='UMG_Usuario')  # correo
    umg_contrasena = models.CharField(max_length=255, db_column='UMG_Contrasena')
    umg_nombre = models.CharField(max_length=50, db_column='UMG_Nombre')
    umg_apellido = models.CharField(max_length=50, db_column='UMG_Apellido')
    umg_rol = models.ForeignKey(Rol, on_delete=models.RESTRICT, db_column='UMG_Rol_ID')
    umg_estado = models.IntegerField(default=1, db_column='UMG_Estado')
    umg_ingreso = models.IntegerField(default=0, db_column='UMG_Ingreso')
    umg_fecha_creacion = models.DateTimeField(auto_now_add=True, db_column='UMG_Fecha_Creacion')
    umg_fecha_modifica_contrasena = models.DateTimeField(null=True, blank=True, db_column='UMG_Fecha_Modifica_Contrasena')
    umg_ultimo_acceso = models.DateTimeField(null=True, blank=True, db_column='UMG_Ultimo_Acceso')

    class Meta:
        db_table = 'UMG_USERS'

    def __str__(self):
        return self.umg_usuario