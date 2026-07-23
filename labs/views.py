from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Lab
from .serializers import LabSerializer
from logs.utils import registrar_log


@api_view(['GET', 'POST'])
def labs_list_create(request):
    if request.method == 'GET':
        labs = Lab.objects.all().order_by('umg_nombre')
        serializer = LabSerializer(labs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        nombre = request.data.get('UMG_Nombre', '').strip()

        if not nombre:
            return Response({'mensaje': 'El nombre del laboratorio es obligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

        if len(nombre) > 30:
            return Response({'mensaje': 'El nombre no puede superar los 30 caracteres.'}, status=status.HTTP_400_BAD_REQUEST)

        if Lab.objects.filter(umg_nombre=nombre).exists():
            return Response({'mensaje': f"Ya existe un laboratorio con el nombre '{nombre}'."}, status=status.HTTP_409_CONFLICT)

        lab = Lab.objects.create(umg_nombre=nombre)

        registrar_log(
            None,
            "CREAR_LABORATORIO",
            "Laboratorios",
            f"Se registró el laboratorio '{lab.umg_nombre}' con ID {lab.umg_id}."
        )

        serializer = LabSerializer(lab)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PUT'])
def labs_update(request, pk):
    try:
        lab = Lab.objects.get(pk=pk)
    except Lab.DoesNotExist:
        return Response({'mensaje': 'El laboratorio especificado no existe.'}, status=status.HTTP_404_NOT_FOUND)

    nombre = request.data.get('UMG_Nombre', '').strip()
    estado = request.data.get('UMG_Estado')

    if not nombre:
        return Response({'mensaje': 'El nombre del laboratorio es obligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

    if Lab.objects.filter(umg_nombre=nombre).exclude(pk=pk).exists():
        return Response({'mensaje': f"Ya existe otro laboratorio con el nombre '{nombre}'."}, status=status.HTTP_409_CONFLICT)

    lab.umg_nombre = nombre
    if estado is not None:
        lab.umg_estado = estado
    lab.save()

    registrar_log(
        None,
        "EDITAR_LABORATORIO",
        "Laboratorios",
        f"Se actualizó el laboratorio con ID {pk}."
    )

    return Response({'mensaje': 'Laboratorio actualizado correctamente.'}, status=status.HTTP_200_OK)