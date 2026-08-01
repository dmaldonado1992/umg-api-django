"""
HU-005 - Consultar una reserva por su identificador | PRUEBAS DE INTEGRACION

    "Como docente o administrador, quiero consultar el detalle de una reserva
     especifica mediante su identificador unico, para verificar su informacion y
     su estado actual."

Endpoint bajo prueba: GET /api/reservas/{id}/
"""

import pytest
from django.urls import reverse

pytestmark = [pytest.mark.integration, pytest.mark.hu005, pytest.mark.django_db]


def url_detalle(pk):
    return reverse('reservas-detalle', args=[pk])


# --------------------------------------------------------------------------- #
# Escenario 1 - Consulta por identificador existente                           #
# --------------------------------------------------------------------------- #

class TestEscenario1IdentificadorExistente:
    """
    Dado    que existe una reserva con el identificador consultado
    Cuando  el usuario solicita el detalle de esa reserva
    Entonces el sistema retorna la informacion completa de la reserva con
            HTTP 200.

    Verifica: RF-010, RN-008
    """

    def test_responde_http_200(self, api, docente, lab, fecha_futura, crear_reserva):
        reserva = crear_reserva(docente, lab, fecha_futura, '08:00', '10:00')

        respuesta = api.get(url_detalle(reserva.umg_id))

        assert respuesta.status_code == 200

    def test_retorna_la_informacion_completa(
        self, api, docente, lab, fecha_futura, crear_reserva
    ):
        reserva = crear_reserva(
            docente, lab, fecha_futura, '08:00', '10:00', motivo='Laboratorio de redes'
        )

        datos = api.get(url_detalle(reserva.umg_id)).data

        assert datos['UMG_ID'] == reserva.umg_id
        assert datos['UMG_User_ID'] == docente.umg_id
        assert datos['UMG_Docente_Nombre'] == 'Juan Perez'
        assert datos['UMG_Docente_Correo'] == 'jperez@umg.edu.gt'
        assert datos['UMG_Lab_ID'] == lab.umg_id
        assert datos['UMG_Lab_Nombre'] == 'Lab Redes 1'
        assert datos['UMG_Fecha_Reserva'] == fecha_futura.isoformat()
        assert datos['UMG_Hora_Inicio'] == '08:00:00'
        assert datos['UMG_Hora_Fin'] == '10:00:00'
        assert datos['UMG_Motivo'] == 'Laboratorio de redes'

    def test_refleja_el_estado_actual_de_la_reserva(
        self, api, docente, lab, fecha_futura, crear_reserva
    ):
        """El proposito de la historia es "verificar su estado actual"."""
        activa = crear_reserva(docente, lab, fecha_futura, '08:00', '10:00', estado='R')
        cancelada = crear_reserva(docente, lab, fecha_futura, '14:00', '16:00', estado='C')

        assert api.get(url_detalle(activa.umg_id)).data['UMG_Estado'] == 'R'
        assert api.get(url_detalle(cancelada.umg_id)).data['UMG_Estado'] == 'C'

    def test_el_identificador_devuelto_coincide_con_el_solicitado(
        self, api, docente, lab, otro_lab, fecha_futura, crear_reserva
    ):
        """RN-008: cada identificador apunta siempre a la misma reserva."""
        primera = crear_reserva(docente, lab, fecha_futura, '08:00', '10:00')
        segunda = crear_reserva(docente, otro_lab, fecha_futura, '08:00', '10:00')

        assert api.get(url_detalle(primera.umg_id)).data['UMG_ID'] == primera.umg_id
        assert api.get(url_detalle(segunda.umg_id)).data['UMG_ID'] == segunda.umg_id


# --------------------------------------------------------------------------- #
# Escenario 2 - Consulta por identificador inexistente                         #
# --------------------------------------------------------------------------- #

class TestEscenario2IdentificadorInexistente:
    """
    Dado    que no existe ninguna reserva con el identificador consultado
    Cuando  el usuario solicita el detalle de esa reserva
    Entonces el sistema responde con HTTP 404 y un mensaje de error semantico,
            sin exponer detalles internos.

    Verifica: RNF-005
    """

    def test_responde_http_404(self, api, db):
        respuesta = api.get(url_detalle(999999))

        assert respuesta.status_code == 404

    def test_el_mensaje_es_semantico(self, api, db):
        respuesta = api.get(url_detalle(999999))

        assert 'mensaje' in respuesta.data
        assert 'no existe' in respuesta.data['mensaje'].lower()

    def test_no_expone_detalles_internos(self, api, db):
        """
        RNF-005: el cliente no debe recibir trazas, nombres de tabla, SQL ni la
        excepcion de Django.
        """
        cuerpo = api.get(url_detalle(999999)).content.decode().lower()

        for filtracion in ['traceback', 'doesnotexist', 'umg_reserv', 'select ', 'django.db']:
            assert filtracion not in cuerpo, f"La respuesta filtra '{filtracion}'"

    def test_consultar_una_reserva_eliminada_tambien_devuelve_404(
        self, api, docente, lab, fecha_futura, crear_reserva
    ):
        reserva = crear_reserva(docente, lab, fecha_futura, '08:00', '10:00')
        reserva_id = reserva.umg_id
        reserva.delete()

        respuesta = api.get(url_detalle(reserva_id))

        assert respuesta.status_code == 404

    def test_un_identificador_no_numerico_no_resuelve(self, api, db):
        """
        La ruta declara <int:pk>, asi que un identificador con letras ni
        siquiera llega a la vista.
        """
        respuesta = api.get('/api/reservas/abc/')

        assert respuesta.status_code == 404
