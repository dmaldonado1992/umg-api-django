from django.db import models
from usuarios.models import Usuario
from labs.models import Lab

class Reserva(models.Model):
    umg_id = models.AutoField(primary_key=True, db_column='UMG_ID')
    umg_user = models.ForeignKey(Usuario, on_delete=models.RESTRICT, db_column='UMG_User_ID')
    umg_lab = models.ForeignKey(Lab, on_delete=models.RESTRICT, db_column='UMG_Lab_ID')
    umg_fecha_reserva = models.DateField(db_column='UMG_Fecha_Reserva')
    umg_hora_inicio = models.TimeField(db_column='UMG_Hora_Inicio')
    umg_hora_fin = models.TimeField(db_column='UMG_Hora_Fin')
    umg_motivo = models.CharField(max_length=150, db_column='UMG_Motivo')
    umg_estado = models.CharField(max_length=1, default='R', db_column='UMG_Estado')  # R = Reservada, C = Cancelada
    umg_fecha_registro = models.DateTimeField(auto_now_add=True, db_column='UMG_Fecha_Registro')

    class Meta:
        db_table = 'UMG_RESERV'

    def __str__(self):
        return f"{self.umg_lab} - {self.umg_fecha_reserva} ({self.umg_hora_inicio}-{self.umg_hora_fin})"