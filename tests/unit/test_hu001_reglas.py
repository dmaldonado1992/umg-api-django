"""
HU-001 - Registrar una nueva reserva | PRUEBAS UNITARIAS

Verifican de forma aislada el contrato de datos de una reserva recien creada y
la regla de formato del correo institucional, sin recorrer la capa HTTP.

Las reglas de disponibilidad que HU-001 invoca al crear (hay_traslape y
hay_bloqueo) se prueban en test_hu002_reglas.py, que es la historia dueña de
esa logica.

Cobertura:
  RN-008  identificador unico
  RN-009  formato del correo
  RN-010  estado inicial 'R' (Reservada)
"""

import pytest

from reservas.models import Reserva
from reservas.serializers import ReservaListSerializer
from usuarios.views import EMAIL_REGEX

pytestmark = [pytest.mark.unit, pytest.mark.hu001]


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


# --------------------------------------------------------------------------- #
# Formato del correo institucional (RN-009)                                    #
# --------------------------------------------------------------------------- #

class TestFormatoDelCorreoInstitucional:
    """
    HU-001 escenario 3 exige rechazar correos con formato invalido. Como se
    documenta en test_hu001_crear_reserva.py, el endpoint de reservas no recibe
    el correo: lo deriva de UMG_User_ID. La validacion vive entonces en el alta
    de usuarios, concentrada en la constante EMAIL_REGEX.

    Estas pruebas la ejercitan en aislamiento, que es donde la regla realmente
    se puede verificar.
    """

    @pytest.mark.parametrize(
        'correo',
        [
            'jperez@umg.edu.gt',
            'juan.perez@umg.edu.gt',
            'j.perez-lopez@miumg.edu.gt',
            'a@b.co',
        ],
    )
    def test_acepta_correos_bien_formados(self, correo):
        assert EMAIL_REGEX.match(correo) is not None, (
            f'Rechazo un correo valido: {correo}'
        )

    @pytest.mark.parametrize(
        'correo, caso',
        [
            ('sin-arroba.umg.edu.gt', 'no tiene arroba'),
            ('@umg.edu.gt', 'no tiene parte local'),
            ('jperez@', 'no tiene dominio'),
            ('jperez@umg', 'el dominio no tiene punto'),
            ('jperez@@umg.edu.gt', 'doble arroba'),
            ('juan perez@umg.edu.gt', 'espacio en la parte local'),
            ('jperez@umg edu.gt', 'espacio en el dominio'),
            ('', 'cadena vacia'),
        ],
    )
    def test_rechaza_correos_mal_formados(self, correo, caso):
        assert EMAIL_REGEX.match(correo) is None, (
            f'Acepto un correo invalido: {caso}'
        )

    @pytest.mark.xfail(
        strict=True,
        reason=(
            'DEF-014: la historia habla de "correo institucional", pero '
            'EMAIL_REGEX solo comprueba la forma generica de un correo. '
            'Cualquier dominio externo pasa la validacion, de modo que se puede '
            'dar de alta un docente con una cuenta personal.'
        ),
    )
    @pytest.mark.parametrize(
        'correo', ['jperez@gmail.com', 'jperez@hotmail.com', 'jperez@ejemplo.org']
    )
    def test_rechaza_correos_de_dominios_no_institucionales(self, correo):
        assert EMAIL_REGEX.match(correo) is None
