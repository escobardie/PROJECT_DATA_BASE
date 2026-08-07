"""
Servicios relacionados con el ciclo de vida
de los proyectos.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.common.choices import EstadoProyectoChoices
from apps.proyecto.models import Proyecto


# ======================================================
# VALIDACIÓN DE ESTADO
# ======================================================

def _validar_estado_proyecto(
    estado: str,
) -> None:
    """
    Valida que el estado indicado pertenezca
    a EstadoProyectoChoices.

    Raises:
        ValidationError:
            Cuando el estado no es válido.
    """

    estados_validos = {
        valor
        for valor, _etiqueta
        in EstadoProyectoChoices.choices
    }

    if estado not in estados_validos:
        raise ValidationError(
            {
                "estado": _(
                    "El estado indicado no es válido."
                )
            }
        )


# ======================================================
# CAMBIO DE ESTADO
# ======================================================

@transaction.atomic
def cambiar_estado_proyecto(
    *,
    proyecto: Proyecto,
    estado: str,
) -> Proyecto:
    """
    Cambia el estado de un proyecto.

    La operación bloquea el registro durante
    la transacción para evitar modificaciones
    concurrentes.

    Args:
        proyecto:
            Proyecto cuyo estado debe modificarse.

        estado:
            Nuevo estado definido en
            EstadoProyectoChoices.

    Returns:
        Proyecto:
            Proyecto actualizado.

    Raises:
        ValueError:
            Cuando el proyecto no existe o todavía
            no fue guardado.

        ValidationError:
            Cuando el estado indicado no es válido.
    """

    if proyecto is None:
        raise ValueError(
            "Debe proporcionar un proyecto válido."
        )

    if not proyecto.pk:
        raise ValueError(
            "El proyecto debe estar guardado antes "
            "de modificar su estado."
        )

    _validar_estado_proyecto(
        estado
    )

    proyecto_bloqueado = (
        Proyecto.objects
        .select_for_update()
        .get(
            pk=proyecto.pk,
        )
    )

    # No realiza una escritura innecesaria.
    if proyecto_bloqueado.estado == estado:
        return proyecto_bloqueado

    proyecto_bloqueado.estado = estado

    proyecto_bloqueado.full_clean()

    Proyecto.objects.filter(
        pk=proyecto_bloqueado.pk,
    ).update(
        estado=estado,
    )

    return proyecto_bloqueado


__all__ = (
    "cambiar_estado_proyecto",
)