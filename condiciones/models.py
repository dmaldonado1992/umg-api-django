from django.db import models
from labs.models import Lab

class Condicion(models.Model):
    umg_id = models.AutoField(primary_key=True, db_column='UMG_ID')
    umg_lab = models.ForeignKey(Lab, on_delete=models.RESTRICT, null=True, blank=True, db_column='UMG_Lab_ID')
    umg_fecha = models.DateField(db_column='UMG_Fecha')
    umg_hora_inicio = models.TimeField(db_column='UMG_Hora_Inicio')
    umg_hora_fin = models.TimeField(db_column='UMG_Hora_Fin')
    umg_tipo = models.CharField(max_length=30, db_column='UMG_Tipo')
    umg_motivo = models.CharField(max_length=150, db_column='UMG_Motivo')
    umg_estado = models.IntegerField(default=1, db_column='UMG_Estado')
    umg_fecha_registro = models.DateTimeField(auto_now_add=True, db_column='UMG_Fecha_Registro')

    class Meta:
        db_table = 'UMG_CONDI'

    def __str__(self):
        return f"{self.umg_tipo} - {self.umg_fecha}"