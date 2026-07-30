"""
HU-003 - Consultar disponibilidad de laboratorios | PRUEBAS UNITARIAS

El endpoint de disponibilidad no existe (DEF-004), asi que no hay logica de
seleccion que aislar. Lo que si se puede verificar en aislamiento es el contrato
de datos con el que un laboratorio viaja en las respuestas: es la forma que
tendria cada elemento de la lista de "laboratorios libres", y la que hoy consume
el rodeo documentado en test_hu003_consultar_disponibilidad.py.

Cobertura: RF-003 (contrato de datos)
"""

import pytest

from labs.serializers import LabSerializer

pytestmark = [pytest.mark.unit, pytest.mark.hu003]


class TestContratoDeLaboratorio:

    def test_expone_los_campos_del_contrato(self, lab):
        datos = LabSerializer(lab).data

        assert set(datos.keys()) == {
            'UMG_ID', 'UMG_Nombre', 'UMG_Estado', 'UMG_Reserva', 'UMG_Fecha_Registro',
        }

    def test_traduce_los_nombres_internos_a_los_del_contrato(self, lab):
        """El modelo usa minusculas; la API expone la convencion UMG_PascalCase."""
        datos = LabSerializer(lab).data

        assert datos['UMG_ID'] == lab.umg_id
        assert datos['UMG_Nombre'] == 'Lab Redes 1'

    def test_un_laboratorio_nace_activo_y_disponible(self, lab):
        """Valores por defecto del modelo: estado 1 y reserva 'D'."""
        datos = LabSerializer(lab).data

        assert datos['UMG_Estado'] == 1
        assert datos['UMG_Reserva'] == 'D'

    def test_distingue_los_laboratorios_inactivos(self, lab_inactivo):
        """
        HU-001 rechaza reservar sobre un laboratorio inactivo, asi que el estado
        tiene que viajar en la respuesta para que el cliente pueda descartarlos
        al calcular la disponibilidad.
        """
        datos = LabSerializer(lab_inactivo).data

        assert datos['UMG_Estado'] == 0

    def test_el_contrato_no_dice_nada_sobre_ocupacion(self, lab):
        """
        Evidencia del hueco de HU-003 a nivel de datos: el laboratorio no
        expone ningun campo que indique si esta libre en una fecha y horario.
        UMG_Reserva es un atributo fijo del catalogo, no una respuesta a la
        consulta del docente.
        """
        datos = LabSerializer(lab).data

        assert not any(
            clave.lower().startswith(('umg_disponible', 'umg_libre'))
            for clave in datos
        )
