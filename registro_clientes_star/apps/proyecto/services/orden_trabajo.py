"""
Servicios para generar órdenes de trabajo
a partir de proyectos aprobados.

Una OT generada desde Proyecto hereda la información
comercial y operativa ya registrada en el Proyecto.

El Proyecto continúa siendo la fuente comercial original,
mientras que la OT representa la ejecución del trabajo.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.common.choices import (
    EstadoAceptacionOTChoices,
    EstadoOrdenTrabajoChoices,
    EstadoProyectoChoices,
    PrioridadOrdenTrabajoChoices,
    PrioridadProyectoChoices,
    RespuestaClienteProyectoChoices,
)

from apps.orden_trabajo.models import OrdenTrabajo
from apps.proyecto.models import Proyecto


# ======================================================
# MAPEO DE PRIORIDADES
# ======================================================

MAPEO_PRIORIDAD_PROYECTO_OT = {
    PrioridadProyectoChoices.BAJA: (
        PrioridadOrdenTrabajoChoices.BAJA
    ),
    PrioridadProyectoChoices.NORMAL: (
        PrioridadOrdenTrabajoChoices.MEDIA
    ),
    PrioridadProyectoChoices.ALTA: (
        PrioridadOrdenTrabajoChoices.ALTA
    ),
    PrioridadProyectoChoices.URGENTE: (
        PrioridadOrdenTrabajoChoices.URGENTE
    ),
}


# ======================================================
# VALIDACIONES PRIVADAS
# ======================================================

def _validar_proyecto_guardado(
    proyecto: Proyecto | None,
) -> None:
    """
    Valida que exista un Proyecto persistido.
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
    Obtiene el Proyecto desde la base de datos
    aplicando bloqueo de fila durante la transacción.
    """

    _validar_proyecto_guardado(
        proyecto
    )

    try:
        return (
            Proyecto.objects
            .select_for_update()
            .select_related(
                # Origen
                "sucursal",

                # Responsable
                "responsable",

                # Trazabilidad
                "usuario_recepcion_solicitud",
                "usuario_envio_cliente",
                "usuario_respuesta_cliente",
            )
            .get(
                pk=proyecto.pk,
            )
        )

    except Proyecto.DoesNotExist as exc:
        raise ValidationError(
            {
                "proyecto": _(
                    "El proyecto indicado ya no existe."
                )
            }
        ) from exc


def _validar_proyecto_aprobado(
    proyecto: Proyecto,
) -> None:
    """
    Solamente permite generar una OT desde
    un Proyecto aprobado.
    """

    if (
        proyecto.estado
        != EstadoProyectoChoices.APROBADO
    ):
        raise ValidationError(
            {
                "estado": _(
                    "Solo se puede generar una orden "
                    "de trabajo desde un proyecto aprobado."
                )
            }
        )


def _validar_proyecto_con_detalles(
    proyecto: Proyecto,
) -> None:
    """
    Requiere al menos un detalle activo.
    """

    tiene_detalles_activos = (
        proyecto.detalles
        .filter(
            is_active=True,
        )
        .exists()
    )

    if not tiene_detalles_activos:
        raise ValidationError(
            {
                "proyecto": _(
                    "No se puede generar una orden de trabajo "
                    "porque el proyecto no tiene detalles activos."
                )
            }
        )


def _validar_aprobacion_cliente(
    proyecto: Proyecto,
) -> None:
    """
    Verifica que el Proyecto tenga completa
    la aprobación comercial que posteriormente
    heredará la OT.

    Una OT generada desde Proyecto no debe solicitar
    nuevamente la aprobación del cliente.
    """

    if (
        proyecto.respuesta_cliente
        != RespuestaClienteProyectoChoices.ACEPTADO
    ):
        raise ValidationError(
            {
                "proyecto": _(
                    "El proyecto debe haber sido aceptado "
                    "por el cliente antes de generar una OT."
                )
            }
        )

    if not proyecto.fecha_envio_cliente:
        raise ValidationError(
            {
                "fecha_envio_cliente": _(
                    "El proyecto aprobado no tiene registrada "
                    "la fecha de envío al cliente."
                )
            }
        )

    if not proyecto.usuario_envio_cliente_id:
        raise ValidationError(
            {
                "proyecto": _(
                    "El proyecto aprobado no tiene registrado "
                    "el usuario que realizó el envío."
                )
            }
        )

    if not proyecto.fecha_respuesta_cliente:
        raise ValidationError(
            {
                "fecha_respuesta_cliente": _(
                    "El proyecto aprobado no tiene registrada "
                    "la fecha de aceptación del cliente."
                )
            }
        )

    if not proyecto.usuario_respuesta_cliente_id:
        raise ValidationError(
            {
                "proyecto": _(
                    "El proyecto aprobado no tiene registrado "
                    "el usuario que registró la aceptación."
                )
            }
        )


def _resolver_prioridad_ot(
    proyecto: Proyecto,
) -> PrioridadOrdenTrabajoChoices:
    """
    Convierte la prioridad comercial del Proyecto
    a la prioridad equivalente de OrdenTrabajo.
    """

    try:
        return MAPEO_PRIORIDAD_PROYECTO_OT[
            proyecto.prioridad
        ]

    except KeyError as exc:
        raise ValidationError(
            {
                "prioridad": _(
                    "La prioridad del proyecto no puede "
                    "convertirse a una prioridad de OT."
                )
            }
        ) from exc


# ======================================================
# CREAR OT DESDE PROYECTO
# ======================================================

@transaction.atomic
def crear_orden_trabajo_desde_proyecto(
    *,
    proyecto: Proyecto,
) -> OrdenTrabajo:
    """
    Genera una nueva OrdenTrabajo a partir
    de un Proyecto aprobado.

    La nueva OT hereda:

    - Proyecto de origen.
    - Sucursal.
    - Responsable.
    - Nombre como título.
    - Descripción.
    - Prioridad.
    - Recepción de la solicitud.
    - Usuario que registró la recepción.
    - Envío al cliente.
    - Usuario que registró el envío.
    - Aceptación del cliente.
    - Fecha de aceptación.
    - Usuario que registró la aceptación.

    La OT se crea en BORRADOR.

    La fecha programada NO se copia automáticamente
    porque Proyecto.fecha_planificada es DateField
    mientras que OrdenTrabajo.fecha_programada
    requiere DateTimeField.

    La programación concreta de la OT se realizará
    posteriormente desde el flujo propio de OrdenTrabajo.
    """

    # ==================================================
    # VALIDACIÓN INICIAL
    # ==================================================

    _validar_proyecto_guardado(
        proyecto
    )

    # ==================================================
    # BLOQUEO
    # ==================================================

    objeto = _bloquear_proyecto(
        proyecto
    )

    # ==================================================
    # VALIDACIONES COMERCIALES
    # ==================================================

    _validar_proyecto_aprobado(
        objeto
    )

    _validar_proyecto_con_detalles(
        objeto
    )

    _validar_aprobacion_cliente(
        objeto
    )

    # ==================================================
    # PRIORIDAD
    # ==================================================

    prioridad_ot = _resolver_prioridad_ot(
        objeto
    )

    # ==================================================
    # CREACIÓN DE LA OT
    # ==================================================

    orden = OrdenTrabajo(

        # ----------------------------------------------
        # ORIGEN
        # ----------------------------------------------

        proyecto=objeto,

        sucursal=objeto.sucursal,

        # ----------------------------------------------
        # INFORMACIÓN GENERAL
        # ----------------------------------------------

        titulo=objeto.nombre,

        descripcion=(
            objeto.descripcion
            or ""
        ),

        # ----------------------------------------------
        # CLASIFICACIÓN
        # ----------------------------------------------

        estado=(
            EstadoOrdenTrabajoChoices.BORRADOR
        ),

        prioridad=prioridad_ot,

        # ----------------------------------------------
        # RECEPCIÓN
        # ----------------------------------------------

        fecha_recepcion_solicitud=(
            objeto.fecha_recepcion_solicitud
        ),

        usuario_recepcion_solicitud=(
            objeto.usuario_recepcion_solicitud
        ),

        # ----------------------------------------------
        # PLANIFICACIÓN
        # ----------------------------------------------

        responsable=(
            objeto.responsable
        ),

        # No copiamos fecha_planificada porque
        # OrdenTrabajo necesita fecha y hora.
        fecha_programada=None,

        # ----------------------------------------------
        # ENVÍO AL CLIENTE
        # ----------------------------------------------

        fecha_envio_cliente=(
            objeto.fecha_envio_cliente
        ),

        usuario_envio_cliente=(
            objeto.usuario_envio_cliente
        ),

        # ----------------------------------------------
        # RESPUESTA DEL CLIENTE
        # ----------------------------------------------

        estado_aceptacion=(
            EstadoAceptacionOTChoices.ACEPTADA
        ),

        fecha_aceptacion=(
            objeto.fecha_respuesta_cliente
        ),

        usuario_aceptacion=(
            objeto.usuario_respuesta_cliente
        ),
    )

    # ==================================================
    # VALIDACIÓN DEL MODELO
    # ==================================================

    orden.full_clean()

    # ==================================================
    # GUARDADO
    # ==================================================

    orden.save()

    return orden


# ======================================================
# EXPORTS
# ======================================================

__all__ = (
    "crear_orden_trabajo_desde_proyecto",
)