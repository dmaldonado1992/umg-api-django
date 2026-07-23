from django.db import models

class Lab(models.Model):
    umg_id = models.AutoField(primary_key=True, db_column='UMG_ID')
    umg_nombre = models.CharField(max_length=30, unique=True, db_column='UMG_Nombre')
    umg_estado = models.IntegerField(default=1, db_column='UMG_Estado')
    umg_reserva = models.CharField(max_length=1, default='D', db_column='UMG_Reserva')
    umg_fecha_registro = models.DateTimeField(auto_now_add=True, db_column='UMG_Fecha_Registro')

    class Meta:
        db_table = 'UMG_LABS'

    def __str__(self):
        return self.umg_nombre