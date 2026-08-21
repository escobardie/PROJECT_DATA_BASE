"""
Servicios para gestionar los técnicos
asignados a una orden de trabajo.

Centraliza:

- asignación;
- reactivación;
- definición del técnico principal;
- desasignación.

Los cambios no deben realizarse directamente
desde el Django Admin.
"""

from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.choices import EstadoOrdenTrabajoChoices
from apps.usuarios.services.roles import es_tecnico

from apps.orden_trabajo.models import (
    OrdenTrabajo,
    OrdenTrabajoTecnico,
)

from apps.usuarios.models import Usuario


# ======================================================
# VALIDACIONES GENERALES
# ======================================================

def _validar_orden_guardada(
    orden_trabajo: OrdenTrabajo | None,
) -> None:
    """
    Valida que exista una OT persistida.
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
    Valida un usuario persistido y activo.
    """

    if usuario is None:
        raise ValueError(
            "Debe proporcionar un usuario válido."
        )

    if not usuario.pk:
        raise ValueError(
            "El usuario debe estar guardado."
        )

    if not usuario.is_active:
        raise ValidationError(
            {
                "usuario": _(
                    "El usuario se encuentra inactivo."
                )
            }
        )


def _bloquear_orden(
    orden_trabajo: OrdenTrabajo,
) -> OrdenTrabajo:
    """
    Bloquea la OT durante la operación.
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
    fecha_existente: datetime | None = None,
) -> datetime:
    """
    Prioridad:

    1. fecha proporcionada;
    2. fecha previamente cargada;
    3. fecha/hora actual.
    """

    return (
        fecha_nueva
        or fecha_existente
        or timezone.now()
    )


# ======================================================
# VALIDACIÓN DE MODIFICACIÓN DEL EQUIPO
# ======================================================

def _validar_equipo_modificable(
    orden_trabajo: OrdenTrabajo,
) -> None:
    """
    Valida que el equipo técnico todavía
    pueda modificarse.

    Reglas:

    - una OT finalizada no modifica técnicos;
    - una OT cancelada no modifica técnicos;
    - una vez generada la Instalación, el equipo de
      la OT queda congelado.

    La Instalación ya posee su propia copia
    de InstalacionTecnico.
    """

    if orden_trabajo.estado in {
        EstadoOrdenTrabajoChoices.FINALIZADA,
        EstadoOrdenTrabajoChoices.CANCELADA,
    }:
        raise ValidationError(
            {
                "orden_trabajo": _(
                    "No pueden modificarse los técnicos "
                    "de una orden finalizada o cancelada."
                )
            }
        )

    if orden_trabajo.tiene_instalacion:
        raise ValidationError(
            {
                "orden_trabajo": _(
                    "La orden ya generó una instalación. "
                    "El equipo técnico de la OT quedó cerrado. "
                    "Los cambios posteriores deben realizarse "
                    "sobre los técnicos de la instalación."
                )
            }
        )


# ======================================================
# ASIGNAR TÉCNICO
# ======================================================

@transaction.atomic
def asignar_tecnico_ot(
    *,
    orden_trabajo: OrdenTrabajo,
    tecnico: Usuario,
    usuario: Usuario,
    es_principal: bool = False,
    observaciones: str = "",
    fecha: datetime | None = None,
) -> OrdenTrabajoTecnico:
    """
    Asigna formalmente un técnico a una OT.

    Si existe una asignación histórica inactiva para
    la misma OT y técnico, reactiva ese registro.

    fecha_asignacion:

        fecha indicada
            ↓
        timezone.now()

    usuario_asignacion:

        usuario que ejecuta la operación.
    """

    _validar_usuario(
        tecnico
    )

    _validar_usuario(
        usuario
    )
    # ==================================================
    # VALIDAR ROL TÉCNICO
    # ==================================================

    if not es_tecnico(
        tecnico
    ):
        raise ValidationError(
            {
                "tecnico": _(
                    "El usuario seleccionado no posee "
                    "el rol de técnico."
                )
            }
        )

    orden = _bloquear_orden(
        orden_trabajo
    )

    _validar_equipo_modificable(
        orden
    )

    # ==================================================
    # BLOQUEAR ASIGNACIONES DE LA OT
    # ==================================================

    asignaciones = (
        OrdenTrabajoTecnico.objects
        .select_for_update()
        .filter(
            orden_trabajo=orden,
        )
    )

    # ==================================================
    # VALIDAR PRINCIPAL
    # ==================================================

    if es_principal:
        existe_principal = (
            asignaciones
            .filter(
                es_principal=True,
                is_active=True,
            )
            .exists()
        )

        if existe_principal:
            raise ValidationError(
                {
                    "es_principal": _(
                        "La orden ya tiene un técnico "
                        "principal activo. Utilice la operación "
                        "Cambiar técnico principal."
                    )
                }
            )

    # ==================================================
    # BUSCAR ASIGNACIÓN PREEXISTENTE
    # ==================================================

    asignacion = (
        asignaciones
        .filter(
            tecnico=tecnico,
        )
        .first()
    )

    # ==================================================
    # YA ESTÁ ACTIVO
    # ==================================================

    if (
        asignacion
        and asignacion.is_active
    ):
        raise ValidationError(
            {
                "tecnico": _(
                    "El técnico ya se encuentra asignado "
                    "a esta orden de trabajo."
                )
            }
        )

    fecha_asignacion = (
        _resolver_fecha_hora(
            fecha_nueva=fecha,
        )
    )

    observaciones_limpias = (
        observaciones
        or ""
    ).strip()

    # ==================================================
    # REACTIVACIÓN
    # ==================================================

    if asignacion:
        asignacion.is_active = True

        asignacion.es_principal = (
            es_principal
        )

        asignacion.fecha_asignacion = (
            fecha_asignacion
        )

        asignacion.usuario_asignacion = (
            usuario
        )

        asignacion.fecha_desasignacion = None
        asignacion.usuario_desasignacion = None

        asignacion.observaciones = (
            observaciones_limpias
        )

        asignacion.full_clean()

        asignacion.save(
            update_fields=(
                "is_active",
                "es_principal",
                "fecha_asignacion",
                "usuario_asignacion",
                "fecha_desasignacion",
                "usuario_desasignacion",
                "observaciones",
            )
        )

        return asignacion

    # ==================================================
    # NUEVA ASIGNACIÓN
    # ==================================================

    asignacion = OrdenTrabajoTecnico(
        orden_trabajo=orden,
        tecnico=tecnico,
        es_principal=es_principal,
        fecha_asignacion=fecha_asignacion,
        usuario_asignacion=usuario,
        observaciones=observaciones_limpias,
        is_active=True,
    )

    asignacion.full_clean()
    asignacion.save()

    return asignacion


# ======================================================
# CAMBIAR TÉCNICO PRINCIPAL
# ======================================================

@transaction.atomic
def establecer_tecnico_principal_ot(
    *,
    asignacion: OrdenTrabajoTecnico,
    usuario: Usuario,
) -> OrdenTrabajoTecnico:
    """
    Establece una asignación activa como
    técnico principal.

    Si existe otro principal activo,
    deja de ser principal.

    Esta operación NO desasigna técnicos.
    """

    if asignacion is None:
        raise ValueError(
            "Debe proporcionar una asignación válida."
        )

    if not asignacion.pk:
        raise ValueError(
            "La asignación debe estar guardada."
        )

    _validar_usuario(
        usuario
    )

    orden = _bloquear_orden(
        asignacion.orden_trabajo
    )

    _validar_equipo_modificable(
        orden
    )

    asignaciones = (
        OrdenTrabajoTecnico.objects
        .select_for_update()
        .filter(
            orden_trabajo=orden,
        )
    )

    objetivo = (
        asignaciones
        .filter(
            pk=asignacion.pk,
        )
        .first()
    )

    if objetivo is None:
        raise ValidationError(
            {
                "tecnico": _(
                    "La asignación indicada no pertenece "
                    "a esta orden de trabajo."
                )
            }
        )

    if not objetivo.is_active:
        raise ValidationError(
            {
                "tecnico": _(
                    "No puede establecerse como principal "
                    "un técnico que está desasignado."
                )
            }
        )

    # ==================================================
    # YA ES PRINCIPAL
    # ==================================================

    if objetivo.es_principal:
        return objetivo

    # ==================================================
    # QUITAR PRINCIPAL ANTERIOR
    # ==================================================

    principales = (
        asignaciones
        .filter(
            es_principal=True,
            is_active=True,
        )
        .exclude(
            pk=objetivo.pk,
        )
    )

    for principal in principales:
        principal.es_principal = False

        principal.full_clean()

        principal.save(
            update_fields=(
                "es_principal",
            )
        )

    # ==================================================
    # NUEVO PRINCIPAL
    # ==================================================

    objetivo.es_principal = True

    objetivo.full_clean()

    objetivo.save(
        update_fields=(
            "es_principal",
        )
    )

    return objetivo


# ======================================================
# DESASIGNAR TÉCNICO
# ======================================================

@transaction.atomic
def desasignar_tecnico_ot(
    *,
    asignacion: OrdenTrabajoTecnico,
    usuario: Usuario,
    fecha: datetime | None = None,
) -> OrdenTrabajoTecnico:
    """
    Desasigna formalmente un técnico.

    No elimina el registro.

    Se utiliza:

        is_active = False

    para conservar la trazabilidad.
    """

    if asignacion is None:
        raise ValueError(
            "Debe proporcionar una asignación válida."
        )

    if not asignacion.pk:
        raise ValueError(
            "La asignación debe estar guardada."
        )

    _validar_usuario(
        usuario
    )

    orden = _bloquear_orden(
        asignacion.orden_trabajo
    )

    _validar_equipo_modificable(
        orden
    )

    objeto = (
        OrdenTrabajoTecnico.objects
        .select_for_update()
        .filter(
            pk=asignacion.pk,
            orden_trabajo=orden,
        )
        .first()
    )

    if objeto is None:
        raise ValidationError(
            {
                "tecnico": _(
                    "La asignación indicada no pertenece "
                    "a esta orden."
                )
            }
        )

    if not objeto.is_active:
        raise ValidationError(
            {
                "tecnico": _(
                    "El técnico ya se encuentra "
                    "desasignado."
                )
            }
        )

    # ==================================================
    # FECHA
    # ==================================================

    objeto.fecha_desasignacion = (
        _resolver_fecha_hora(
            fecha_nueva=fecha,
            fecha_existente=(
                objeto.fecha_desasignacion
            ),
        )
    )

    # ==================================================
    # AUDITORÍA
    # ==================================================

    objeto.usuario_desasignacion = (
        usuario
    )

    # ==================================================
    # ESTADO DE LA ASIGNACIÓN
    # ==================================================

    objeto.is_active = False

    # Un técnico inactivo no puede seguir
    # figurando como principal.
    objeto.es_principal = False

    objeto.full_clean()

    objeto.save(
        update_fields=(
            "fecha_desasignacion",
            "usuario_desasignacion",
            "is_active",
            "es_principal",
        )
    )

    return objeto


# ======================================================
# EXPORTACIONES
# ======================================================

__all__ = (
    "asignar_tecnico_ot",
    "establecer_tecnico_principal_ot",
    "desasignar_tecnico_ot",
)