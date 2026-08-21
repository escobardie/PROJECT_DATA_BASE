"""
Servicios para generar instalaciones
a partir de órdenes de trabajo.

Una Instalacion generada desde una OrdenTrabajo
hereda los datos operativos necesarios de la OT:

- prioridad;
- fecha programada;
- observaciones;
- técnicos asignados;
- técnico principal como responsable.

Proyecto, sucursal, servicio contratado y presupuesto
Telecom no se duplican en Instalacion, ya que pueden
obtenerse mediante la relación con OrdenTrabajo.
"""

from datetime import date, datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.choices import (
    EstadoInstalacionChoices,
    EstadoOrdenTrabajoChoices,
    PrioridadInstalacionChoices,
    PrioridadOrdenTrabajoChoices,
    RolTecnicoInstalacionChoices,
    TipoOrdenTrabajoChoices,
)

from apps.instalacion.models import (
    Instalacion,
    InstalacionTecnico,
)

from apps.orden_trabajo.models import (
    OrdenTrabajo,
)


# ======================================================
# MAPEO DE PRIORIDADES
# ======================================================

MAPEO_PRIORIDAD_OT_INSTALACION = {
    PrioridadOrdenTrabajoChoices.BAJA: (
        PrioridadInstalacionChoices.NORMAL
    ),
    PrioridadOrdenTrabajoChoices.MEDIA: (
        PrioridadInstalacionChoices.NORMAL
    ),
    PrioridadOrdenTrabajoChoices.ALTA: (
        PrioridadInstalacionChoices.ALTA
    ),
    PrioridadOrdenTrabajoChoices.URGENTE: (
        PrioridadInstalacionChoices.URGENTE
    ),
}


# ======================================================
# VALIDACIONES GENERALES
# ======================================================

def _validar_orden_guardada(
    orden_trabajo: OrdenTrabajo | None,
) -> None:
    """
    Valida que exista una OrdenTrabajo persistida.
    """

    if orden_trabajo is None:
        raise ValueError(
            "Debe proporcionar una orden de trabajo válida."
        )

    if not orden_trabajo.pk:
        raise ValueError(
            "La orden de trabajo debe estar guardada "
            "antes de generar una instalación."
        )


# ======================================================
# BLOQUEO DE OT
# ======================================================

def _bloquear_orden(
    orden_trabajo: OrdenTrabajo,
) -> OrdenTrabajo:
    """
    Recupera y bloquea la OT durante la transacción.

    Esto evita que dos operaciones intenten generar
    simultáneamente una instalación desde la misma OT.
    """

    _validar_orden_guardada(
        orden_trabajo
    )

    try:
        return (
            OrdenTrabajo.objects
            .select_for_update()
            .select_related(
                "proyecto",
                "servicio_contratado",
                "presupuesto_telecom",
                "sucursal",
                "responsable",
            )
            .get(
                pk=orden_trabajo.pk,
            )
        )

    except OrdenTrabajo.DoesNotExist as exc:
        raise ValidationError(
            {
                "orden_trabajo": _(
                    "La orden de trabajo indicada "
                    "ya no existe."
                )
            }
        ) from exc


# ======================================================
# PRIORIDAD
# ======================================================

def _resolver_prioridad_instalacion(
    orden: OrdenTrabajo,
):
    """
    Convierte la prioridad de OrdenTrabajo
    a la prioridad equivalente de Instalacion.
    """

    try:
        return MAPEO_PRIORIDAD_OT_INSTALACION[
            orden.prioridad
        ]

    except KeyError as exc:
        raise ValidationError(
            {
                "prioridad": _(
                    "La prioridad de la orden de trabajo "
                    "no puede convertirse a una prioridad "
                    "de instalación."
                )
            }
        ) from exc


# ======================================================
# FECHA PROGRAMADA
# ======================================================

def _convertir_a_fecha(
    valor: date | datetime,
) -> date:
    """
    Convierte DateTime a Date.

    Si el DateTime posee zona horaria, primero
    lo convierte a la zona horaria local configurada
    en Django.
    """

    if isinstance(
        valor,
        datetime,
    ):
        if timezone.is_aware(
            valor
        ):
            valor = timezone.localtime(
                valor
            )

        return valor.date()

    return valor


def _resolver_fecha_programada(
    *,
    orden: OrdenTrabajo,
    fecha_programada: date | datetime | None = None,
) -> date:
    """
    Resuelve la fecha programada de la instalación.

    Prioridad:

    1. fecha indicada explícitamente;
    2. fecha_programada de la OT.

    No utiliza automáticamente la fecha actual.
    """

    if fecha_programada is not None:
        return _convertir_a_fecha(
            fecha_programada
        )

    if orden.fecha_programada is not None:
        return _convertir_a_fecha(
            orden.fecha_programada
        )

    raise ValidationError(
        {
            "fecha_programada": _(
                "Debe indicar una fecha programada "
                "para generar la instalación."
            )
        }
    )


# ======================================================
# REQUISITOS OPERATIVOS
# ======================================================

def _validar_requisitos_previos_instalacion(
    orden: OrdenTrabajo,
) -> None:
    """
    Valida los requisitos operativos necesarios
    para generar la instalación.

    Requisitos:

    - al menos un técnico activo;
    - exactamente un técnico principal;
    - al menos un seguimiento activo.

    Se informan todos los faltantes juntos.
    """

    errores = []

    # ==================================================
    # TÉCNICOS
    # ==================================================

    tecnicos = (
        orden.tecnicos
        .filter(
            is_active=True,
        )
    )

    if not tecnicos.exists():
        errores.append(
            _(
                "Debe asignar al menos un técnico "
                "a la orden de trabajo."
            )
        )

    else:
        cantidad_principales = (
            tecnicos
            .filter(
                es_principal=True,
            )
            .count()
        )

        if cantidad_principales == 0:
            errores.append(
                _(
                    "Debe indicar un técnico principal "
                    "para la orden de trabajo."
                )
            )

        elif cantidad_principales > 1:
            errores.append(
                _(
                    "La orden de trabajo tiene más de "
                    "un técnico principal."
                )
            )

    # ==================================================
    # SEGUIMIENTOS
    # ==================================================

    if not (
        orden.seguimientos
        .filter(
            is_active=True,
        )
        .exists()
    ):
        errores.append(
            _(
                "Debe registrar al menos un seguimiento "
                "de la orden de trabajo."
            )
        )

    # ==================================================
    # RESULTADO
    # ==================================================

    if errores:
        raise ValidationError(
            {
                "orden_trabajo": errores,
            }
        )


# ======================================================
# IMPORTAR TÉCNICOS DE LA OT
# ======================================================

def _crear_tecnicos_instalacion_desde_ot(
    *,
    orden: OrdenTrabajo,
    instalacion: Instalacion,
) -> None:
    """
    Copia los técnicos activos asignados a la OT
    hacia la nueva Instalacion.

    El técnico principal de la OT pasa a ser:

        rol = RESPONSABLE
        es_responsable = True

    Los demás técnicos pasan a ser:

        rol = AYUDANTE
        es_responsable = False

    SUPERVISOR no se asigna automáticamente porque
    OrdenTrabajoTecnico no posee un dato equivalente.
    """

    asignaciones = (
        orden.tecnicos
        .filter(
            is_active=True,
        )
        .select_related(
            "tecnico",
        )
        .order_by(
            "-es_principal",
            "id",
        )
    )

    for asignacion in asignaciones:

        if asignacion.es_principal:
            rol = (
                RolTecnicoInstalacionChoices.RESPONSABLE
            )

        else:
            rol = (
                RolTecnicoInstalacionChoices.AYUDANTE
            )

        tecnico_instalacion = InstalacionTecnico(
            instalacion=instalacion,
            usuario=asignacion.tecnico,
            rol=rol,
            es_responsable=(
                asignacion.es_principal
            ),
        )

        tecnico_instalacion.full_clean()

        tecnico_instalacion.save()


# ======================================================
# CREAR INSTALACIÓN DESDE OT
# ======================================================

@transaction.atomic
def crear_instalacion_desde_ot(
    *,
    orden_trabajo: OrdenTrabajo,
    fecha_programada: date | datetime | None = None,
) -> Instalacion:
    """
    Genera una Instalacion desde una OrdenTrabajo.

    Requisitos:

    - la OT debe estar guardada;
    - debe ser de tipo INSTALACION;
    - debe estar EN_PROCESO;
    - debe tener un origen válido;
    - debe contar con aprobación comercial
      cuando corresponda;
    - debe tener al menos un técnico activo;
    - debe tener exactamente un técnico principal;
    - debe tener al menos un seguimiento activo;
    - no debe existir previamente una instalación;
    - debe existir fecha programada.

    Datos heredados:

    - prioridad;
    - fecha programada;
    - observaciones;
    - técnicos;
    - técnico principal / responsable.

    La Instalacion comienza en estado PENDIENTE.

    Generar la Instalacion no modifica automáticamente
    el estado de la OrdenTrabajo.
    """

    # ==================================================
    # VALIDACIÓN INICIAL
    # ==================================================

    _validar_orden_guardada(
        orden_trabajo
    )

    # ==================================================
    # BLOQUEAR OT
    # ==================================================

    orden = _bloquear_orden(
        orden_trabajo
    )

    # ==================================================
    # VALIDAR TIPO
    # ==================================================

    if (
        orden.tipo
        != TipoOrdenTrabajoChoices.INSTALACION
    ):
        raise ValidationError(
            {
                "tipo": _(
                    "Solo una orden de trabajo "
                    "de tipo Instalación puede generar "
                    "una instalación."
                )
            }
        )

    # ==================================================
    # VALIDAR ESTADO
    # ==================================================

    if (
        orden.estado
        != EstadoOrdenTrabajoChoices.EN_PROCESO
    ):
        raise ValidationError(
            {
                "estado": _(
                    "La orden de trabajo debe estar "
                    "en proceso para poder generar "
                    "una instalación."
                )
            }
        )

    # ==================================================
    # VALIDAR ORIGEN
    # ==================================================

    tiene_origen = bool(
        orden.proyecto_id
        or orden.servicio_contratado_id
        or orden.presupuesto_telecom_id
    )

    if not tiene_origen:
        raise ValidationError(
            {
                "orden_trabajo": _(
                    "La orden de trabajo debe estar "
                    "relacionada con un proyecto, "
                    "servicio contratado o presupuesto "
                    "Telecom antes de generar "
                    "una instalación."
                )
            }
        )

    # ==================================================
    # VALIDAR APROBACIÓN COMERCIAL
    # ==================================================

    if (
        orden.requiere_aceptacion_cliente
        and not orden.fue_aceptada
    ):
        raise ValidationError(
            {
                "estado_aceptacion": _(
                    "La orden de trabajo requiere "
                    "la aceptación del cliente antes "
                    "de generar la instalación."
                )
            }
        )

    # ==================================================
    # VALIDAR INSTALACIÓN EXISTENTE
    # ==================================================

    if orden.tiene_instalacion:
        raise ValidationError(
            {
                "orden_trabajo": _(
                    "La orden de trabajo ya tiene "
                    "una instalación generada."
                )
            }
        )

    # ==================================================
    # VALIDAR TÉCNICOS Y SEGUIMIENTO
    # ==================================================

    _validar_requisitos_previos_instalacion(
        orden
    )

    # ==================================================
    # RESOLVER FECHA
    # ==================================================

    fecha_programada_resuelta = (
        _resolver_fecha_programada(
            orden=orden,
            fecha_programada=fecha_programada,
        )
    )

    # ==================================================
    # RESOLVER PRIORIDAD
    # ==================================================

    prioridad_instalacion = (
        _resolver_prioridad_instalacion(
            orden
        )
    )

    # ==================================================
    # CREAR INSTALACIÓN
    # ==================================================

    instalacion = Instalacion(

        # ----------------------------------------------
        # ORIGEN
        # ----------------------------------------------

        orden_trabajo=orden,

        # ----------------------------------------------
        # CLASIFICACIÓN
        # ----------------------------------------------

        prioridad=prioridad_instalacion,

        estado=(
            EstadoInstalacionChoices.PENDIENTE
        ),

        # ----------------------------------------------
        # PLANIFICACIÓN
        # ----------------------------------------------

        fecha_programada=(
            fecha_programada_resuelta
        ),

        # ----------------------------------------------
        # OBSERVACIONES
        # ----------------------------------------------

        observaciones=(
            orden.observaciones
            or ""
        ),
    )

    # ==================================================
    # VALIDAR INSTALACIÓN
    # ==================================================

    instalacion.full_clean()

    # ==================================================
    # GUARDAR INSTALACIÓN
    # ==================================================

    instalacion.save()

    # ==================================================
    # IMPORTAR TÉCNICOS
    # ==================================================

    _crear_tecnicos_instalacion_desde_ot(
        orden=orden,
        instalacion=instalacion,
    )

    return instalacion


# ======================================================
# EXPORTS
# ======================================================

__all__ = (
    "crear_instalacion_desde_ot",
)