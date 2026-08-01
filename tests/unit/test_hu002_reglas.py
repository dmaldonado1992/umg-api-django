"""
HU-002 - Validacion automatica de disponibilidad | PRUEBAS UNITARIAS

Ejercitan en aislamiento las dos funciones que deciden si un laboratorio esta
libre, sin recorrer la capa HTTP:

    reservas.views.hay_traslape()   choque con reservas de otros docentes
    reservas.views.hay_bloqueo()    condiciones administrativas (UMG_CONDI)

Son las unicas reglas de negocio del proyecto extraidas como funciones
independientes de la vista, y por eso las unicas que admiten pruebas unitarias
verdaderas sobre la logica de reserva.

Cobertura: RF-002, RN-001, RN-004, RN-006
"""

from datetime import timedelta

import pytest

from condiciones.models import Condicion
from reservas.views import hay_bloqueo, hay_traslape

pytestmark = [pytest.mark.unit, pytest.mark.hu002]


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
