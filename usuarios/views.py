from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from .models import Usuario, Rol
from .serializers import UsuarioListSerializer
from logs.utils import registrar_log
import re

EMAIL_REGEX = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


@api_view(['GET', 'POST'])
def usuarios_list_create(request):
    if request.method == 'GET':
        usuarios = Usuario.objects.select_related('umg_rol').all().order_by('umg_nombre', 'umg_apellido')
        serializer = UsuarioListSerializer(usuarios, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        correo = request.data.get('UMG_Usuario', '').strip().lower()
        contrasena = request.data.get('UMG_Contrasena', '')
        nombre = request.data.get('UMG_Nombre', '').strip()
        apellido = request.data.get('UMG_Apellido', '').strip()
        rol_id = request.data.get('UMG_Rol_ID')

        if not correo or not EMAIL_REGEX.match(correo):
            return Response({'mensaje': 'El correo electronico no tiene un formato valido.'}, status=status.HTTP_400_BAD_REQUEST)

        if not contrasena or len(contrasena) < 6:
            return Response({'mensaje': 'La contrasena debe tener al menos 6 caracteres.'}, status=status.HTTP_400_BAD_REQUEST)

        if not nombre or not apellido:
            return Response({'mensaje': 'El nombre y apellido son obligatorios.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            rol = Rol.objects.get(pk=rol_id, umg_estado=1)
        except Rol.DoesNotExist:
            return Response({'mensaje': 'El rol especificado no existe o esta inactivo.'}, status=status.HTTP_400_BAD_REQUEST)

        if Usuario.objects.filter(umg_usuario=correo).exists():
            msg = "Ya existe un usuario registrado con el correo '{0}'.".format(correo)
            return Response({'mensaje': msg}, status=status.HTTP_409_CONFLICT)

        usuario = Usuario.objects.create(
            umg_usuario=correo,
            umg_contrasena=contrasena,
            umg_nombre=nombre,
            umg_apellido=apellido,
            umg_rol=rol
        )

        msg_log = "Se registro el usuario '{0}' con ID {1}.".format(usuario.umg_usuario, usuario.umg_id)
        registrar_log(None, "CREAR_USUARIO", "Usuarios", msg_log)

        return Response({
            'UMG_ID': usuario.umg_id,
            'UMG_Usuario': usuario.umg_usuario,
            'UMG_Nombre': usuario.umg_nombre,
            'UMG_Apellido': usuario.umg_apellido,
            'UMG_Rol_ID': rol.umg_id
        }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def login(request):
    correo = request.data.get('UMG_Usuario', '').strip().lower()
    contrasena = request.data.get('UMG_Contrasena', '')

    if not correo or not contrasena:
        return Response({'mensaje': 'Debe ingresar usuario y contrasena.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        usuario = Usuario.objects.select_related('umg_rol').get(
            umg_usuario=correo, umg_contrasena=contrasena, umg_estado=1
        )
    except Usuario.DoesNotExist:
        msg_log = "Intento de inicio de sesion fallido para el correo '{0}'.".format(correo)
        registrar_log(None, "LOGIN_FALLIDO", "Autenticacion", msg_log)
        return Response({'mensaje': 'Usuario o contrasena incorrectos.'}, status=status.HTTP_401_UNAUTHORIZED)

    usuario.umg_ultimo_acceso = timezone.now()
    usuario.save()

    msg_log = "El usuario '{0}' inicio sesion correctamente.".format(usuario.umg_usuario)
    registrar_log(usuario.umg_id, "LOGIN", "Autenticacion", msg_log)

    return Response({
        'UMG_ID': usuario.umg_id,
        'UMG_Usuario': usuario.umg_usuario,
        'UMG_Nombre': usuario.umg_nombre,
        'UMG_Apellido': usuario.umg_apellido,
        'UMG_Rol_ID': usuario.umg_rol.umg_id,
        'UMG_Rol_Nombre': usuario.umg_rol.umg_nombre,
        'RequiereCambioContrasena': usuario.umg_ingreso == 0
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def cambiar_contrasena(request):
    user_id = request.data.get('UMG_ID')
    nueva = request.data.get('NuevaContrasena', '')

    try:
        usuario = Usuario.objects.get(pk=user_id, umg_estado=1)
    except Usuario.DoesNotExist:
        return Response({'mensaje': 'El usuario especificado no existe o esta inactivo.'}, status=status.HTTP_400_BAD_REQUEST)

    if not nueva or len(nueva) < 6:
        return Response({'mensaje': 'La nueva contrasena debe tener al menos 6 caracteres.'}, status=status.HTTP_400_BAD_REQUEST)

    usuario.umg_contrasena = nueva
    usuario.umg_ingreso = 1
    usuario.umg_fecha_modifica_contrasena = timezone.now()
    usuario.umg_ultimo_acceso = timezone.now()
    usuario.save()

    msg_log = "El usuario con ID {0} actualizo su contrasena.".format(usuario.umg_id)
    registrar_log(usuario.umg_id, "CAMBIO_CONTRASENA", "Autenticacion", msg_log)

    return Response({'mensaje': 'Contrasena actualizada correctamente.'}, status=status.HTTP_200_OK)


@api_view(['PATCH'])
def inactivar_usuario(request, pk):
    try:
        usuario = Usuario.objects.get(pk=pk, umg_estado=1)
    except Usuario.DoesNotExist:
        return Response({'mensaje': 'El usuario no existe o ya se encuentra inactivo.'}, status=status.HTTP_400_BAD_REQUEST)

    usuario.umg_estado = 0
    usuario.save()

    msg_log = "El usuario con ID {0} fue inactivado por un administrador.".format(pk)
    registrar_log(None, "INACTIVAR_USUARIO", "Usuarios", msg_log)

    return Response({'mensaje': 'Usuario inactivado correctamente.'}, status=status.HTTP_200_OK)


@api_view(['PATCH'])
def resetear_contrasena(request, pk):
    try:
        usuario = Usuario.objects.get(pk=pk, umg_estado=1)
    except Usuario.DoesNotExist:
        return Response({'mensaje': 'El usuario no existe o esta inactivo.'}, status=status.HTTP_400_BAD_REQUEST)

    contrasena_temporal = request.data.get('ContrasenaTemporal', '')

    if not contrasena_temporal or len(contrasena_temporal) < 6:
        return Response({'mensaje': 'La contrasena temporal debe tener al menos 6 caracteres.'}, status=status.HTTP_400_BAD_REQUEST)

    usuario.umg_contrasena = contrasena_temporal
    usuario.umg_ingreso = 0
    usuario.umg_fecha_modifica_contrasena = timezone.now()
    usuario.save()

    msg_log = "Un administrador reseteo la contrasena del usuario con ID {0}.".format(pk)
    registrar_log(None, "RESET_CONTRASENA", "Usuarios", msg_log)

    return Response({'mensaje': 'Contrasena reseteada. El usuario debera cambiarla en su proximo ingreso.'}, status=status.HTTP_200_OK)