"""
Servicios relacionados con el ciclo de vida
de las instalaciones.

Centraliza:

- programación;
- inicio;
- finalización;
- cancelación;
- conformidad del cliente.

Las operaciones se ejecutan dentro de transacciones
atómicas y respetan las validaciones del modelo.
"""

from datetime import date, datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.choices import (
    EstadoDispositivoInstaladoChoices,
    EstadoInstalacionChoices,
)

from apps.instalacion.models import Instalacion


# ======================================================
# TRANSICIONES
# ======================================================

TRANSICIONES_ESTADO = {
    EstadoInstalacionChoices.PENDIENTE: {
        EstadoInstalacionChoices.PROGRAMADA,
        EstadoInstalacionChoices.EN_PROCESO,
        EstadoInstalacionChoices.CANCELADA,
    },

    EstadoInstalacionChoices.PROGRAMADA: {
        EstadoInstalacionChoices.EN_PROCESO,
        EstadoInstalacionChoices.CANCELADA,
    },

    EstadoInstalacionChoices.EN_PROCESO: {
        EstadoInstalacionChoices.FINALIZADA,
        EstadoInstalacionChoices.CANCELADA,
    },

    EstadoInstalacionChoices.FINALIZADA: set(),

    EstadoInstalacionChoices.CANCELADA: set(),
}


# ======================================================
# FUNCIONES PRIVADAS
# ======================================================

def _validar_instalacion_guardada(
    instalacion: Instalacion | None,
) -> None:
    """
    Valida que exista una instalación persistida.
    """

    if instalacion is None:
        raise ValueError(
            "Debe proporcionar una instalación válida."
        )

    if not instalacion.pk:
        raise ValueError(
            "La instalación debe estar guardada antes "
            "de ejecutar esta operación."
        )


def _bloquear_instalacion(
    instalacion: Instalacion,
) -> Instalacion:
    """
    Recupera y bloquea la instalación durante
    la transacción actual.
    """

    _validar_instalacion_guardada(
        instalacion
    )

    return (
        Instalacion.objects
        .select_for_update()
        .select_related(
            "orden_trabajo",
        )
        .get(
            pk=instalacion.pk,
        )
    )


def _validar_transicion(
    *,
    estado_actual: str,
    nuevo_estado: str,
) -> None:
    """
    Valida una transición del ciclo de vida.
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
                    "No se puede cambiar la instalación de "
                    "%(actual)s a %(nuevo)s."
                )
                % {
                    "actual": estado_actual,
                    "nuevo": nuevo_estado,
                }
            }
        )


def _resolver_fecha_hora(
    *,
    fecha_nueva: datetime | None,
    fecha_existente: datetime | None,
) -> datetime:
    """
    Prioridad:

    1. fecha proporcionada;
    2. fecha existente;
    3. fecha/hora actual.
    """

    return (
        fecha_nueva
        or fecha_existente
        or timezone.now()
    )


def _validar_y_guardar(
    instalacion: Instalacion,
    *,
    campos: tuple[str, ...],
) -> Instalacion:
    """
    Ejecuta full_clean() y guarda únicamente
    los campos modificados.
    """

    instalacion.full_clean()

    instalacion.save(
        update_fields=campos,
    )

    return instalacion

def _validar_dispositivos_para_finalizacion(
    instalacion: Instalacion,
) -> None:
    """
    Valida que los dispositivos físicos asociados
    estén correctamente registrados antes de finalizar
    la instalación.

    Reglas:
    - debe existir al menos un dispositivo;
    - todos deben tener ubicación;
    - todos deben tener un estado técnico definido.

    Los estados válidos son los definidos por
    EstadoDispositivoInstaladoChoices:
    INSTALADO, RETIRADO, REEMPLAZADO y FUERA_SERVICIO.
    """

    dispositivos = list(
        instalacion.dispositivos.all()
    )

    if not dispositivos:
        raise ValidationError(
            {
                "dispositivos": _(
                    "La instalación debe tener al menos "
                    "un dispositivo registrado antes "
                    "de poder finalizarse."
                )
            }
        )

    sin_ubicacion = [
        dispositivo
        for dispositivo in dispositivos
        if not (dispositivo.ubicacion or "").strip()
    ]

    if sin_ubicacion:
        codigos = ", ".join(
            dispositivo.codigo
            for dispositivo in sin_ubicacion
        )

        raise ValidationError(
            {
                "dispositivos": _(
                    "Todos los dispositivos deben tener "
                    "una ubicación antes de finalizar "
                    "la instalación. "
                    "Dispositivos pendientes: %(codigos)s."
                )
                % {
                    "codigos": codigos,
                }
            }
        )

    estados_validos = {
        choice.value
        for choice
        in EstadoDispositivoInstaladoChoices
    }

    estado_invalido = [
        dispositivo
        for dispositivo in dispositivos
        if dispositivo.estado not in estados_validos
    ]

    if estado_invalido:
        codigos = ", ".join(
            dispositivo.codigo
            for dispositivo in estado_invalido
        )

        raise ValidationError(
            {
                "dispositivos": _(
                    "Existen dispositivos con un estado "
                    "técnico inválido. "
                    "Dispositivos: %(codigos)s."
                )
                % {
                    "codigos": codigos,
                }
            }
        )
def _validar_tecnicos_para_finalizacion(
    instalacion: Instalacion,
) -> None:
    """
    Valida la asignación técnica antes de finalizar
    una instalación.

    Reglas:

    - debe existir al menos un técnico asignado;
    - debe existir exactamente un responsable principal.
    """

    tecnicos = instalacion.tecnicos.all()

    if not tecnicos.exists():
        raise ValidationError(
            {
                "tecnicos": _(
                    "La instalación debe tener al menos "
                    "un técnico asignado antes de finalizarse."
                )
            }
        )

    cantidad_responsables = tecnicos.filter(
        es_responsable=True,
    ).count()

    if cantidad_responsables == 0:
        raise ValidationError(
            {
                "tecnicos": _(
                    "Debe asignar un técnico responsable "
                    "antes de finalizar la instalación."
                )
            }
        )

    if cantidad_responsables > 1:
        raise ValidationError(
            {
                "tecnicos": _(
                    "La instalación no puede tener más "
                    "de un técnico responsable."
                )
            }
        )

# ======================================================
# PROGRAMACIÓN
# ======================================================

@transaction.atomic
def programar_instalacion(
    *,
    instalacion: Instalacion,
    fecha_programada: date | None = None,
    duracion_estimada: timedelta | None = None,
) -> Instalacion:
    """
    Programa una instalación existente.
    """

    objeto = _bloquear_instalacion(
        instalacion
    )

    fecha = (
        fecha_programada
        or objeto.fecha_programada
    )

    if fecha is None:
        raise ValidationError(
            {
                "fecha_programada": _(
                    "Debe indicar una fecha programada."
                )
            }
        )

    _validar_transicion(
        estado_actual=objeto.estado,
        nuevo_estado=(
            EstadoInstalacionChoices.PROGRAMADA
        ),
    )

    objeto.fecha_programada = fecha

    campos = [
        "fecha_programada",
        "estado",
    ]

    if duracion_estimada is not None:
        objeto.duracion_estimada = duracion_estimada

        campos.append(
            "duracion_estimada"
        )

    objeto.estado = (
        EstadoInstalacionChoices.PROGRAMADA
    )

    return _validar_y_guardar(
        objeto,
        campos=tuple(campos),
    )


# ======================================================
# INICIO
# ======================================================

@transaction.atomic
def iniciar_instalacion(
    *,
    instalacion: Instalacion,
    fecha: datetime | None = None,
) -> Instalacion:
    """
    Registra el inicio real de una instalación.
    """

    objeto = _bloquear_instalacion(
        instalacion
    )

    _validar_transicion(
        estado_actual=objeto.estado,
        nuevo_estado=(
            EstadoInstalacionChoices.EN_PROCESO
        ),
    )

    objeto.fecha_inicio = (
        _resolver_fecha_hora(
            fecha_nueva=fecha,
            fecha_existente=objeto.fecha_inicio,
        )
    )

    objeto.estado = (
        EstadoInstalacionChoices.EN_PROCESO
    )

    return _validar_y_guardar(
        objeto,
        campos=(
            "fecha_inicio",
            "estado",
        ),
    )


# ======================================================
# FINALIZACIÓN
# ======================================================

@transaction.atomic
def finalizar_instalacion(
    *,
    instalacion: Instalacion,
    fecha: datetime | None = None,
) -> Instalacion:
    """
    Finaliza una instalación en ejecución.
    """

    objeto = _bloquear_instalacion(
        instalacion
    )

    # Validaciones existentes...
    _validar_transicion(
        estado_actual=objeto.estado,
        nuevo_estado=(
            EstadoInstalacionChoices.FINALIZADA
        ),
    )

    objeto.fecha_finalizacion = (
        _resolver_fecha_hora(
            fecha_nueva=fecha,
            fecha_existente=(
                objeto.fecha_finalizacion
            ),
        )
    )

    objeto.estado = (
        EstadoInstalacionChoices.FINALIZADA
    )

    # Nueva validación técnica
    _validar_dispositivos_para_finalizacion(
        objeto # instalacion
    )
    _validar_tecnicos_para_finalizacion(
        objeto
    )

    return _validar_y_guardar(
        objeto,
        campos=(
            "fecha_finalizacion",
            "estado",
        ),
    )


# ======================================================
# CANCELACIÓN
# ======================================================

@transaction.atomic
def cancelar_instalacion(
    *,
    instalacion: Instalacion,
) -> Instalacion:
    """
    Cancela una instalación que todavía
    no fue finalizada.
    """

    objeto = _bloquear_instalacion(
        instalacion
    )

    _validar_transicion(
        estado_actual=objeto.estado,
        nuevo_estado=(
            EstadoInstalacionChoices.CANCELADA
        ),
    )

    objeto.estado = (
        EstadoInstalacionChoices.CANCELADA
    )

    return _validar_y_guardar(
        objeto,
        campos=(
            "estado",
        ),
    )


# ======================================================
# CONFORMIDAD
# ======================================================

@transaction.atomic
def registrar_conformidad_instalacion(
    *,
    instalacion: Instalacion,
    recibido_por: str,
    fecha: datetime | None = None,
    observaciones: str = "",
) -> Instalacion:
    """
    Registra la conformidad del cliente.

    La instalación debe estar finalizada.
    """

    objeto = _bloquear_instalacion(
        instalacion
    )

    if not objeto.finalizada:
        raise ValidationError(
            {
                "fecha_conformidad": _(
                    "Debe finalizar la instalación antes "
                    "de registrar la conformidad."
                )
            }
        )

    nombre = (
        recibido_por
        or ""
    ).strip()

    if not nombre:
        raise ValidationError(
            {
                "recibido_por": _(
                    "Debe indicar quién recibió "
                    "la instalación."
                )
            }
        )

    objeto.recibido_por = nombre

    objeto.fecha_conformidad = (
        _resolver_fecha_hora(
            fecha_nueva=fecha,
            fecha_existente=(
                objeto.fecha_conformidad
            ),
        )
    )

    objeto.observaciones_conformidad = (
        observaciones
        or ""
    ).strip()

    return _validar_y_guardar(
        objeto,
        campos=(
            "recibido_por",
            "fecha_conformidad",
            "observaciones_conformidad",
        ),
    )


__all__ = (
    "programar_instalacion",
    "iniciar_instalacion",
    "finalizar_instalacion",
    "cancelar_instalacion",
    "registrar_conformidad_instalacion",
)