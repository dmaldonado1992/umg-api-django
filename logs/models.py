from django.db import models
from usuarios.models import Usuario

class LogEntry(models.Model):
    umg_id = models.BigAutoField(primary_key=True, db_column='UMG_ID')
    umg_user = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, db_column='UMG_User_ID')
    umg_accion = models.CharField(max_length=50, db_column='UMG_Accion')
    umg_modulo = models.CharField(max_length=50, db_column='UMG_Modulo')
    umg_descripcion = models.TextField(db_column='UMG_Descripcion')
    umg_fecha_registro = models.DateTimeField(auto_now_add=True, db_column='UMG_Fecha_Registro')

    class Meta:
        db_table = 'UMG_LOG'

    def __str__(self):
        return f"{self.umg_accion} - {self.umg_fecha_registro}"