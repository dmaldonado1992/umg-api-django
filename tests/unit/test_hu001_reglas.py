"""
HU-001 - Registrar una nueva reserva | PRUEBAS UNITARIAS

Verifican de forma aislada las reglas de negocio y el contrato de datos en los
que se apoya el endpoint POST /api/reservas/, sin recorrer la capa HTTP.

Cobertura:
  RN-001/RN-004  deteccion de traslape de horarios
  RN-006         una reserva cancelada libera el espacio
  RN-008         identificador unico
  RN-010         estado inicial 'R' (Reservada)
"""

from datetime import timedelta

import pytest

from reservas.models import Reserva
from reservas.serializers import ReservaListSerializer
from reservas.views import hay_bloqueo, hay_traslape
from condiciones.models import Condicion

pytestmark = [pytest.mark.unit, pytest.mark.hu001]


# --------------------------------------------------------------------------- #
# Deteccion de traslape                                                        #
# --------------------------------------------------------------------------- #

class TestDeteccionDeTraslape:
    """
    Sobre una reserva existente de 08:00 a 10:00 en estado 'R', comprueba que
    hay_traslape() clasifique correctamente cada posicion relativa del bloque
    solicitado.
    """

    @pytest.mark.parametrize(
        'inicio, fin, esperado, caso',
        [
            ('08:00', '10:00', True,  'bloque identico'),
            ('09:00', '11:00', True,  'traslape sobre el final'),
            ('07:00', '09:00', True,  'traslape sobre el inicio'),
            ('08:30', '09:30', True,  'contenido dentro del existente'),
            ('07:00', '11:00', True,  'contiene al existente'),
            ('10:00', '12:00', False, 'adyacente posterior, sin traslape'),
            ('06:00', '08:00', False, 'adyacente anterior, sin traslape'),
            ('14:00', '16:00', False, 'completamente separado'),
        ],
    )
    def test_clasifica_correctamente_cada_posicion(
        self, docente, lab, fecha_futura, crear_reserva, inicio, fin, esperado, caso
    ):
        crear_reserva(docente, lab, fecha_futura, '08:00', '10:00')

        resultado = hay_traslape(lab.umg_id, fecha_futura, inicio, fin)

        assert resultado is esperado, f'Fallo el caso: {caso}'

    def test_una_reserva_cancelada_no_bloquea_el_horario(
        self, docente, lab, fecha_futura, crear_reserva
    ):
        """RN-006: el estado 'C' libera el espacio inmediatamente."""
        crear_reserva(docente, lab, fecha_futura, '08:00', '10:00', estado='C')

        assert hay_traslape(lab.umg_id, fecha_futura, '08:00', '10:00') is False

    def test_el_traslape_se_evalua_por_laboratorio(
        self, docente, lab, otro_lab, fecha_futura, crear_reserva
    ):
        crear_reserva(docente, lab, fecha_futura, '08:00', '10:00')

        assert hay_traslape(otro_lab.umg_id, fecha_futura, '08:00', '10:00') is False

    def test_el_traslape_se_evalua_por_fecha(
        self, docente, lab, fecha_futura, crear_reserva
    ):
        crear_reserva(docente, lab, fecha_futura, '08:00', '10:00')
        otro_dia = fecha_futura + timedelta(days=1)

        assert hay_traslape(lab.umg_id, otro_dia, '08:00', '10:00') is False

    def test_excluir_id_permite_reevaluar_la_propia_reserva(
        self, docente, lab, fecha_futura, crear_reserva
    ):
        """Necesario para HU-007: al modificar, la reserva no debe chocar consigo misma."""
        reserva = crear_reserva(docente, lab, fecha_futura, '08:00', '10:00')

        assert hay_traslape(lab.umg_id, fecha_futura, '08:00', '10:00') is True
        assert hay_traslape(
            lab.umg_id, fecha_futura, '08:00', '10:00', excluir_id=reserva.umg_id
        ) is False


# --------------------------------------------------------------------------- #
# Bloqueos administrativos                                                     #
# --------------------------------------------------------------------------- #

class TestDeteccionDeBloqueo:

    def test_un_bloqueo_del_laboratorio_impide_la_reserva(self, lab, fecha_futura):
        Condicion.objects.create(
            umg_lab=lab,
            umg_fecha=fecha_futura,
            umg_hora_inicio='08:00',
            umg_hora_fin='12:00',
            umg_tipo='MANTENIMIENTO',
            umg_motivo='Cambio de equipo de red',
            umg_estado=1,
        )

        assert hay_bloqueo(lab.umg_id, fecha_futura, '09:00', '11:00') is True

    def test_un_bloqueo_global_aplica_a_todos_los_laboratorios(
        self, lab, otro_lab, fecha_futura
    ):
        """Una condicion sin laboratorio asociado (umg_lab NULL) es institucional."""
        Condicion.objects.create(
            umg_lab=None,
            umg_fecha=fecha_futura,
            umg_hora_inicio='07:00',
            umg_hora_fin='22:00',
            umg_tipo='ASUETO',
            umg_motivo='Feriado nacional',
            umg_estado=1,
        )

        assert hay_bloqueo(lab.umg_id, fecha_futura, '08:00', '10:00') is True
        assert hay_bloqueo(otro_lab.umg_id, fecha_futura, '08:00', '10:00') is True

    def test_un_bloqueo_inactivo_se_ignora(self, lab, fecha_futura):
        Condicion.objects.create(
            umg_lab=lab,
            umg_fecha=fecha_futura,
            umg_hora_inicio='08:00',
            umg_hora_fin='12:00',
            umg_tipo='MANTENIMIENTO',
            umg_motivo='Bloqueo dado de baja',
            umg_estado=0,
        )

        assert hay_bloqueo(lab.umg_id, fecha_futura, '09:00', '11:00') is False


# --------------------------------------------------------------------------- #
# Contrato del modelo y del serializer                                         #
# --------------------------------------------------------------------------- #

class TestContratoDeLaReserva:

    def test_el_estado_inicial_por_defecto_es_reservada(
        self, docente, lab, fecha_futura
    ):
        """RN-010: toda reserva nueva nace en estado 'R'."""
        reserva = Reserva.objects.create(
            umg_user=docente,
            umg_lab=lab,
            umg_fecha_reserva=fecha_futura,
            umg_hora_inicio='08:00',
            umg_hora_fin='10:00',
            umg_motivo='Practica de laboratorio',
        )

        assert reserva.umg_estado == 'R'

    def test_cada_reserva_recibe_un_identificador_unico(
        self, docente, lab, otro_lab, fecha_futura, crear_reserva
    ):
        """RN-008: el identificador es unico y lo asigna el sistema."""
        primera = crear_reserva(docente, lab, fecha_futura, '08:00', '10:00')
        segunda = crear_reserva(docente, otro_lab, fecha_futura, '08:00', '10:00')

        assert primera.umg_id is not None
        assert segunda.umg_id is not None
        assert primera.umg_id != segunda.umg_id

    def test_el_serializer_expone_los_campos_del_contrato(
        self, docente, lab, fecha_futura, crear_reserva
    ):
        reserva = crear_reserva(docente, lab, fecha_futura, '08:00', '10:00')

        datos = ReservaListSerializer(reserva).data

        assert set(datos.keys()) == {
            'UMG_ID', 'UMG_User_ID', 'UMG_Docente_Nombre', 'UMG_Docente_Correo',
            'UMG_Lab_ID', 'UMG_Lab_Nombre', 'UMG_Fecha_Reserva', 'UMG_Hora_Inicio',
            'UMG_Hora_Fin', 'UMG_Motivo', 'UMG_Estado', 'UMG_Fecha_Registro',
        }

    def test_el_serializer_resuelve_nombre_y_correo_del_docente(
        self, docente, lab, fecha_futura, crear_reserva
    ):
        reserva = crear_reserva(docente, lab, fecha_futura, '08:00', '10:00')

        datos = ReservaListSerializer(reserva).data

        assert datos['UMG_Docente_Nombre'] == 'Juan Perez'
        assert datos['UMG_Docente_Correo'] == 'jperez@umg.edu.gt'
        assert datos['UMG_Lab_Nombre'] == 'Lab Redes 1'
