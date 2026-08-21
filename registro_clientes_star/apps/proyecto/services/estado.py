"""
Servicios relacionados con el ciclo comercial
y operativo de los proyectos.

Centraliza:

- recepción de solicitudes;
- planificación;
- envío al cliente;
- aceptación;
- rechazo.

Las fechas pueden cargarse previamente desde el Admin.
Si ya existe una fecha, el service la conserva.
Si no existe, utiliza la fecha/hora actual cuando
corresponde.
"""

from datetime import date, datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.choices import (
    EstadoOrdenTrabajoChoices,
    EstadoProyectoChoices,
    RespuestaClienteProyectoChoices,
)

from apps.proyecto.models import Proyecto
from apps.usuarios.models import Usuario


# ======================================================
# FUNCIONES PRIVADAS
# ======================================================

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
            "de ejecutar esta operación."
        )


def _validar_usuario(
    usuario: Usuario | None,
) -> None:
    """
    Valida el usuario responsable de registrar
    una operación.
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


def _bloquear_proyecto(
    proyecto: Proyecto,
) -> Proyecto:
    """
    Recupera y bloquea el proyecto durante
    la transacción actual.
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
            "usuario_recepcion_solicitud",
            "usuario_envio_cliente",
            "usuario_respuesta_cliente",
        )
        .get(
            pk=proyecto.pk,
        )
    )


def _resolver_fecha_hora(
    *,
    nueva: datetime | None,
    existente: datetime | None,
) -> datetime:
    """
    Prioridad:

    1. fecha indicada al service;
    2. fecha previamente cargada;
    3. fecha/hora actual.
    """

    return (
        nueva
        or existente
        or timezone.now()
    )


def _resolver_fecha_planificada(
    *,
    nueva: date | None,
    existente: date | None,
) -> date:
    """
    Prioridad:

    1. fecha indicada al service;
    2. fecha previamente cargada;
    3. fecha actual.
    """

    return (
        nueva
        or existente
        or timezone.localdate()
    )

def _validar_y_guardar(
    proyecto: Proyecto,
    *,
    campos: tuple[str, ...],
) -> Proyecto:
    """
    Ejecuta las validaciones del modelo antes
    de persistir los cambios.
    """

    proyecto.full_clean()

    proyecto.save(
        update_fields=campos,
    )

    return proyecto


# ======================================================
# RECEPCIÓN
# ======================================================

@transaction.atomic
def registrar_recepcion_proyecto(
    *,
    proyecto: Proyecto,
    usuario: Usuario,
    fecha: datetime | None = None,
) -> Proyecto:
    """
    Registra la recepción de la solicitud
    que dio origen al proyecto.

    Esta operación no cambia todavía el estado.
    El proyecto permanece BORRADOR hasta ser planificado.
    """

    _validar_usuario(
        usuario
    )

    objeto = _bloquear_proyecto(
        proyecto
    )

    if objeto.usuario_recepcion_solicitud_id:
        raise ValidationError(
            {
                "usuario_recepcion_solicitud": _(
                    "La recepción de la solicitud "
                    "ya fue registrada."
                )
            }
        )

    if (
        objeto.estado
        != EstadoProyectoChoices.BORRADOR
    ):
        raise ValidationError(
            {
                "estado": _(
                    "La recepción solo puede registrarse "
                    "mientras el proyecto está en borrador."
                )
            }
        )

    objeto.fecha_recepcion_solicitud = (
        _resolver_fecha_hora(
            nueva=fecha,
            existente=(
                objeto.fecha_recepcion_solicitud
            ),
        )
    )

    objeto.usuario_recepcion_solicitud = usuario

    return _validar_y_guardar(
        objeto,
        campos=(
            "fecha_recepcion_solicitud",
            "usuario_recepcion_solicitud",
        ),
    )


# ======================================================
# PLANIFICACIÓN
# ======================================================

@transaction.atomic
def planificar_proyecto(
    *,
    proyecto: Proyecto,
    fecha_planificada: date | None = None,
) -> Proyecto:
    """
    Registra la planificación del proyecto
    y cambia su estado a PLANIFICADO.
    """

    objeto = _bloquear_proyecto(
        proyecto
    )

    if not objeto.fecha_recepcion_solicitud:
        raise ValidationError(
            {
                "fecha_recepcion_solicitud": _(
                    "Debe registrar primero la recepción "
                    "de la solicitud."
                )
            }
        )

    if (
        objeto.estado
        != EstadoProyectoChoices.BORRADOR
    ):
        raise ValidationError(
            {
                "estado": _(
                    "Solo un proyecto en borrador "
                    "puede planificarse."
                )
            }
        )

    objeto.fecha_planificada = (
        _resolver_fecha_planificada(
            nueva=fecha_planificada,
            existente=objeto.fecha_planificada,
        )
    )

    objeto.estado = (
        EstadoProyectoChoices.PLANIFICADO
    )

    return _validar_y_guardar(
        objeto,
        campos=(
            "fecha_planificada",
            "estado",
        ),
    )


# ======================================================
# ENVÍO AL CLIENTE
# ======================================================

@transaction.atomic
def registrar_envio_proyecto(
    *,
    proyecto: Proyecto,
    usuario: Usuario,
    fecha: datetime | None = None,
) -> Proyecto:
    """
    Registra el envío del proyecto al cliente.

    Después del envío el proyecto queda
    PENDIENTE_APROBACION.
    """

    _validar_usuario(
        usuario
    )

    objeto = _bloquear_proyecto(
        proyecto
    )


    if objeto.usuario_envio_cliente_id:
        raise ValidationError(
            {
                "usuario_envio_cliente": _(
                    "El envío del proyecto al cliente "
                    "ya fue registrado."
                )
            }
        )
    if not objeto.fecha_recepcion_solicitud:
        raise ValidationError(
            {
                "fecha_envio_cliente": _(
                    "Debe registrar primero la recepción "
                    "de la solicitud."
                )
            }
        )

    if (
        objeto.estado
        != EstadoProyectoChoices.PLANIFICADO
    ):
        raise ValidationError(
            {
                "estado": _(
                    "El proyecto debe estar planificado "
                    "antes de enviarlo al cliente."
                )
            }
        )

    objeto.fecha_envio_cliente = (
        _resolver_fecha_hora(
            nueva=fecha,
            existente=objeto.fecha_envio_cliente,
        )
    )

    objeto.usuario_envio_cliente = usuario

    objeto.respuesta_cliente = (
        RespuestaClienteProyectoChoices.PENDIENTE
    )

    objeto.estado = (
        EstadoProyectoChoices.PENDIENTE_APROBACION
    )

    return _validar_y_guardar(
        objeto,
        campos=(
            "fecha_envio_cliente",
            "usuario_envio_cliente",
            "respuesta_cliente",
            "estado",
        ),
    )


# ======================================================
# ACEPTACIÓN
# ======================================================

@transaction.atomic
def registrar_aceptacion_proyecto(
    *,
    proyecto: Proyecto,
    usuario: Usuario,
    fecha: datetime | None = None,
) -> Proyecto:
    """
    Registra la aceptación del proyecto
    por parte del cliente.

    El proyecto pasa automáticamente a APROBADO.
    """

    _validar_usuario(
        usuario
    )

    objeto = _bloquear_proyecto(
        proyecto
    )

    if not objeto.fecha_envio_cliente:
        raise ValidationError(
            {
                "fecha_respuesta_cliente": _(
                    "Debe registrar el envío del proyecto "
                    "antes de registrar la aceptación."
                )
            }
        )

    if (
        objeto.estado
        != EstadoProyectoChoices.PENDIENTE_APROBACION
    ):
        raise ValidationError(
            {
                "estado": _(
                    "El proyecto debe estar pendiente "
                    "de aprobación."
                )
            }
        )

    if (
        objeto.respuesta_cliente
        != RespuestaClienteProyectoChoices.PENDIENTE
    ):
        raise ValidationError(
            {
                "respuesta_cliente": _(
                    "La respuesta del cliente "
                    "ya fue registrada."
                )
            }
        )

    objeto.respuesta_cliente = (
        RespuestaClienteProyectoChoices.ACEPTADO
    )

    objeto.fecha_respuesta_cliente = (
        _resolver_fecha_hora(
            nueva=fecha,
            existente=objeto.fecha_respuesta_cliente,
        )
    )

    objeto.usuario_respuesta_cliente = usuario

    objeto.estado = (
        EstadoProyectoChoices.APROBADO
    )

    return _validar_y_guardar(
        objeto,
        campos=(
            "respuesta_cliente",
            "fecha_respuesta_cliente",
            "usuario_respuesta_cliente",
            "estado",
        ),
    )


# ======================================================
# RECHAZO
# ======================================================

@transaction.atomic
def registrar_rechazo_proyecto(
    *,
    proyecto: Proyecto,
    usuario: Usuario,
    fecha: datetime | None = None,
) -> Proyecto:
    """
    Registra el rechazo del proyecto.

    El proyecto no se cancela automáticamente.
    Permanece PENDIENTE_APROBACION para conservar
    la trazabilidad y permitir una revisión posterior.
    """

    _validar_usuario(
        usuario
    )

    objeto = _bloquear_proyecto(
        proyecto
    )

    if not objeto.fecha_envio_cliente:
        raise ValidationError(
            {
                "fecha_respuesta_cliente": _(
                    "Debe registrar el envío del proyecto "
                    "antes de registrar el rechazo."
                )
            }
        )

    if (
        objeto.estado
        != EstadoProyectoChoices.PENDIENTE_APROBACION
    ):
        raise ValidationError(
            {
                "estado": _(
                    "El proyecto debe estar pendiente "
                    "de aprobación."
                )
            }
        )

    if (
        objeto.respuesta_cliente
        != RespuestaClienteProyectoChoices.PENDIENTE
    ):
        raise ValidationError(
            {
                "respuesta_cliente": _(
                    "La respuesta del cliente "
                    "ya fue registrada."
                )
            }
        )

    objeto.respuesta_cliente = (
        RespuestaClienteProyectoChoices.RECHAZADO
    )

    objeto.fecha_respuesta_cliente = (
        _resolver_fecha_hora(
            nueva=fecha,
            existente=objeto.fecha_respuesta_cliente,
        )
    )

    objeto.usuario_respuesta_cliente = usuario

    return _validar_y_guardar(
        objeto,
        campos=(
            "respuesta_cliente",
            "fecha_respuesta_cliente",
            "usuario_respuesta_cliente",
        ),
    )

# ======================================================
# FINALIZACIÓN DEL PROYECTO
# ======================================================

@transaction.atomic
def finalizar_proyecto(
    *,
    proyecto: Proyecto,
    fecha_finalizacion: date | None = None,
) -> Proyecto:
    """
    Finaliza formalmente un Proyecto.

    Reglas:

    - el Proyecto debe estar guardado;
    - debe estar APROBADO o EN_EJECUCION;
    - debe tener al menos una OrdenTrabajo;
    - todas sus OT deben estar FINALIZADA o CANCELADA;
    - toda OT FINALIZADA debe poseer fecha_finalizacion;
    - el Proyecto debe tener fecha_inicio;
    - la fecha_finalizacion del Proyecto no puede ser
      anterior a la última OT finalizada.

    Finalizar una OT NO finaliza automáticamente
    el Proyecto. Esta operación representa un hito
    independiente.
    """

    # ==================================================
    # BLOQUEAR PROYECTO
    # ==================================================

    objeto = _bloquear_proyecto(
        proyecto
    )

    # ==================================================
    # VALIDAR ESTADO DEL PROYECTO
    # ==================================================

    estados_permitidos = {
        EstadoProyectoChoices.APROBADO,
        EstadoProyectoChoices.EN_EJECUCION,
    }

    if objeto.estado not in estados_permitidos:
        raise ValidationError(
            {
                "estado": _(
                    "El proyecto debe estar aprobado "
                    "o en ejecución para poder finalizarlo."
                )
            }
        )

    # ==================================================
    # VALIDAR FECHA DE INICIO
    # ==================================================

    if not objeto.fecha_inicio:
        raise ValidationError(
            {
                "fecha_inicio": _(
                    "Debe registrar la fecha de inicio "
                    "del proyecto antes de finalizarlo."
                )
            }
        )

    # ==================================================
    # BLOQUEAR ÓRDENES DE TRABAJO
    # ==================================================

    ordenes = list(
        objeto.ordenes_trabajo
        .select_for_update()
        .only(
            "id",
            "codigo",
            "estado",
            "fecha_inicio",
            "fecha_finalizacion",
        )
        .order_by(
            "id"
        )
    )

    # ==================================================
    # VALIDAR EXISTENCIA DE OT
    # ==================================================

    if not ordenes:
        raise ValidationError(
            {
                "estado": _(
                    "No se puede finalizar el proyecto "
                    "porque todavía no tiene órdenes "
                    "de trabajo."
                )
            }
        )

    # ==================================================
    # VALIDAR QUE TODAS LAS OT ESTÉN CERRADAS
    # ==================================================

    estados_ot_cerrada = {
        EstadoOrdenTrabajoChoices.FINALIZADA,
        EstadoOrdenTrabajoChoices.CANCELADA,
    }

    ordenes_abiertas = [
        orden
        for orden in ordenes
        if orden.estado not in estados_ot_cerrada
    ]

    if ordenes_abiertas:
        codigos = ", ".join(
            orden.codigo
            for orden in ordenes_abiertas
        )

        raise ValidationError(
            {
                "estado": _(
                    "No se puede finalizar el proyecto "
                    "porque existen órdenes de trabajo "
                    "que todavía no están cerradas: %(ordenes)s."
                )
                % {
                    "ordenes": codigos,
                }
            }
        )

    # ==================================================
    # VALIDAR FECHAS DE OT FINALIZADAS
    # ==================================================

    ordenes_finalizadas_sin_fecha = [
        orden
        for orden in ordenes
        if (
            orden.estado
            == EstadoOrdenTrabajoChoices.FINALIZADA
            and not orden.fecha_finalizacion
        )
    ]

    if ordenes_finalizadas_sin_fecha:
        codigos = ", ".join(
            orden.codigo
            for orden in ordenes_finalizadas_sin_fecha
        )

        raise ValidationError(
            {
                "fecha_finalizacion": _(
                    "Existen órdenes finalizadas sin fecha "
                    "de finalización: %(ordenes)s."
                )
                % {
                    "ordenes": codigos,
                }
            }
        )

    # ==================================================
    # OBTENER ÚLTIMA FECHA DE FINALIZACIÓN DE OT
    # ==================================================

    fechas_ot_finalizadas = [
        orden.fecha_finalizacion.date()
        for orden in ordenes
        if (
            orden.estado
            == EstadoOrdenTrabajoChoices.FINALIZADA
            and orden.fecha_finalizacion
        )
    ]

    ultima_fecha_ot = (
        max(fechas_ot_finalizadas)
        if fechas_ot_finalizadas
        else None
    )

    # ==================================================
    # RESOLVER FECHA DE FINALIZACIÓN DEL PROYECTO
    # ==================================================

    fecha_resuelta = (
        fecha_finalizacion
        or objeto.fecha_finalizacion
        or timezone.localdate()
    )

    # ==================================================
    # VALIDAR CRONOLOGÍA
    # ==================================================

    if (
        ultima_fecha_ot
        and fecha_resuelta < ultima_fecha_ot
    ):
        raise ValidationError(
            {
                "fecha_finalizacion": _(
                    "La fecha de finalización del proyecto "
                    "no puede ser anterior a la última orden "
                    "de trabajo finalizada (%(fecha)s)."
                )
                % {
                    "fecha": ultima_fecha_ot.strftime(
                        "%d/%m/%Y"
                    ),
                }
            }
        )

    # ==================================================
    # FINALIZAR PROYECTO
    # ==================================================

    objeto.fecha_finalizacion = (
        fecha_resuelta
    )

    objeto.estado = (
        EstadoProyectoChoices.FINALIZADO
    )

    # ==================================================
    # VALIDAR Y GUARDAR
    # ==================================================

    return _validar_y_guardar(
        objeto,
        campos=(
            "fecha_finalizacion",
            "estado",
        ),
    )

__all__ = (
    "registrar_recepcion_proyecto",
    "planificar_proyecto",
    "registrar_envio_proyecto",
    "registrar_aceptacion_proyecto",
    "registrar_rechazo_proyecto",
    "finalizar_proyecto",
)