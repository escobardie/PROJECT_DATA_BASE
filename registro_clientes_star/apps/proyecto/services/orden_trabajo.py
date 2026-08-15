"""
Servicios para generar órdenes de trabajo
a partir de proyectos aprobados.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.common.choices import (
    EstadoOrdenTrabajoChoices,
    EstadoProyectoChoices,
)

from apps.orden_trabajo.models import OrdenTrabajo
from apps.proyecto.models import Proyecto


def _validar_proyecto_guardado(
    proyecto: Proyecto | None,
) -> None:
    """
    Valida que exista un proyecto persistido.
    """

    if proyecto is None:
        raise ValueError(
            "Debe proporcionar un proyecto válido."
        )

    if not proyecto.pk:
        raise ValueError(
            "El proyecto debe estar guardado antes "
            "de generar una orden de trabajo."
        )


def _bloquear_proyecto(
    proyecto: Proyecto,
) -> Proyecto:
    """
    Recupera y bloquea el proyecto durante
    la generación de la OT.
    """

    _validar_proyecto_guardado(
        proyecto
    )

    return (
        Proyecto.objects
        .select_for_update()
        .select_related(
            "sucursal",
            "responsable",
        )
        .get(
            pk=proyecto.pk,
        )
    )


def _validar_proyecto_aprobado(
    proyecto: Proyecto,
) -> None:
    """
    Solamente permite generar OT desde
    proyectos aprobados.
    """

    if (
        proyecto.estado
        != EstadoProyectoChoices.APROBADO
    ):
        raise ValidationError(
            {
                "estado": _(
                    "Solamente puede generar una orden "
                    "de trabajo desde un proyecto aprobado."
                )
            }
        )


@transaction.atomic
def crear_orden_trabajo_desde_proyecto(
    *,
    proyecto: Proyecto,
) -> OrdenTrabajo:
    """
    Genera una nueva OT en BORRADOR
    vinculada al proyecto aprobado.

    El proyecto puede originar varias OT.
    """

    objeto = _bloquear_proyecto(
        proyecto
    )

    _validar_proyecto_aprobado(
        objeto
    )

    orden = OrdenTrabajo(
        proyecto=objeto,
        sucursal=objeto.sucursal,
        responsable=objeto.responsable,
        titulo=objeto.nombre,
        descripcion=objeto.descripcion or "",
        estado=EstadoOrdenTrabajoChoices.BORRADOR,
    )

    orden.full_clean()
    orden.save()

    return orden


__all__ = (
    "crear_orden_trabajo_desde_proyecto",
)