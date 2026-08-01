"""
HU-009 - Consultar el historial de auditoria | PRUEBAS UNITARIAS

Verifican en aislamiento las dos piezas que sostienen la trazabilidad del
sistema, sin recorrer la capa HTTP:

    logs.utils.registrar_log()   la funcion que toda operacion invoca
    logs.serializers            el contrato de datos del historial

Cobertura: RF-012, RN-007, RNF-006
"""

import pytest
from django.db import IntegrityError, transaction

from logs.models import LogEntry
from logs.serializers import LogEntrySerializer
from logs.utils import registrar_log

pytestmark = [pytest.mark.unit, pytest.mark.hu009]


# --------------------------------------------------------------------------- #
# registrar_log                                                                #
# --------------------------------------------------------------------------- #

class TestRegistrarLog:

    def test_crea_la_entrada_con_todos_los_campos(self, docente):
        registrar_log(docente.umg_id, 'CREAR_RESERVA', 'Reservas', 'Descripcion X')

        registro = LogEntry.objects.get()
        assert registro.umg_user_id == docente.umg_id
        assert registro.umg_accion == 'CREAR_RESERVA'
        assert registro.umg_modulo == 'Reservas'
        assert registro.umg_descripcion == 'Descripcion X'

    def test_sella_la_fecha_y_hora_automaticamente(self, docente):
        """RN-007: el momento lo pone el sistema, no quien invoca."""
        registrar_log(docente.umg_id, 'CREAR_RESERVA', 'Reservas', 'Descripcion')

        assert LogEntry.objects.get().umg_fecha_registro is not None

    def test_acepta_operaciones_sin_usuario_identificado(self, db):
        """
        El campo es nullable a proposito: hay acciones que hoy no tienen a quien
        atribuirse (ver DEF-007 y DEF-008). La funcion no debe reventar.
        """
        registrar_log(None, 'CANCELAR_RESERVA', 'Reservas', 'Sin responsable')

        assert LogEntry.objects.get().umg_user_id is None

    def test_no_devuelve_nada(self, docente):
        """
        Quien la invoca no recibe forma de saber si la auditoria funciono. Es
        consecuencia del diseno "nunca interrumpir" y explica por que un fallo
        de bitacora pasa inadvertido.
        """
        assert registrar_log(docente.umg_id, 'X', 'Y', 'Z') is None

    @pytest.mark.django_db(transaction=True)
    def test_en_autocommit_el_fallo_se_traga_y_se_pierde_el_registro(self):
        """
        Comportamiento actual en produccion: las vistas no abren transaccion
        explicita, asi que cada INSERT va en autocommit. Ahi el try/except si
        cumple su proposito.

        La contrapartida es que el registro se pierde sin dejar rastro ni senal
        para el operador. Para una historia cuyo proposito es "garantizar la
        trazabilidad", conviene tenerlo presente.
        """
        registrar_log(999999, 'CREAR_RESERVA', 'Reservas', 'Usuario inexistente')

        assert LogEntry.objects.count() == 0

    @pytest.mark.django_db(transaction=True)
    def test_dentro_de_una_transaccion_el_fallo_escapa_al_confirmar(self):
        """
        DEF-015: el docstring de registrar_log promete que "nunca lanza
        excepcion" y que "si falla el log, no debe interrumpir la operacion
        principal". Esa promesa no se sostiene dentro de una transaccion.

        Django crea las claves foraneas en PostgreSQL como DEFERRABLE INITIALLY
        DEFERRED, de modo que la violacion no se detecta en el INSERT sino en el
        COMMIT. Para entonces registrar_log ya retorno y su except no puede
        atrapar nada: la excepcion estalla fuera de la funcion y aborta toda la
        operacion, que es justo lo contrario de lo que buscaba proteger.

        Hoy es un problema latente porque ninguna vista usa transaction.atomic()
        ni ATOMIC_REQUESTS. Se vuelve real en cuanto alguien envuelva la
        creacion de una reserva en una transaccion, que es lo natural al querer
        hacerla atomica.
        """
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                registrar_log(999999, 'CREAR_RESERVA', 'Reservas', 'Usuario inexistente')

        assert LogEntry.objects.count() == 0

    @pytest.mark.parametrize(
        'accion',
        ['CREAR_RESERVA', 'CANCELAR_RESERVA', 'CREAR_USUARIO', 'LOGIN', 'LOGIN_FALLIDO'],
    )
    def test_registra_cualquier_accion_del_sistema(self, docente, accion):
        registrar_log(docente.umg_id, accion, 'Modulo', 'Descripcion')

        assert LogEntry.objects.get().umg_accion == accion


# --------------------------------------------------------------------------- #
# Contrato del historial                                                       #
# --------------------------------------------------------------------------- #

class TestContratoDelHistorial:

    def test_el_serializer_expone_los_campos_de_auditoria(self, docente):
        registrar_log(docente.umg_id, 'CREAR_RESERVA', 'Reservas', 'Descripcion')

        datos = LogEntrySerializer(LogEntry.objects.get()).data

        assert set(datos.keys()) == {
            'umg_id', 'umg_user', 'umg_accion', 'umg_modulo',
            'umg_descripcion', 'umg_fecha_registro',
        }

    def test_el_serializer_responde_a_las_cuatro_preguntas_de_una_auditoria(
        self, docente
    ):
        """Quien, que, donde y cuando."""
        registrar_log(docente.umg_id, 'CANCELAR_RESERVA', 'Reservas', 'Detalle')

        datos = LogEntrySerializer(LogEntry.objects.get()).data

        assert datos['umg_user'] == docente.umg_id      # quien
        assert datos['umg_accion'] == 'CANCELAR_RESERVA'  # que
        assert datos['umg_modulo'] == 'Reservas'        # donde
        assert datos['umg_fecha_registro'] is not None  # cuando

    def test_el_modelo_conserva_la_entrada_si_se_elimina_el_usuario(
        self, docente
    ):
        """
        RNF-006: la FK usa on_delete=SET_NULL. Borrar un usuario no debe
        arrastrarse sus registros de auditoria.
        """
        registrar_log(docente.umg_id, 'CREAR_RESERVA', 'Reservas', 'Descripcion')

        docente.delete()

        registro = LogEntry.objects.get()
        assert registro.umg_user_id is None
        assert registro.umg_accion == 'CREAR_RESERVA'
