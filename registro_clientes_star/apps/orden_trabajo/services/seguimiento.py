"""
Servicios para registrar seguimientos
de órdenes de trabajo.

Un seguimiento representa un evento histórico.

Una vez registrado:

- no se modifica;
- no se elimina desde el flujo funcional;
- una corrección genera un nuevo seguimiento.
"""

from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.choices import EstadoOrdenTrabajoChoices

from apps.orden_trabajo.models import (
    OrdenTrabajo,
    OrdenTrabajoSeguimiento,
)

from apps.usuarios.models import Usuario


# ======================================================
# VALIDACIONES GENERALES
# ======================================================

def _validar_orden_guardada(
    orden_trabajo: OrdenTrabajo | None,
) -> None:
    """
    Valida una OT persistida.
    """

    if orden_trabajo is None:
        raise ValueError(
            "Debe proporcionar una orden de trabajo válida."
        )

    if not orden_trabajo.pk:
        raise ValueError(
            "La orden de trabajo debe estar guardada."
        )


def _validar_usuario(
    usuario: Usuario | None,
) -> None:
    """
    Valida el usuario que registra el seguimiento.
    """

    if usuario is None:
        raise ValueError(
            "Debe proporcionar el usuario que "
            "registra el seguimiento."
        )

    if not usuario.pk:
        raise ValueError(
            "El usuario debe estar guardado."
        )


def _bloquear_orden(
    orden_trabajo: OrdenTrabajo,
) -> OrdenTrabajo:
    """
    Recupera y bloquea la OT durante
    el registro del seguimiento.
    """

    _validar_orden_guardada(
        orden_trabajo
    )

    return (
        OrdenTrabajo.objects
        .select_for_update()
        .get(
            pk=orden_trabajo.pk,
        )
    )


def _resolver_fecha_hora(
    *,
    fecha_nueva: datetime | None,
) -> datetime:
    """
    Un seguimiento es siempre un registro nuevo.

    Prioridad:

    1. fecha proporcionada;
    2. fecha/hora actual.
    """

    return (
        fecha_nueva
        or timezone.now()
    )


# ======================================================
# REGISTRAR SEGUIMIENTO
# ======================================================

@transaction.atomic
def registrar_seguimiento_ot(
    *,
    orden_trabajo: OrdenTrabajo,
    usuario: Usuario,
    comentario: str,
    fecha: datetime | None = None,
) -> OrdenTrabajoSeguimiento:
    """
    Registra una nueva actualización
    dentro del historial de la OT.

    fecha_seguimiento:
        cuándo ocurrió el evento.

    usuario:
        quién registró formalmente el evento.

    created_at:
        cuándo fue almacenado técnicamente
        en la base de datos.
    """

    _validar_usuario(
        usuario
    )

    orden = _bloquear_orden(
        orden_trabajo
    )

    # ==================================================
    # OT CERRADA
    # ==================================================

    if orden.estado in {
        EstadoOrdenTrabajoChoices.FINALIZADA,
        EstadoOrdenTrabajoChoices.CANCELADA,
    }:
        raise ValidationError(
            {
                "orden_trabajo": _(
                    "No pueden agregarse seguimientos "
                    "operativos a una orden finalizada "
                    "o cancelada."
                )
            }
        )

    # ==================================================
    # COMENTARIO
    # ==================================================

    comentario_limpio = (
        comentario
        or ""
    ).strip()

    if not comentario_limpio:
        raise ValidationError(
            {
                "comentario": _(
                    "Debe indicar una novedad, avance "
                    "o comentario."
                )
            }
        )

    # ==================================================
    # FECHA
    # ==================================================

    fecha_seguimiento = (
        _resolver_fecha_hora(
            fecha_nueva=fecha,
        )
    )

    # ==================================================
    # CREAR REGISTRO HISTÓRICO
    # ==================================================

    seguimiento = OrdenTrabajoSeguimiento(
        orden_trabajo=orden,
        usuario=usuario,
        fecha_seguimiento=fecha_seguimiento,
        comentario=comentario_limpio,
    )

    seguimiento.full_clean()
    seguimiento.save()

    return seguimiento


# ======================================================
# EXPORTACIONES
# ======================================================

__all__ = (
    "registrar_seguimiento_ot",
)