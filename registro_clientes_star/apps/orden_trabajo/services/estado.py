"""
Servicios relacionados con el ciclo de vida
de las órdenes de trabajo.

Este módulo centraliza:

- recepción de solicitudes;
- programación;
- envío al cliente;
- aceptación o rechazo del cliente;
- inicio;
- pausa;
- reanudación;
- finalización;
- cancelación;
- facturación;
- cobro.

Los cambios se realizan dentro de transacciones atómicas
y registran el usuario responsable cuando corresponde.

Regla general para fechas de hitos:

1. se utiliza la fecha proporcionada explícitamente;
2. si no existe, se conserva la fecha previamente cargada;
3. si tampoco existe, se utiliza timezone.now().

La fecha representa cuándo ocurrió el evento.

Los campos usuario_* representan quién confirmó
formalmente el hito dentro del sistema.
"""

from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.choices import (
    EstadoAceptacionOTChoices,
    EstadoInstalacionChoices,
    EstadoOrdenTrabajoChoices,
    TipoOrdenTrabajoChoices,
)

from apps.orden_trabajo.models import OrdenTrabajo
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
    Valida que se haya proporcionado
    una orden de trabajo persistida.
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


def _resolver_fecha(
    *,
    fecha_nueva: datetime | None,
    fecha_existente: datetime | None,
) -> datetime:
    """
    Resuelve la fecha/hora que debe utilizarse.

    Prioridad:

    1. fecha proporcionada explícitamente;
    2. fecha previamente registrada;
    3. fecha/hora actual.
    """

    return (
        fecha_nueva
        or fecha_existente
        or timezone.now()
    )


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
        .select_related(
            "proyecto",
            "sucursal",
            "servicio_contratado",
            "presupuesto_telecom",
            "instalacion",
        )
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
    Registra la recepción de la solicitud
    que dio origen a la orden de trabajo.

    Prioridad de fecha:

    1. fecha enviada desde el Admin;
    2. fecha previamente cargada;
    3. fecha/hora actual.

    El hito se considera formalmente registrado
    cuando existe usuario_recepcion_solicitud.

    Una OT generada desde Proyecto puede heredar
    tanto la fecha como el usuario de recepción,
    por lo que no debe registrar nuevamente este hito.
    """

    # ==================================================
    # VALIDAR USUARIO
    # ==================================================

    _validar_usuario(
        usuario
    )

    # ==================================================
    # BLOQUEAR OT
    # ==================================================

    orden = _bloquear_orden(
        orden_trabajo
    )

    # ==================================================
    # VALIDAR HITO PREVIO
    # ==================================================

    if orden.usuario_recepcion_solicitud_id:
        raise ValidationError(
            {
                "usuario_recepcion_solicitud": _(
                    "La recepción de la solicitud "
                    "ya fue registrada."
                )
            }
        )

    # ==================================================
    # VALIDAR ESTADO
    # ==================================================

    if (
        orden.estado
        != EstadoOrdenTrabajoChoices.BORRADOR
    ):
        raise ValidationError(
            {
                "estado": _(
                    "La recepción de la solicitud "
                    "solo puede registrarse cuando "
                    "la orden está en borrador."
                )
            }
        )

    # ==================================================
    # RESOLVER FECHA
    # ==================================================

    orden.fecha_recepcion_solicitud = (
        _resolver_fecha(
            fecha_nueva=fecha,
            fecha_existente=(
                orden.fecha_recepcion_solicitud
            ),
        )
    )

    # ==================================================
    # REGISTRAR USUARIO
    # ==================================================

    orden.usuario_recepcion_solicitud = usuario

    # ==================================================
    # CAMBIAR ESTADO
    # ==================================================

    orden.estado = (
        EstadoOrdenTrabajoChoices.PENDIENTE
    )

    # ==================================================
    # VALIDAR Y GUARDAR
    # ==================================================

    return _validar_y_guardar(
        orden,
        campos=(
            "fecha_recepcion_solicitud",
            "usuario_recepcion_solicitud",
            "estado",
        ),
    )


# ======================================================
# PROGRAMACIÓN
# ======================================================

@transaction.atomic
def programar_orden_trabajo(
    *,
    orden_trabajo: OrdenTrabajo,
    fecha_programada: datetime | None = None,
) -> OrdenTrabajo:
    """
    Programa la ejecución de una OT
    y establece su estado en PROGRAMADA.

    Prioridad para fecha_programada:

    1. fecha enviada desde el Admin;
    2. fecha previamente cargada;
    3. fecha/hora actual.
    """

    # ==================================================
    # BLOQUEAR OT
    # ==================================================

    orden = _bloquear_orden(
        orden_trabajo
    )

    # ==================================================
    # VALIDAR TRANSICIÓN
    # ==================================================

    _validar_transicion(
        estado_actual=orden.estado,
        nuevo_estado=(
            EstadoOrdenTrabajoChoices.PROGRAMADA
        ),
    )

    # ==================================================
    # RESOLVER FECHA PROGRAMADA
    # ==================================================

    orden.fecha_programada = (
        _resolver_fecha(
            fecha_nueva=fecha_programada,
            fecha_existente=(
                orden.fecha_programada
            ),
        )
    )

    # ==================================================
    # CAMBIAR ESTADO
    # ==================================================

    orden.estado = (
        EstadoOrdenTrabajoChoices.PROGRAMADA
    )

    # ==================================================
    # VALIDAR Y GUARDAR
    # ==================================================

    return _validar_y_guardar(
        orden,
        campos=(
            "fecha_programada",
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
    Registra el envío al cliente de la propuesta
    relacionada con la OT.

    Se utiliza para órdenes provenientes de:

    - Proyecto;
    - Presupuesto Telecom.

    El hito se considera formalmente registrado
    cuando existe usuario_envio_cliente.
    """

    # ==================================================
    # VALIDAR USUARIO
    # ==================================================

    _validar_usuario(
        usuario
    )

    # ==================================================
    # BLOQUEAR OT
    # ==================================================

    orden = _bloquear_orden(
        orden_trabajo
    )

    # ==================================================
    # VALIDAR FLUJO COMERCIAL
    # ==================================================

    if not orden.requiere_aceptacion_cliente:
        raise ValidationError(
            {
                "fecha_envio_cliente": _(
                    "Esta orden de trabajo no requiere "
                    "un proceso de aprobación comercial."
                )
            }
        )

    # ==================================================
    # VALIDAR RECEPCIÓN
    # ==================================================

    if not orden.fecha_recepcion_solicitud:
        raise ValidationError(
            {
                "fecha_envio_cliente": _(
                    "Debe registrar primero la recepción "
                    "de la solicitud."
                )
            }
        )

    # ==================================================
    # VALIDAR HITO PREVIO
    # ==================================================

    if orden.usuario_envio_cliente_id:
        raise ValidationError(
            {
                "usuario_envio_cliente": _(
                    "El envío al cliente "
                    "ya fue registrado."
                )
            }
        )

    # ==================================================
    # VALIDAR ESTADO
    # ==================================================

    if orden.estado not in {
        EstadoOrdenTrabajoChoices.PENDIENTE,
        EstadoOrdenTrabajoChoices.PROGRAMADA,
    }:
        raise ValidationError(
            {
                "estado": _(
                    "La propuesta solo puede enviarse "
                    "cuando la orden está Pendiente "
                    "o Programada."
                )
            }
        )

    # ==================================================
    # RESOLVER FECHA
    # ==================================================

    orden.fecha_envio_cliente = (
        _resolver_fecha(
            fecha_nueva=fecha,
            fecha_existente=(
                orden.fecha_envio_cliente
            ),
        )
    )

    # ==================================================
    # REGISTRAR USUARIO
    # ==================================================

    orden.usuario_envio_cliente = usuario

    # ==================================================
    # VALIDAR Y GUARDAR
    # ==================================================

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
    Registra la aceptación de la propuesta
    por parte del cliente.

    La fecha puede estar previamente cargada
    sin que el hito haya sido formalmente registrado.
    """

    # ==================================================
    # VALIDAR USUARIO
    # ==================================================

    _validar_usuario(
        usuario
    )

    # ==================================================
    # BLOQUEAR OT
    # ==================================================

    orden = _bloquear_orden(
        orden_trabajo
    )

    # ==================================================
    # VALIDAR FLUJO COMERCIAL
    # ==================================================

    if not orden.requiere_aceptacion_cliente:
        raise ValidationError(
            {
                "estado_aceptacion": _(
                    "Esta orden de trabajo no requiere "
                    "aceptación comercial."
                )
            }
        )

    # ==================================================
    # VALIDAR ENVÍO
    # ==================================================

    if not orden.fecha_envio_cliente:
        raise ValidationError(
            {
                "fecha_aceptacion": _(
                    "Debe registrar el envío al cliente "
                    "antes de registrar su aceptación."
                )
            }
        )

    # ==================================================
    # VALIDAR RESPUESTA PREVIA
    # ==================================================

    if orden.usuario_aceptacion_id:
        raise ValidationError(
            {
                "usuario_aceptacion": _(
                    "La respuesta del cliente "
                    "ya fue registrada."
                )
            }
        )

    if (
        orden.estado_aceptacion
        != EstadoAceptacionOTChoices.PENDIENTE
    ):
        raise ValidationError(
            {
                "estado_aceptacion": _(
                    "La respuesta del cliente "
                    "ya fue registrada."
                )
            }
        )

    # ==================================================
    # REGISTRAR ACEPTACIÓN
    # ==================================================

    orden.estado_aceptacion = (
        EstadoAceptacionOTChoices.ACEPTADA
    )

    orden.fecha_aceptacion = (
        _resolver_fecha(
            fecha_nueva=fecha,
            fecha_existente=(
                orden.fecha_aceptacion
            ),
        )
    )

    orden.usuario_aceptacion = usuario

    # ==================================================
    # VALIDAR Y GUARDAR
    # ==================================================

    return _validar_y_guardar(
        orden,
        campos=(
            "estado_aceptacion",
            "fecha_aceptacion",
            "usuario_aceptacion",
        ),
    )


# ======================================================
# RECHAZO DEL CLIENTE
# ======================================================

@transaction.atomic
def registrar_rechazo_cliente(
    *,
    orden_trabajo: OrdenTrabajo,
    usuario: Usuario,
    fecha: datetime | None = None,
) -> OrdenTrabajo:
    """
    Registra el rechazo de la propuesta
    por parte del cliente.

    La fecha puede estar previamente cargada
    sin que el hito haya sido formalmente registrado.
    """

    # ==================================================
    # VALIDAR USUARIO
    # ==================================================

    _validar_usuario(
        usuario
    )

    # ==================================================
    # BLOQUEAR OT
    # ==================================================

    orden = _bloquear_orden(
        orden_trabajo
    )

    # ==================================================
    # VALIDAR FLUJO COMERCIAL
    # ==================================================

    if not orden.requiere_aceptacion_cliente:
        raise ValidationError(
            {
                "estado_aceptacion": _(
                    "Esta orden de trabajo no requiere "
                    "aceptación comercial."
                )
            }
        )

    # ==================================================
    # VALIDAR ENVÍO
    # ==================================================

    if not orden.fecha_envio_cliente:
        raise ValidationError(
            {
                "fecha_aceptacion": _(
                    "Debe registrar el envío al cliente "
                    "antes de registrar su respuesta."
                )
            }
        )

    # ==================================================
    # VALIDAR RESPUESTA PREVIA
    # ==================================================

    if orden.usuario_aceptacion_id:
        raise ValidationError(
            {
                "usuario_aceptacion": _(
                    "La respuesta del cliente "
                    "ya fue registrada."
                )
            }
        )

    if (
        orden.estado_aceptacion
        != EstadoAceptacionOTChoices.PENDIENTE
    ):
        raise ValidationError(
            {
                "estado_aceptacion": _(
                    "La respuesta del cliente "
                    "ya fue registrada."
                )
            }
        )

    # ==================================================
    # REGISTRAR RECHAZO
    # ==================================================

    orden.estado_aceptacion = (
        EstadoAceptacionOTChoices.RECHAZADA
    )

    orden.fecha_aceptacion = (
        _resolver_fecha(
            fecha_nueva=fecha,
            fecha_existente=(
                orden.fecha_aceptacion
            ),
        )
    )

    orden.usuario_aceptacion = usuario

    # ==================================================
    # VALIDAR Y GUARDAR
    # ==================================================

    return _validar_y_guardar(
        orden,
        campos=(
            "estado_aceptacion",
            "fecha_aceptacion",
            "usuario_aceptacion",
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

    Prioridad de fecha:

    1. fecha enviada desde el Admin;
    2. fecha previamente cargada;
    3. fecha/hora actual.

    Las OT provenientes de Proyecto o Presupuesto Telecom
    requieren aceptación previa del cliente.
    """

    # ==================================================
    # VALIDAR USUARIO
    # ==================================================

    _validar_usuario(
        usuario
    )

    # ==================================================
    # BLOQUEAR OT
    # ==================================================

    orden = _bloquear_orden(
        orden_trabajo
    )

    # ==================================================
    # VALIDAR ACEPTACIÓN
    # ==================================================

    if (
        orden.requiere_aceptacion_cliente
        and not orden.fue_aceptada
    ):
        raise ValidationError(
            {
                "estado_aceptacion": _(
                    "El cliente debe aceptar la propuesta "
                    "antes de iniciar la orden de trabajo."
                )
            }
        )

    # ==================================================
    # VALIDAR TRANSICIÓN
    # ==================================================

    _validar_transicion(
        estado_actual=orden.estado,
        nuevo_estado=(
            EstadoOrdenTrabajoChoices.EN_PROCESO
        ),
    )

    # ==================================================
    # RESOLVER FECHA
    # ==================================================

    orden.fecha_inicio = (
        _resolver_fecha(
            fecha_nueva=fecha,
            fecha_existente=orden.fecha_inicio,
        )
    )

    # ==================================================
    # REGISTRAR USUARIO Y ESTADO
    # ==================================================

    orden.usuario_inicio = usuario

    orden.estado = (
        EstadoOrdenTrabajoChoices.EN_PROCESO
    )

    # ==================================================
    # VALIDAR Y GUARDAR
    # ==================================================

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
    Pausa una OT actualmente en ejecución.

    Actualmente la OT no posee una fecha específica
    de pausa, por lo que esta operación únicamente
    modifica el estado.
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

    Actualmente la OT no posee una fecha específica
    de reanudación, por lo que esta operación únicamente
    modifica el estado.
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

    Prioridad de fecha:

    1. fecha enviada desde el Admin;
    2. fecha previamente cargada;
    3. fecha/hora actual.

    Para órdenes de tipo INSTALACION:

    - debe existir una instalación generada;
    - la instalación debe estar FINALIZADA;
    - la instalación debe tener fecha de finalización;
    - la fecha de finalización de la OT no puede ser
      anterior a la fecha de finalización de la instalación.

    La instalación y la OT representan hitos distintos:

        Instalación FINALIZADA
                ↓
        habilita Finalizar OT

    pero ambas fechas no necesariamente deben coincidir.
    """

    # ==================================================
    # VALIDAR USUARIO
    # ==================================================

    _validar_usuario(
        usuario
    )

    # ==================================================
    # BLOQUEAR OT
    # ==================================================

    orden = _bloquear_orden(
        orden_trabajo
    )

    instalacion = None

    # ==================================================
    # VALIDACIÓN DE INSTALACIÓN
    # ==================================================

    if (
        orden.tipo
        == TipoOrdenTrabajoChoices.INSTALACION
    ):

        # ----------------------------------------------
        # DEBE EXISTIR INSTALACIÓN
        # ----------------------------------------------

        if not orden.tiene_instalacion:
            raise ValidationError(
                {
                    "estado": _(
                        "No puede finalizar una orden "
                        "de tipo Instalación sin haber "
                        "generado la instalación correspondiente."
                    )
                }
            )

        instalacion = orden.instalacion

        # ----------------------------------------------
        # DEBE ESTAR FINALIZADA
        # ----------------------------------------------

        if (
            instalacion.estado
            != EstadoInstalacionChoices.FINALIZADA
        ):
            raise ValidationError(
                {
                    "estado": _(
                        "No puede finalizar la orden "
                        "de trabajo hasta que la instalación "
                        "asociada esté finalizada."
                    )
                }
            )

        # ----------------------------------------------
        # DEBE TENER FECHA DE FINALIZACIÓN
        # ----------------------------------------------

        if not instalacion.fecha_finalizacion:
            raise ValidationError(
                {
                    "fecha_finalizacion": _(
                        "La instalación está marcada como "
                        "finalizada pero no tiene registrada "
                        "su fecha de finalización."
                    )
                }
            )

    # ==================================================
    # VALIDAR TRANSICIÓN
    # ==================================================

    _validar_transicion(
        estado_actual=orden.estado,
        nuevo_estado=(
            EstadoOrdenTrabajoChoices.FINALIZADA
        ),
    )

    # ==================================================
    # RESOLVER FECHA DE FINALIZACIÓN
    # ==================================================

    fecha_finalizacion = (
        _resolver_fecha(
            fecha_nueva=fecha,
            fecha_existente=(
                orden.fecha_finalizacion
            ),
        )
    )

    # ==================================================
    # VALIDAR INSTALACIÓN → OT
    # ==================================================

    if (
        instalacion
        and instalacion.fecha_finalizacion
        and fecha_finalizacion
        < instalacion.fecha_finalizacion
    ):
        raise ValidationError(
            {
                "fecha_finalizacion": _(
                    "La fecha de finalización de la orden "
                    "de trabajo no puede ser anterior a "
                    "la fecha de finalización de la instalación "
                    "(%(fecha)s)."
                )
                % {
                    "fecha": (
                        instalacion
                        .fecha_finalizacion
                        .strftime(
                            "%d/%m/%Y %H:%M"
                        )
                    ),
                }
            }
        )

    # ==================================================
    # FINALIZAR OT
    # ==================================================

    orden.fecha_finalizacion = (
        fecha_finalizacion
    )

    orden.usuario_finalizacion = usuario

    orden.estado = (
        EstadoOrdenTrabajoChoices.FINALIZADA
    )

    # ==================================================
    # VALIDAR Y GUARDAR
    # ==================================================

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

    Una OT finalizada o ya cancelada no puede
    pasar nuevamente a CANCELADA.

    Actualmente no existe una fecha específica
    de cancelación dentro del modelo.
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
    Registra formalmente la facturación de una OT.

    Prioridad de fecha:

    1. fecha enviada desde el Admin;
    2. fecha previamente cargada;
    3. fecha/hora actual.

    fecha_facturacion representa cuándo ocurrió.

    usuario_facturacion representa quién confirmó
    formalmente el hito.

    Este servicio registra únicamente la trazabilidad.
    La creación de la factura pertenece al módulo
    de facturación.
    """

    # ==================================================
    # VALIDAR USUARIO
    # ==================================================

    _validar_usuario(
        usuario
    )

    # ==================================================
    # BLOQUEAR OT
    # ==================================================

    orden = _bloquear_orden(
        orden_trabajo
    )

    # ==================================================
    # VALIDAR HITO PREVIO
    # ==================================================

    if orden.usuario_facturacion_id:
        raise ValidationError(
            {
                "usuario_facturacion": _(
                    "La facturación de esta orden "
                    "ya fue registrada."
                )
            }
        )

    # ==================================================
    # VALIDAR ESTADO
    # ==================================================

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

    # ==================================================
    # RESOLVER FECHA
    # ==================================================

    orden.fecha_facturacion = (
        _resolver_fecha(
            fecha_nueva=fecha,
            fecha_existente=(
                orden.fecha_facturacion
            ),
        )
    )

    # ==================================================
    # REGISTRAR USUARIO
    # ==================================================

    orden.usuario_facturacion = usuario

    # ==================================================
    # VALIDAR Y GUARDAR
    # ==================================================

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
    Registra formalmente el cobro de una OT.

    Prioridad de fecha:

    1. fecha enviada desde el Admin;
    2. fecha previamente cargada;
    3. fecha/hora actual.

    fecha_cobro representa cuándo ocurrió.

    usuario_cobro representa quién confirmó
    formalmente el hito.

    Este servicio registra únicamente la trazabilidad;
    no crea movimientos financieros.
    """

    # ==================================================
    # VALIDAR USUARIO
    # ==================================================

    _validar_usuario(
        usuario
    )

    # ==================================================
    # BLOQUEAR OT
    # ==================================================

    orden = _bloquear_orden(
        orden_trabajo
    )

    # ==================================================
    # VALIDAR HITO PREVIO
    # ==================================================

    if orden.usuario_cobro_id:
        raise ValidationError(
            {
                "usuario_cobro": _(
                    "El cobro de esta orden "
                    "ya fue registrado."
                )
            }
        )

    # ==================================================
    # VALIDAR FACTURACIÓN
    # ==================================================

    if not orden.usuario_facturacion_id:
        raise ValidationError(
            {
                "fecha_cobro": _(
                    "Debe registrar formalmente la "
                    "facturación antes de registrar "
                    "el cobro."
                )
            }
        )

    if not orden.fecha_facturacion:
        raise ValidationError(
            {
                "fecha_cobro": _(
                    "La facturación registrada no posee "
                    "fecha de facturación."
                )
            }
        )

    # ==================================================
    # RESOLVER FECHA
    # ==================================================

    orden.fecha_cobro = (
        _resolver_fecha(
            fecha_nueva=fecha,
            fecha_existente=(
                orden.fecha_cobro
            ),
        )
    )

    # ==================================================
    # REGISTRAR USUARIO
    # ==================================================

    orden.usuario_cobro = usuario

    # ==================================================
    # VALIDAR Y GUARDAR
    # ==================================================

    return _validar_y_guardar(
        orden,
        campos=(
            "fecha_cobro",
            "usuario_cobro",
        ),
    )


# ======================================================
# EXPORTACIONES
# ======================================================

__all__ = (
    "registrar_recepcion_solicitud",
    "programar_orden_trabajo",
    "registrar_envio_cliente",
    "registrar_aceptacion_cliente",
    "registrar_rechazo_cliente",
    "iniciar_orden_trabajo",
    "pausar_orden_trabajo",
    "reanudar_orden_trabajo",
    "finalizar_orden_trabajo",
    "cancelar_orden_trabajo",
    "registrar_facturacion_ot",
    "registrar_cobro_ot",
)