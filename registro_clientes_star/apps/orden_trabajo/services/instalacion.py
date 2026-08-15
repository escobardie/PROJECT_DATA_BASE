"""
Servicios para generar instalaciones
a partir de órdenes de trabajo.

Este módulo pertenece a OrdenTrabajo porque representa
el caso de uso:

    OrdenTrabajo -> generar Instalacion

La gestión posterior del ciclo de vida de la instalación
pertenece a apps.instalacion.services.
"""

from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.common.choices import (
    EstadoInstalacionChoices,
    EstadoOrdenTrabajoChoices,
    PrioridadInstalacionChoices,
    TipoOrdenTrabajoChoices,
)

from apps.instalacion.models import Instalacion

from apps.orden_trabajo.models import OrdenTrabajo


# ======================================================
# FUNCIONES PRIVADAS
# ======================================================

def _validar_ot_apta_para_instalacion(
    orden_trabajo: OrdenTrabajo,
) -> None:
    """
    Valida que la OT pueda originar una instalación.

    Reglas:
    - debe ser de tipo INSTALACION;
    - debe estar EN_PROCESO;
    - si requiere aprobación comercial,
      el cliente debe haber aceptado;
    - no puede estar finalizada ni cancelada.
    """

    if (
        orden_trabajo.tipo
        != TipoOrdenTrabajoChoices.INSTALACION
    ):
        raise ValidationError(
            {
                "tipo": _(
                    "Solamente una orden de tipo Instalación "
                    "puede generar una instalación."
                )
            }
        )

    if (
        orden_trabajo.estado
        != EstadoOrdenTrabajoChoices.EN_PROCESO
    ):
        raise ValidationError(
            {
                "estado": _(
                    "La orden debe estar En proceso "
                    "para generar una instalación."
                )
            }
        )

    if (
        orden_trabajo.requiere_aceptacion_cliente
        and not orden_trabajo.fue_aceptada
    ):
        raise ValidationError(
            {
                "estado_aceptacion": _(
                    "El cliente debe haber aceptado "
                    "la propuesta antes de generar "
                    "la instalación."
                )
            }
        )

def _validar_orden(
    orden_trabajo: OrdenTrabajo | None,
) -> None:
    """
    Valida que la OT exista y se encuentre guardada.
    """

    if orden_trabajo is None:
        raise ValueError(
            "Debe proporcionar una orden de trabajo válida."
        )

    if not orden_trabajo.pk:
        raise ValueError(
            "La orden de trabajo debe estar guardada."
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
        .select_related(
            "proyecto",
            "sucursal",
            "servicio_contratado",
            "presupuesto_telecom",
        )
        .get(
            pk=orden_trabajo.pk,
        )
    )


def _validar_sin_instalacion(
    orden_trabajo: OrdenTrabajo,
) -> None:
    """
    Verifica que la OT todavía no tenga
    una instalación generada.
    """

    if Instalacion.objects.filter(
        orden_trabajo=orden_trabajo,
    ).exists():
        raise ValidationError(
            {
                "orden_trabajo": _(
                    "La orden de trabajo ya tiene "
                    "una instalación asociada."
                )
            }
        )


def _resolver_fecha_programada(
    *,
    orden_trabajo: OrdenTrabajo,
    fecha_programada: date | None,
) -> date:
    """
    Obtiene la fecha programada de la instalación.

    Prioridad:

    1. Fecha indicada explícitamente.
    2. Fecha programada de la OT.

    Si ninguna existe, genera ValidationError.
    """

    if fecha_programada is not None:
        return fecha_programada

    if orden_trabajo.fecha_programada:
        return orden_trabajo.fecha_programada.date()

    raise ValidationError(
        {
            "fecha_programada": _(
                "Debe indicar la fecha programada "
                "de la instalación."
            )
        }
    )


# ======================================================
# CREAR INSTALACIÓN DESDE OT
# ======================================================

@transaction.atomic
def crear_instalacion_desde_ot(
    *,
    orden_trabajo: OrdenTrabajo,
    fecha_programada: date | None = None,
    prioridad: str = PrioridadInstalacionChoices.NORMAL,
    duracion_estimada: timedelta | None = None,
    observaciones: str = "",
) -> Instalacion:
    """
    Genera una instalación a partir de una OT.

    La relación OneToOne garantiza que una orden
    solamente pueda generar una instalación.

    Si no se proporciona fecha_programada:

    - se utiliza la fecha programada de la OT;
    - si la OT tampoco posee una, se utiliza
      la fecha local actual.

    Args:
        orden_trabajo:
            OT que origina la instalación.

        fecha_programada:
            Fecha prevista de ejecución.

        prioridad:
            Prioridad operativa de la instalación.

        duracion_estimada:
            Tiempo previsto para realizar el trabajo.

        observaciones:
            Observaciones iniciales.

    Returns:
        Instalacion:
            Instalación creada.

    Raises:
        ValueError:
            Si la OT no está guardada.

        ValidationError:
            Si la OT ya tiene una instalación
            o los datos son inválidos.
    """

    orden = _bloquear_orden(
        orden_trabajo
    )
    _validar_ot_apta_para_instalacion(
        orden
    )

    _validar_sin_instalacion(
        orden
    )

    fecha = _resolver_fecha_programada(
        orden_trabajo=orden,
        fecha_programada=fecha_programada,
    )

    instalacion = Instalacion(
        orden_trabajo=orden,
        prioridad=prioridad,
        fecha_programada=fecha,
        duracion_estimada=duracion_estimada,
        estado=EstadoInstalacionChoices.PENDIENTE,
        observaciones=(
            observaciones or ""
        ).strip(),
    )

    instalacion.full_clean()

    instalacion.save()

    return instalacion


__all__ = (
    "crear_instalacion_desde_ot",
)