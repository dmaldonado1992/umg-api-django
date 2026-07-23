from .models import LogEntry


def registrar_log(user_id, accion, modulo, descripcion):
    """
    Registra una entrada de auditoría. Nunca lanza excepción:
    si falla el log, no debe interrumpir la operación principal.
    """
    try:
        LogEntry.objects.create(
            umg_user_id=user_id,
            umg_accion=accion,
            umg_modulo=modulo,
            umg_descripcion=descripcion
        )
    except Exception:
        pass