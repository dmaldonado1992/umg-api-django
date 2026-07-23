from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import datetime, date
from .models import Condicion
from .serializers import CondicionListSerializer
from labs.models import Lab
from logs.utils import registrar_log

TIPOS_VALIDOS = ['Asueto', 'Mantenimiento', 'Actividad']


def validar_datos_condicion(lab_id, fecha_str, hora_inicio, hora_fin, tipo, motivo):
    try:
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None, {'mensaje': 'La fecha proporcionada no es válida.'}

    if fecha_obj < date.today():
        return None, {'mensaje': 'No se puede registrar un bloqueo para una fecha pasada.'}

    if hora_inicio >= hora_fin:
        return None, {'mensaje': 'La hora de inicio debe ser menor a la hora de fin.'}

    if not tipo or tipo not in TIPOS_VALIDOS:
        return None, {'mensaje': f"El tipo debe ser uno de los siguientes valores: {', '.join(TIPOS_VALIDOS)}."}

    if not motivo or not motivo.strip():
        return None, {'mensaje': 'El motivo del bloqueo es obligatorio.'}

    lab = None
    if lab_id:
        try:
            lab = Lab.objects.get(pk=lab_id, umg_estado=1)
        except Lab.DoesNotExist:
            return None, {'mensaje': 'El laboratorio especificado no existe o está inactivo.'}

    return {
        'lab': lab,
        'fecha': fecha_obj,
        'hora_inicio': hora_inicio,
        'hora_fin': hora_fin,
        'tipo': tipo,
        'motivo': motivo.strip()
    }, None


@api_view(['GET', 'POST'])
def condiciones_list_create(request):
    if request.method == 'GET':
        condiciones = Condicion.objects.select_related('umg_lab').all().order_by('-umg_fecha', 'umg_hora_inicio')
        serializer = CondicionListSerializer(condiciones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        lab_id = request.data.get('UMG_Lab_ID')
        fecha_str = request.data.get('UMG_Fecha')
        hora_inicio = request.data.get('UMG_Hora_Inicio')
        hora_fin = request.data.get('UMG_Hora_Fin')
        tipo = request.data.get('UMG_Tipo')
        motivo = request.data.get('UMG_Motivo', '')

        datos, error = validar_datos_condicion(lab_id, fecha_str, hora_inicio, hora_fin, tipo, motivo)
        if error:
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        condicion = Condicion.objects.create(
            umg_lab=datos['lab'],
            umg_fecha=datos['fecha'],
            umg_hora_inicio=datos['hora_inicio'],
            umg_hora_fin=datos['hora_fin'],
            umg_tipo=datos['tipo'],
            umg_motivo=datos['motivo']
        )

        registrar_log(
            None,
            "CREAR_CONDICION",
            "Condiciones",
            f"Se registró un bloqueo tipo '{condicion.umg_tipo}' para el {condicion.umg_fecha}."
        )

        serializer = CondicionListSerializer(condicion)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PUT'])
def condiciones_update(request, pk):
    try:
        condicion = Condicion.objects.get(pk=pk)
    except Condicion.DoesNotExist:
        return Response({'mensaje': 'El bloqueo especificado no existe.'}, status=status.HTTP_404_NOT_FOUND)

    lab_id = request.data.get('UMG_Lab_ID')
    fecha_str = request.data.get('UMG_Fecha')
    hora_inicio = request.data.get('UMG_Hora_Inicio')
    hora_fin = request.data.get('UMG_Hora_Fin')
    tipo = request.data.get('UMG_Tipo')
    motivo = request.data.get('UMG_Motivo', '')
    estado = request.data.get('UMG_Estado')

    datos, error = validar_datos_condicion(lab_id, fecha_str, hora_inicio, hora_fin, tipo, motivo)
    if error:
        return Response(error, status=status.HTTP_400_BAD_REQUEST)

    condicion.umg_lab = datos['lab']
    condicion.umg_fecha = datos['fecha']
    condicion.umg_hora_inicio = datos['hora_inicio']
    condicion.umg_hora_fin = datos['hora_fin']
    condicion.umg_tipo = datos['tipo']
    condicion.umg_motivo = datos['motivo']
    if estado is not None:
        condicion.umg_estado = estado
    condicion.save()

    registrar_log(
        None,
        "EDITAR_CONDICION",
        "Condiciones",
        f"Se actualizó el bloqueo con ID {pk}."
    )

    return Response({'mensaje': 'Bloqueo actualizado correctamente.'}, status=status.HTTP_200_OK)