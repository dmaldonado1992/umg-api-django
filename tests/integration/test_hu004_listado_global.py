"""
HU-004 - Visualizar el listado global de reservas | PRUEBAS DE INTEGRACION

    "Como administrador, quiero visualizar el listado completo de reservas
     registradas, para mantener el control global del uso de los laboratorios y
     facilitar la auditoria administrativa."

Endpoint bajo prueba: GET /api/reservas/
"""

from datetime import timedelta

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.hu004, pytest.mark.django_db]


# --------------------------------------------------------------------------- #
# Escenario 1 - Listado completo de reservas                                   #
# --------------------------------------------------------------------------- #

class TestEscenario1ListadoCompleto:
    """
    Dado    que existen reservas registradas en el sistema
    Cuando  el administrador consulta el listado general (GET /reservas)
    Entonces el sistema retorna todas las reservas con sus datos y estados, con
            HTTP 200.

    Verifica: RF-009
    """

    def test_responde_http_200(self, api, url_reservas, docente, lab,
                               fecha_futura, crear_reserva):
        crear_reserva(docente, lab, fecha_futura, '08:00', '10:00')

        respuesta = api.get(url_reservas)

        assert respuesta.status_code == 200

    def test_retorna_todas_las_reservas_registradas(
        self, api, url_reservas, docente, otro_docente, lab, otro_lab,
        fecha_futura, crear_reserva
    ):
        crear_reserva(docente, lab, fecha_futura, '08:00', '10:00')
        crear_reserva(otro_docente, otro_lab, fecha_futura, '10:00', '12:00')
        crear_reserva(docente, lab, fecha_futura + timedelta(days=1), '14:00', '16:00')

        respuesta = api.get(url_reservas)

        assert len(respuesta.data) == 3

    def test_incluye_las_canceladas_y_no_solo_las_activas(
        self, api, url_reservas, docente, lab, otro_lab, fecha_futura, crear_reserva
    ):
        """
        El control global y la auditoria requieren ver el historial completo,
        no unicamente lo vigente.
        """
        crear_reserva(docente, lab, fecha_futura, '08:00', '10:00', estado='R')
        crear_reserva(docente, otro_lab, fecha_futura, '08:00', '10:00', estado='C')

        respuesta = api.get(url_reservas)

        estados = sorted(r['UMG_Estado'] for r in respuesta.data)
        assert estados == ['C', 'R']

    def test_cada_reserva_trae_el_contrato_completo_de_datos(
        self, api, url_reservas, docente, lab, fecha_futura, crear_reserva
    ):
        crear_reserva(docente, lab, fecha_futura, '08:00', '10:00')

        item = api.get(url_reservas).data[0]

        assert set(item.keys()) == {
            'UMG_ID', 'UMG_User_ID', 'UMG_Docente_Nombre', 'UMG_Docente_Correo',
            'UMG_Lab_ID', 'UMG_Lab_Nombre', 'UMG_Fecha_Reserva', 'UMG_Hora_Inicio',
            'UMG_Hora_Fin', 'UMG_Motivo', 'UMG_Estado', 'UMG_Fecha_Registro',
        }

    def test_resuelve_el_nombre_del_docente_y_del_laboratorio(
        self, api, url_reservas, docente, lab, fecha_futura, crear_reserva
    ):
        """
        Para el administrador, ver identificadores numericos no sirve: el
        listado debe traer los nombres ya resueltos.
        """
        crear_reserva(docente, lab, fecha_futura, '08:00', '10:00')

        item = api.get(url_reservas).data[0]

        assert item['UMG_Docente_Nombre'] == 'Juan Perez'
        assert item['UMG_Docente_Correo'] == 'jperez@umg.edu.gt'
        assert item['UMG_Lab_Nombre'] == 'Lab Redes 1'

    def test_ordena_por_fecha_descendente_y_hora_ascendente(
        self, api, url_reservas, docente, lab, fecha_futura, crear_reserva
    ):
        """Lo mas reciente primero, y dentro del dia en orden cronologico."""
        manana = fecha_futura + timedelta(days=1)
        crear_reserva(docente, lab, fecha_futura, '08:00', '10:00')
        crear_reserva(docente, lab, manana, '14:00', '16:00')
        crear_reserva(docente, lab, manana, '08:00', '10:00')

        datos = api.get(url_reservas).data

        assert [(r['UMG_Fecha_Reserva'], r['UMG_Hora_Inicio']) for r in datos] == [
            (manana.isoformat(), '08:00:00'),
            (manana.isoformat(), '14:00:00'),
            (fecha_futura.isoformat(), '08:00:00'),
        ]

    def test_no_incurre_en_consultas_n_mas_1(
        self, api, url_reservas, django_assert_max_num_queries, docente,
        otro_docente, lab, otro_lab, fecha_futura, crear_reserva
    ):
        """
        La vista usa select_related sobre usuario y laboratorio. Sin el, cada
        reserva dispararia dos consultas extra y el listado se degradaria a
        medida que crece la tabla.
        """
        for i in range(10):
            crear_reserva(
                docente if i % 2 else otro_docente,
                lab if i % 2 else otro_lab,
                fecha_futura + timedelta(days=i),
                '08:00', '10:00',
            )

        with django_assert_max_num_queries(3):
            api.get(url_reservas)


# --------------------------------------------------------------------------- #
# Escenario 2 - Listado sin reservas registradas                               #
# --------------------------------------------------------------------------- #

class TestEscenario2ListadoVacio:
    """
    Dado    que no existe ninguna reserva registrada
    Cuando  el administrador consulta el listado general
    Entonces el sistema responde con HTTP 200 y una lista vacia.

    Verifica: RF-009
    """

    def test_responde_200_con_lista_vacia(self, api, url_reservas, db):
        respuesta = api.get(url_reservas)

        assert respuesta.status_code == 200
        assert respuesta.data == []

    def test_no_lo_trata_como_un_error(self, api, url_reservas, db):
        """Una agenda vacia es un estado valido, no un 404 ni un 204."""
        respuesta = api.get(url_reservas)

        assert respuesta.status_code == 200
        assert isinstance(respuesta.data, list)
