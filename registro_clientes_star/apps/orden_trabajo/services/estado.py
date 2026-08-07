"""
Servicios relacionados con el ciclo de vida
de las órdenes de trabajo.

Este módulo centraliza:

- recepción de solicitudes;
- cambio de estado operativo;
- programación;
- inicio;
- pausa;
- reanudación;
- finalización;
- cancelación;
- envío al cliente;
- aceptación del cliente;
- facturación;
- cobro.

Los cambios se realizan dentro de transacciones atómicas
y registran el usuario responsable cuando corresponde.
"""

from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.choices import (
    EstadoOrdenTrabajoChoices,
)

from apps.orden_trabajo.models import (
    OrdenTrabajo,
)

from apps.usuarios.models import Usuario


# ======================================================
# TRANSICIONES DE ESTADO
# ======================================================

TRANSICIONES_ESTADO = {
    EstadoOrdenTrabajoChoices.BORRADOR: {
        EstadoOrdenTrabajoChoices.PENDIENTE,
        EstadoOrdenTrabajoChoices.PROGRAMADA,
        EstadoOrdenTrabajoChoices.CANCELADA,
    },

    EstadoOrdenTrabajoChoices.PENDIENTE: {
        EstadoOrdenTrabajoChoices.PROGRAMADA,
        EstadoOrdenTrabajoChoices.EN_PROCESO,
        EstadoOrdenTrabajoChoices.CANCELADA,
    },

    EstadoOrdenTrabajoChoices.PROGRAMADA: {
        EstadoOrdenTrabajoChoices.PENDIENTE,
        EstadoOrdenTrabajoChoices.EN_PROCESO,
        EstadoOrdenTrabajoChoices.CANCELADA,
    },

    EstadoOrdenTrabajoChoices.EN_PROCESO: {
        EstadoOrdenTrabajoChoices.PAUSADA,
        EstadoOrdenTrabajoChoices.FINALIZADA,
        EstadoOrdenTrabajoChoices.CANCELADA,
    },

    EstadoOrdenTrabajoChoices.PAUSADA: {
        EstadoOrdenTrabajoChoices.EN_PROCESO,
        EstadoOrdenTrabajoChoices.CANCELADA,
    },

    EstadoOrdenTrabajoChoices.FINALIZADA: set(),

    EstadoOrdenTrabajoChoices.CANCELADA: set(),
}


# ======================================================
# FUNCIONES PRIVADAS
# ======================================================

def _validar_orden_guardada(
    orden_trabajo: OrdenTrabajo | None,
) -> None:
    """
    Valida que se haya proporcionado una OT persistida.
    """

    if orden_trabajo is None:
        raise ValueError(
            "Debe proporcionar una orden de trabajo válida."
        )

    if not orden_trabajo.pk:
        raise ValueError(
            "La orden de trabajo debe estar guardada "
            "antes de ejecutar esta operación."
        )


def _validar_usuario(
    usuario: Usuario | None,
) -> None:
    """
    Valida que exista un usuario responsable
    de registrar la operación.
    """

    if usuario is None:
        raise ValueError(
            "Debe proporcionar el usuario que "
            "registra la operación."
        )

    if not usuario.pk:
        raise ValueError(
            "El usuario debe estar guardado."
        )


def _obtener_fecha(
    fecha: datetime | None,
) -> datetime:
    """
    Devuelve la fecha proporcionada o la fecha/hora actual.
    """

    return fecha or timezone.now()


def _bloquear_orden(
    orden_trabajo: OrdenTrabajo,
) -> OrdenTrabajo:
    """
    Recupera y bloquea la OT durante
    la transacción actual.
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


def _validar_transicion(
    *,
    estado_actual: str,
    nuevo_estado: str,
) -> None:
    """
    Valida una transición del ciclo de vida operativo.
    """

    if estado_actual == nuevo_estado:
        return

    estados_permitidos = (
        TRANSICIONES_ESTADO.get(
            estado_actual,
            set(),
        )
    )

    if nuevo_estado not in estados_permitidos:
        raise ValidationError(
            {
                "estado": _(
                    "No se puede cambiar la orden de "
                    "%(actual)s a %(nuevo)s."
                )
                % {
                    "actual": estado_actual,
                    "nuevo": nuevo_estado,
                }
            }
        )


def _validar_y_guardar(
    orden_trabajo: OrdenTrabajo,
    *,
    campos: tuple[str, ...],
) -> OrdenTrabajo:
    """
    Ejecuta las validaciones del modelo y guarda
    únicamente los campos modificados.
    """

    orden_trabajo.full_clean()

    orden_trabajo.save(
        update_fields=campos,
    )

    return orden_trabajo


# ======================================================
# RECEPCIÓN DE SOLICITUD
# ======================================================

@transaction.atomic
def registrar_recepcion_solicitud(
    *,
    orden_trabajo: OrdenTrabajo,
    usuario: Usuario,
    fecha: datetime | None = None,
) -> OrdenTrabajo:
    """
    Registra la recepción de una solicitud del cliente.

    Si la OT se encuentra en BORRADOR, pasa
    automáticamente a PENDIENTE.
    """

    _validar_usuario(usuario)

    orden = _bloquear_orden(
        orden_trabajo
    )

    fecha_registro = _obtener_fecha(
        fecha
    )

    orden.fecha_recepcion_solicitud = (
        fecha_registro
    )

    orden.usuario_recepcion_solicitud = (
        usuario
    )

    campos = [
        "fecha_recepcion_solicitud",
        "usuario_recepcion_solicitud",
    ]

    if (
        orden.estado
        == EstadoOrdenTrabajoChoices.BORRADOR
    ):
        _validar_transicion(
            estado_actual=orden.estado,
            nuevo_estado=(
                EstadoOrdenTrabajoChoices.PENDIENTE
            ),
        )

        orden.estado = (
            EstadoOrdenTrabajoChoices.PENDIENTE
        )

        campos.append(
            "estado"
        )

    return _validar_y_guardar(
        orden,
        campos=tuple(campos),
    )


# ======================================================
# PROGRAMACIÓN
# ======================================================

@transaction.atomic
def programar_orden_trabajo(
    *,
    orden_trabajo: OrdenTrabajo,
    fecha_programada: datetime,
) -> OrdenTrabajo:
    """
    Programa la ejecución de una OT y establece
    su estado en PROGRAMADA.
    """

    if fecha_programada is None:
        raise ValidationError(
            {
                "fecha_programada": _(
                    "Debe indicar la fecha programada."
                )
            }
        )

    orden = _bloquear_orden(
        orden_trabajo
    )

    _validar_transicion(
        estado_actual=orden.estado,
        nuevo_estado=(
            EstadoOrdenTrabajoChoices.PROGRAMADA
        ),
    )

    orden.fecha_programada = (
        fecha_programada
    )

    orden.estado = (
        EstadoOrdenTrabajoChoices.PROGRAMADA
    )

    return _validar_y_guardar(
        orden,
        campos=(
            "fecha_programada",
            "estado",
        ),
    )


# ======================================================
# INICIO
# ======================================================

@transaction.atomic
def iniciar_orden_trabajo(
    *,
    orden_trabajo: OrdenTrabajo,
    usuario: Usuario,
    fecha: datetime | None = None,
) -> OrdenTrabajo:
    """
    Registra el inicio de ejecución y cambia
    el estado de la OT a EN_PROCESO.
    """

    _validar_usuario(usuario)

    orden = _bloquear_orden(
        orden_trabajo
    )

    _validar_transicion(
        estado_actual=orden.estado,
        nuevo_estado=(
            EstadoOrdenTrabajoChoices.EN_PROCESO
        ),
    )

    orden.fecha_inicio = (
        _obtener_fecha(fecha)
    )

    orden.usuario_inicio = usuario

    orden.estado = (
        EstadoOrdenTrabajoChoices.EN_PROCESO
    )

    return _validar_y_guardar(
        orden,
        campos=(
            "fecha_inicio",
            "usuario_inicio",
            "estado",
        ),
    )


# ======================================================
# PAUSA
# ======================================================

@transaction.atomic
def pausar_orden_trabajo(
    *,
    orden_trabajo: OrdenTrabajo,
) -> OrdenTrabajo:
    """
    Pausa una orden que se encuentra en ejecución.
    """

    orden = _bloquear_orden(
        orden_trabajo
    )

    _validar_transicion(
        estado_actual=orden.estado,
        nuevo_estado=(
            EstadoOrdenTrabajoChoices.PAUSADA
        ),
    )

    orden.estado = (
        EstadoOrdenTrabajoChoices.PAUSADA
    )

    return _validar_y_guardar(
        orden,
        campos=(
            "estado",
        ),
    )


# ======================================================
# REANUDACIÓN
# ======================================================

@transaction.atomic
def reanudar_orden_trabajo(
    *,
    orden_trabajo: OrdenTrabajo,
) -> OrdenTrabajo:
    """
    Reanuda una OT pausada.
    """

    orden = _bloquear_orden(
        orden_trabajo
    )

    _validar_transicion(
        estado_actual=orden.estado,
        nuevo_estado=(
            EstadoOrdenTrabajoChoices.EN_PROCESO
        ),
    )

    orden.estado = (
        EstadoOrdenTrabajoChoices.EN_PROCESO
    )

    return _validar_y_guardar(
        orden,
        campos=(
            "estado",
        ),
    )


# ======================================================
# FINALIZACIÓN
# ======================================================

@transaction.atomic
def finalizar_orden_trabajo(
    *,
    orden_trabajo: OrdenTrabajo,
    usuario: Usuario,
    fecha: datetime | None = None,
) -> OrdenTrabajo:
    """
    Registra la finalización operativa de una OT.
    """

    _validar_usuario(usuario)

    orden = _bloquear_orden(
        orden_trabajo
    )

    _validar_transicion(
        estado_actual=orden.estado,
        nuevo_estado=(
            EstadoOrdenTrabajoChoices.FINALIZADA
        ),
    )

    orden.fecha_finalizacion = (
        _obtener_fecha(fecha)
    )

    orden.usuario_finalizacion = usuario

    orden.estado = (
        EstadoOrdenTrabajoChoices.FINALIZADA
    )

    return _validar_y_guardar(
        orden,
        campos=(
            "fecha_finalizacion",
            "usuario_finalizacion",
            "estado",
        ),
    )


# ======================================================
# CANCELACIÓN
# ======================================================

@transaction.atomic
def cancelar_orden_trabajo(
    *,
    orden_trabajo: OrdenTrabajo,
) -> OrdenTrabajo:
    """
    Cancela una orden de trabajo.

    Una OT finalizada o ya cancelada no puede pasar
    nuevamente a CANCELADA mediante este servicio.
    """

    orden = _bloquear_orden(
        orden_trabajo
    )

    _validar_transicion(
        estado_actual=orden.estado,
        nuevo_estado=(
            EstadoOrdenTrabajoChoices.CANCELADA
        ),
    )

    orden.estado = (
        EstadoOrdenTrabajoChoices.CANCELADA
    )

    return _validar_y_guardar(
        orden,
        campos=(
            "estado",
        ),
    )


# ======================================================
# ENVÍO AL CLIENTE
# ======================================================

@transaction.atomic
def registrar_envio_cliente(
    *,
    orden_trabajo: OrdenTrabajo,
    usuario: Usuario,
    fecha: datetime | None = None,
) -> OrdenTrabajo:
    """
    Registra que una OT finalizada fue enviada
    al cliente.
    """

    _validar_usuario(usuario)

    orden = _bloquear_orden(
        orden_trabajo
    )

    if (
        orden.estado
        != EstadoOrdenTrabajoChoices.FINALIZADA
    ):
        raise ValidationError(
            {
                "estado": _(
                    "La orden debe estar finalizada "
                    "antes de enviarla al cliente."
                )
            }
        )

    orden.fecha_envio_cliente = (
        _obtener_fecha(fecha)
    )

    orden.usuario_envio_cliente = usuario

    return _validar_y_guardar(
        orden,
        campos=(
            "fecha_envio_cliente",
            "usuario_envio_cliente",
        ),
    )


# ======================================================
# ACEPTACIÓN DEL CLIENTE
# ======================================================

@transaction.atomic
def registrar_aceptacion_cliente(
    *,
    orden_trabajo: OrdenTrabajo,
    usuario: Usuario,
    fecha: datetime | None = None,
) -> OrdenTrabajo:
    """
    Registra la aceptación de la OT por parte
    del cliente.
    """

    _validar_usuario(usuario)

    orden = _bloquear_orden(
        orden_trabajo
    )

    if not orden.fecha_envio_cliente:
        raise ValidationError(
            {
                "fecha_aceptacion": _(
                    "La orden debe haber sido enviada "
                    "al cliente antes de registrar "
                    "su aceptación."
                )
            }
        )

    orden.fecha_aceptacion = (
        _obtener_fecha(fecha)
    )

    orden.usuario_aceptacion = usuario

    return _validar_y_guardar(
        orden,
        campos=(
            "fecha_aceptacion",
            "usuario_aceptacion",
        ),
    )


# ======================================================
# FACTURACIÓN
# ======================================================

@transaction.atomic
def registrar_facturacion_ot(
    *,
    orden_trabajo: OrdenTrabajo,
    usuario: Usuario,
    fecha: datetime | None = None,
) -> OrdenTrabajo:
    """
    Registra la facturación de una orden de trabajo.

    Este servicio registra únicamente la trazabilidad
    de la OT. La creación de una Factura pertenece
    al módulo de facturación.
    """

    _validar_usuario(usuario)

    orden = _bloquear_orden(
        orden_trabajo
    )

    if (
        orden.estado
        != EstadoOrdenTrabajoChoices.FINALIZADA
    ):
        raise ValidationError(
            {
                "fecha_facturacion": _(
                    "La orden debe estar finalizada "
                    "antes de registrar su facturación."
                )
            }
        )

    if orden.fecha_facturacion:
        raise ValidationError(
            {
                "fecha_facturacion": _(
                    "La orden ya tiene una fecha "
                    "de facturación registrada."
                )
            }
        )

    orden.fecha_facturacion = (
        _obtener_fecha(fecha)
    )

    orden.usuario_facturacion = usuario

    return _validar_y_guardar(
        orden,
        campos=(
            "fecha_facturacion",
            "usuario_facturacion",
        ),
    )


# ======================================================
# COBRO
# ======================================================

@transaction.atomic
def registrar_cobro_ot(
    *,
    orden_trabajo: OrdenTrabajo,
    usuario: Usuario,
    fecha: datetime | None = None,
) -> OrdenTrabajo:
    """
    Registra el cobro de una orden previamente facturada.

    Este servicio registra la trazabilidad de la OT;
    no crea movimientos financieros.
    """

    _validar_usuario(usuario)

    orden = _bloquear_orden(
        orden_trabajo
    )

    if not orden.fecha_facturacion:
        raise ValidationError(
            {
                "fecha_cobro": _(
                    "Debe registrar la facturación "
                    "antes de registrar el cobro."
                )
            }
        )

    if orden.fecha_cobro:
        raise ValidationError(
            {
                "fecha_cobro": _(
                    "La orden ya tiene un cobro registrado."
                )
            }
        )

    orden.fecha_cobro = (
        _obtener_fecha(fecha)
    )

    orden.usuario_cobro = usuario

    return _validar_y_guardar(
        orden,
        campos=(
            "fecha_cobro",
            "usuario_cobro",
        ),
    )


__all__ = (
    "registrar_recepcion_solicitud",
    "programar_orden_trabajo",
    "iniciar_orden_trabajo",
    "pausar_orden_trabajo",
    "reanudar_orden_trabajo",
    "finalizar_orden_trabajo",
    "cancelar_orden_trabajo",
    "registrar_envio_cliente",
    "registrar_aceptacion_cliente",
    "registrar_facturacion_ot",
    "registrar_cobro_ot",
)