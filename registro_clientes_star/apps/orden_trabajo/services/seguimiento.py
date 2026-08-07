"""
Servicios relacionados con seguimientos
de órdenes de trabajo.

Este módulo centraliza:

- creación de seguimientos;
- actualización de comentarios;
- eliminación de seguimientos.

Todas las operaciones de escritura se ejecutan
dentro de transacciones atómicas.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.orden_trabajo.models import (
    OrdenTrabajo,
    OrdenTrabajoSeguimiento,
)

from apps.usuarios.models import Usuario


# ======================================================
# FUNCIONES PRIVADAS
# ======================================================

def _validar_orden(
    orden_trabajo: OrdenTrabajo | None,
) -> None:
    """
    Valida que la orden exista y esté guardada.
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
    Valida que el usuario exista y esté guardado.
    """

    if usuario is None:
        raise ValueError(
            "Debe proporcionar un usuario válido."
        )

    if not usuario.pk:
        raise ValueError(
            "El usuario debe estar guardado."
        )


def _validar_comentario(
    comentario: str,
) -> str:
    """
    Valida y normaliza el comentario del seguimiento.
    """

    comentario_normalizado = (
        comentario or ""
    ).strip()

    if not comentario_normalizado:
        raise ValidationError(
            {
                "comentario": _(
                    "Debe indicar un comentario."
                )
            }
        )

    return comentario_normalizado


def _bloquear_orden(
    orden_trabajo: OrdenTrabajo,
) -> OrdenTrabajo:
    """
    Recupera y bloquea la OT durante
    la transacción actual.
    """

    _validar_orden(
        orden_trabajo
    )

    return (
        OrdenTrabajo.objects
        .select_for_update()
        .get(
            pk=orden_trabajo.pk,
        )
    )


def _bloquear_seguimiento(
    seguimiento: OrdenTrabajoSeguimiento,
) -> OrdenTrabajoSeguimiento:
    """
    Recupera y bloquea un seguimiento existente.
    """

    if seguimiento is None:
        raise ValueError(
            "Debe proporcionar un seguimiento válido."
        )

    if not seguimiento.pk:
        raise ValueError(
            "El seguimiento debe estar guardado."
        )

    return (
        OrdenTrabajoSeguimiento.objects
        .select_for_update()
        .select_related(
            "orden_trabajo",
            "usuario",
        )
        .get(
            pk=seguimiento.pk,
        )
    )


# ======================================================
# CREAR SEGUIMIENTO
# ======================================================

@transaction.atomic
def crear_seguimiento_ot(
    *,
    orden_trabajo: OrdenTrabajo,
    usuario: Usuario,
    comentario: str,
) -> OrdenTrabajoSeguimiento:
    """
    Crea un seguimiento asociado a una orden
    de trabajo.

    Args:
        orden_trabajo:
            Orden sobre la cual se registra la novedad.

        usuario:
            Usuario que registra el seguimiento.

        comentario:
            Descripción de la novedad o avance.

    Returns:
        OrdenTrabajoSeguimiento:
            Seguimiento creado.
    """

    _validar_usuario(
        usuario
    )

    orden = _bloquear_orden(
        orden_trabajo
    )

    comentario_normalizado = (
        _validar_comentario(
            comentario
        )
    )

    seguimiento = OrdenTrabajoSeguimiento(
        orden_trabajo=orden,
        usuario=usuario,
        comentario=comentario_normalizado,
    )

    seguimiento.full_clean()

    seguimiento.save()

    return seguimiento


# ======================================================
# ACTUALIZAR SEGUIMIENTO
# ======================================================

@transaction.atomic
def actualizar_seguimiento_ot(
    *,
    seguimiento: OrdenTrabajoSeguimiento,
    comentario: str,
) -> OrdenTrabajoSeguimiento:
    """
    Actualiza el comentario de un seguimiento
    existente.

    El usuario autor del seguimiento no se modifica
    mediante este servicio.
    """

    seguimiento_bloqueado = (
        _bloquear_seguimiento(
            seguimiento
        )
    )

    _bloquear_orden(
        seguimiento_bloqueado.orden_trabajo
    )

    comentario_normalizado = (
        _validar_comentario(
            comentario
        )
    )

    seguimiento_bloqueado.comentario = (
        comentario_normalizado
    )

    seguimiento_bloqueado.full_clean()

    seguimiento_bloqueado.save(
        update_fields=(
            "comentario",
        ),
    )

    return seguimiento_bloqueado


# ======================================================
# ELIMINAR SEGUIMIENTO
# ======================================================

@transaction.atomic
def eliminar_seguimiento_ot(
    *,
    seguimiento: OrdenTrabajoSeguimiento,
) -> tuple[int, dict[str, int]]:
    """
    Elimina un seguimiento de una orden de trabajo.
    """

    seguimiento_bloqueado = (
        _bloquear_seguimiento(
            seguimiento
        )
    )

    _bloquear_orden(
        seguimiento_bloqueado.orden_trabajo
    )

    return seguimiento_bloqueado.delete()


__all__ = (
    "crear_seguimiento_ot",
    "actualizar_seguimiento_ot",
    "eliminar_seguimiento_ot",
)