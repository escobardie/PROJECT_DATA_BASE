"""
Servicios relacionados con técnicos asignados
a órdenes de trabajo.

Este módulo centraliza:

- asignación de técnicos;
- actualización de asignaciones;
- definición del técnico principal;
- eliminación de técnicos de una OT.

Todas las operaciones de escritura se ejecutan
dentro de transacciones atómicas.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.orden_trabajo.models import (
    OrdenTrabajo,
    OrdenTrabajoTecnico,
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


def _validar_tecnico(
    tecnico: Usuario | None,
) -> None:
    """
    Valida que el técnico exista y esté guardado.
    """

    if tecnico is None:
        raise ValueError(
            "Debe proporcionar un técnico válido."
        )

    if not tecnico.pk:
        raise ValueError(
            "El técnico debe estar guardado."
        )


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


def _bloquear_asignacion(
    asignacion: OrdenTrabajoTecnico,
) -> OrdenTrabajoTecnico:
    """
    Recupera y bloquea una asignación existente.
    """

    if asignacion is None:
        raise ValueError(
            "Debe proporcionar una asignación válida."
        )

    if not asignacion.pk:
        raise ValueError(
            "La asignación debe estar guardada."
        )

    return (
        OrdenTrabajoTecnico.objects
        .select_for_update()
        .select_related(
            "orden_trabajo",
            "tecnico",
        )
        .get(
            pk=asignacion.pk,
        )
    )


def _desmarcar_principal_actual(
    *,
    orden_trabajo: OrdenTrabajo,
    excluir_pk: int | None = None,
) -> None:
    """
    Desmarca cualquier técnico principal actual
    de la orden.

    Puede excluir una asignación concreta.
    """

    queryset = (
        OrdenTrabajoTecnico.objects
        .filter(
            orden_trabajo=orden_trabajo,
            es_principal=True,
        )
    )

    if excluir_pk is not None:
        queryset = queryset.exclude(
            pk=excluir_pk,
        )

    queryset.update(
        es_principal=False,
    )


# ======================================================
# ASIGNAR TÉCNICO
# ======================================================

@transaction.atomic
def asignar_tecnico_ot(
    *,
    orden_trabajo: OrdenTrabajo,
    tecnico: Usuario,
    es_principal: bool = False,
    observaciones: str = "",
) -> OrdenTrabajoTecnico:
    """
    Asigna un técnico a una orden de trabajo.

    Si ``es_principal=True``, cualquier técnico principal
    anterior deja de serlo automáticamente.

    Returns:
        OrdenTrabajoTecnico:
            Asignación creada.

    Raises:
        ValidationError:
            Cuando el técnico ya está asignado.
    """

    _validar_tecnico(
        tecnico
    )

    orden = _bloquear_orden(
        orden_trabajo
    )

    existe = (
        OrdenTrabajoTecnico.objects
        .filter(
            orden_trabajo=orden,
            tecnico=tecnico,
        )
        .exists()
    )

    if existe:
        raise ValidationError(
            {
                "tecnico": _(
                    "El técnico ya está asignado "
                    "a esta orden de trabajo."
                )
            }
        )

    if es_principal:
        _desmarcar_principal_actual(
            orden_trabajo=orden,
        )

    asignacion = OrdenTrabajoTecnico(
        orden_trabajo=orden,
        tecnico=tecnico,
        es_principal=es_principal,
        observaciones=observaciones,
    )

    asignacion.full_clean()

    asignacion.save()

    return asignacion


# ======================================================
# ACTUALIZAR ASIGNACIÓN
# ======================================================

@transaction.atomic
def actualizar_tecnico_ot(
    *,
    asignacion: OrdenTrabajoTecnico,
    es_principal: bool | None = None,
    observaciones: str | None = None,
) -> OrdenTrabajoTecnico:
    """
    Actualiza una asignación técnica existente.

    Args:
        asignacion:
            Asignación a modificar.

        es_principal:
            Nuevo estado principal.
            Si es None, no se modifica.

        observaciones:
            Nuevas observaciones.
            Si es None, no se modifican.

    Returns:
        OrdenTrabajoTecnico:
            Asignación actualizada.
    """

    asignacion_bloqueada = (
        _bloquear_asignacion(
            asignacion
        )
    )

    orden = _bloquear_orden(
        asignacion_bloqueada.orden_trabajo
    )

    campos_actualizados = []

    if es_principal is not None:
        if es_principal:
            _desmarcar_principal_actual(
                orden_trabajo=orden,
                excluir_pk=asignacion_bloqueada.pk,
            )

        asignacion_bloqueada.es_principal = (
            es_principal
        )

        campos_actualizados.append(
            "es_principal"
        )

    if observaciones is not None:
        asignacion_bloqueada.observaciones = (
            observaciones
        )

        campos_actualizados.append(
            "observaciones"
        )

    if not campos_actualizados:
        return asignacion_bloqueada

    asignacion_bloqueada.full_clean()

    asignacion_bloqueada.save(
        update_fields=tuple(
            campos_actualizados
        ),
    )

    return asignacion_bloqueada


# ======================================================
# MARCAR COMO PRINCIPAL
# ======================================================

@transaction.atomic
def marcar_tecnico_principal(
    *,
    asignacion: OrdenTrabajoTecnico,
) -> OrdenTrabajoTecnico:
    """
    Marca una asignación como técnico principal.

    Cualquier técnico principal anterior
    deja automáticamente de serlo.
    """

    asignacion_bloqueada = (
        _bloquear_asignacion(
            asignacion
        )
    )

    orden = _bloquear_orden(
        asignacion_bloqueada.orden_trabajo
    )

    _desmarcar_principal_actual(
        orden_trabajo=orden,
        excluir_pk=asignacion_bloqueada.pk,
    )

    if asignacion_bloqueada.es_principal:
        return asignacion_bloqueada

    asignacion_bloqueada.es_principal = True

    asignacion_bloqueada.full_clean()

    asignacion_bloqueada.save(
        update_fields=(
            "es_principal",
        ),
    )

    return asignacion_bloqueada


# ======================================================
# QUITAR TÉCNICO
# ======================================================

@transaction.atomic
def quitar_tecnico_ot(
    *,
    asignacion: OrdenTrabajoTecnico,
) -> tuple[int, dict[str, int]]:
    """
    Elimina una asignación técnica de la OT.

    Returns:
        tuple:
            Resultado estándar de Django al eliminar.
    """

    asignacion_bloqueada = (
        _bloquear_asignacion(
            asignacion
        )
    )

    _bloquear_orden(
        asignacion_bloqueada.orden_trabajo
    )

    return asignacion_bloqueada.delete()


__all__ = (
    "asignar_tecnico_ot",
    "actualizar_tecnico_ot",
    "marcar_tecnico_principal",
    "quitar_tecnico_ot",
)