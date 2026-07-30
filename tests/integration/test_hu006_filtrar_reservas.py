"""
HU-006 - Filtrar reservas por criterios | PRUEBAS DE INTEGRACION

    "Como administrador, quiero filtrar las reservas por laboratorio, fecha o
     docente, para localizar rapidamente la informacion que necesito."

Endpoint bajo prueba: GET /api/reservas/?labId=&fecha=&userId=

Los tres criterios de la historia se mapean a los parametros de consulta que
acepta la vista:

    laboratorio  ->  labId
    fecha        ->  fecha
    docente      ->  userId
"""

from datetime import timedelta

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.hu006, pytest.mark.django_db]


@pytest.fixture
def agenda(docente, otro_docente, lab, otro_lab, fecha_futura, crear_reserva):
    """
    Escenario base con cuatro reservas que se distinguen entre si por cada uno
    de los tres criterios de filtrado.
    """
    manana = fecha_futura + timedelta(days=1)
    return {
        'manana': manana,
        'a': crear_reserva(docente, lab, fecha_futura, '08:00', '10:00'),
        'b': crear_reserva(docente, otro_lab, fecha_futura, '10:00', '12:00'),
        'c': crear_reserva(otro_docente, lab, manana, '08:00', '10:00'),
        'd': crear_reserva(otro_docente, otro_lab, manana, '14:00', '16:00'),
    }


# --------------------------------------------------------------------------- #
# Escenario 1 - Filtro con coincidencias                                       #
# --------------------------------------------------------------------------- #

class TestEscenario1FiltroConCoincidencias:
    """
    Dado    que existen reservas que cumplen con el criterio de filtro
            (laboratorio, fecha o docente)
    Cuando  el administrador aplica el filtro en la consulta
    Entonces el sistema retorna unicamente las reservas que cumplen el criterio,
            con HTTP 200.

    Verifica: RF-011
    """

    def test_filtra_por_laboratorio(self, api, url_reservas, agenda, lab):
        respuesta = api.get(url_reservas, {'labId': lab.umg_id})

        assert respuesta.status_code == 200
        assert len(respuesta.data) == 2
        assert all(r['UMG_Lab_ID'] == lab.umg_id for r in respuesta.data)

    def test_filtra_por_fecha(self, api, url_reservas, agenda, fecha_futura):
        respuesta = api.get(url_reservas, {'fecha': fecha_futura.isoformat()})

        assert respuesta.status_code == 200
        assert len(respuesta.data) == 2
        assert all(
            r['UMG_Fecha_Reserva'] == fecha_futura.isoformat() for r in respuesta.data
        )

    def test_filtra_por_docente(self, api, url_reservas, agenda, docente):
        respuesta = api.get(url_reservas, {'userId': docente.umg_id})

        assert respuesta.status_code == 200
        assert len(respuesta.data) == 2
        assert all(r['UMG_User_ID'] == docente.umg_id for r in respuesta.data)

    def test_los_filtros_se_combinan_entre_si(
        self, api, url_reservas, agenda, docente, lab, fecha_futura
    ):
        """
        Localizar rapidamente implica poder acotar por varios criterios a la
        vez, no solo por uno.
        """
        respuesta = api.get(
            url_reservas,
            {
                'labId': lab.umg_id,
                'fecha': fecha_futura.isoformat(),
                'userId': docente.umg_id,
            },
        )

        assert respuesta.status_code == 200
        assert len(respuesta.data) == 1
        assert respuesta.data[0]['UMG_ID'] == agenda['a'].umg_id

    def test_sin_filtros_devuelve_todo(self, api, url_reservas, agenda):
        """Omitir los parametros equivale al listado global de HU-004."""
        respuesta = api.get(url_reservas)

        assert len(respuesta.data) == 4

    def test_el_filtro_incluye_reservas_canceladas(
        self, api, url_reservas, docente, lab, fecha_futura, crear_reserva
    ):
        """
        La busqueda administrativa es para auditar; ocultar las canceladas
        escondería justamente lo que se quiere revisar.
        """
        crear_reserva(docente, lab, fecha_futura, '08:00', '10:00', estado='R')
        crear_reserva(docente, lab, fecha_futura, '14:00', '16:00', estado='C')

        respuesta = api.get(url_reservas, {'labId': lab.umg_id})

        assert len(respuesta.data) == 2


# --------------------------------------------------------------------------- #
# Escenario 2 - Filtro sin coincidencias                                       #
# --------------------------------------------------------------------------- #

class TestEscenario2FiltroSinCoincidencias:
    """
    Dado    que ninguna reserva cumple con el criterio de filtro aplicado
    Cuando  el administrador ejecuta la consulta
    Entonces el sistema responde con HTTP 200 y una lista vacia.

    Verifica: RF-011
    """

    def test_laboratorio_sin_reservas_devuelve_lista_vacia(
        self, api, url_reservas, agenda, lab_inactivo
    ):
        respuesta = api.get(url_reservas, {'labId': lab_inactivo.umg_id})

        assert respuesta.status_code == 200
        assert respuesta.data == []

    def test_fecha_sin_reservas_devuelve_lista_vacia(
        self, api, url_reservas, agenda, fecha_futura
    ):
        respuesta = api.get(
            url_reservas,
            {'fecha': (fecha_futura + timedelta(days=90)).isoformat()},
        )

        assert respuesta.status_code == 200
        assert respuesta.data == []

    def test_docente_sin_reservas_devuelve_lista_vacia(
        self, api, url_reservas, agenda, docente_inactivo
    ):
        respuesta = api.get(url_reservas, {'userId': docente_inactivo.umg_id})

        assert respuesta.status_code == 200
        assert respuesta.data == []

    def test_combinacion_imposible_devuelve_lista_vacia(
        self, api, url_reservas, agenda, docente, otro_lab
    ):
        """
        Cada criterio por separado tiene coincidencias, pero juntos no: se
        confirma que los filtros se aplican en conjuncion (AND) y no en
        disyuncion (OR).
        """
        respuesta = api.get(
            url_reservas,
            {'userId': docente.umg_id, 'fecha': agenda['manana'].isoformat()},
        )

        assert respuesta.status_code == 200
        assert respuesta.data == []

    def test_no_lo_trata_como_un_error(self, api, url_reservas, agenda):
        """No encontrar coincidencias es un resultado valido, no un 404."""
        respuesta = api.get(url_reservas, {'labId': 999999})

        assert respuesta.status_code == 200
        assert respuesta.data == []
