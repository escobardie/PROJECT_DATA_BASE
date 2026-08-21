from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.orden_trabajo.models import (
    OrdenTrabajo,
    OrdenTrabajoArchivo,
)

from apps.usuarios.models import Usuario


# ======================================================
# VALIDACIONES INTERNAS
# ======================================================


def _validar_orden_guardada(
    orden_trabajo: OrdenTrabajo,
) -> None:
    """
    Verifica que la Orden de Trabajo exista
    físicamente en la base de datos.

    Los archivos solamente pueden gestionarse
    sobre una OT previamente guardada.
    """

    if (
        orden_trabajo is None
        or not orden_trabajo.pk
    ):
        raise ValidationError(
            _(
                "La orden de trabajo debe estar "
                "guardada antes de gestionar archivos."
            )
        )


def _validar_usuario(
    usuario: Usuario,
) -> None:
    """
    Verifica que el usuario que ejecuta
    la operación exista y se encuentre activo.
    """

    if (
        usuario is None
        or not usuario.pk
    ):
        raise ValidationError(
            _(
                "Debe indicar el usuario que realiza "
                "la operación."
            )
        )

    if not usuario.is_active:
        raise ValidationError(
            _(
                "El usuario que realiza la operación "
                "no se encuentra activo."
            )
        )


def _validar_archivo_guardado(
    archivo_ot: OrdenTrabajoArchivo,
) -> None:
    """
    Verifica que el registro documental
    exista físicamente en la base de datos.
    """

    if (
        archivo_ot is None
        or not archivo_ot.pk
    ):
        raise ValidationError(
            _(
                "El archivo de la orden de trabajo "
                "debe estar guardado."
            )
        )


# ======================================================
# FECHAS
# ======================================================


def _resolver_fecha_hora(
    *,
    fecha_explicita=None,
    fecha_existente=None,
):
    """
    Resuelve una fecha/hora utilizando
    la regla general utilizada en el proyecto:

        1. fecha proporcionada explícitamente;
        2. fecha ya existente;
        3. fecha/hora actual.

    Esta regla permite registrar acontecimientos
    históricos sin perder la fecha real de carga.
    """

    return (
        fecha_explicita
        or fecha_existente
        or timezone.now()
    )


# ======================================================
# BLOQUEOS
# ======================================================


def _bloquear_orden(
    orden_trabajo: OrdenTrabajo,
) -> OrdenTrabajo:
    """
    Recupera y bloquea la Orden de Trabajo
    durante la transacción actual.

    Evita que dos operaciones concurrentes
    modifiquen información relacionada con la OT
    al mismo tiempo.
    """

    return (
        OrdenTrabajo.objects
        .select_for_update()
        .get(
            pk=orden_trabajo.pk,
        )
    )


def _bloquear_archivo(
    archivo_ot: OrdenTrabajoArchivo,
) -> OrdenTrabajoArchivo:
    """
    Recupera y bloquea un archivo de OT
    durante la transacción actual.
    """

    return (
        OrdenTrabajoArchivo.objects
        .select_for_update()
        .select_related(
            "orden_trabajo",
            "usuario",
            "usuario_retiro",
        )
        .get(
            pk=archivo_ot.pk,
        )
    )


# ======================================================
# REGLAS DOCUMENTALES
# ======================================================


def _validar_gestion_documental(
    orden_trabajo: OrdenTrabajo,
) -> None:
    """
    Valida que la Orden de Trabajo permita
    operaciones documentales.

    Regla funcional:

    - OT activa:
        permite documentación.

    - OT finalizada:
        permite documentación posterior,
        por ejemplo:
            * actas;
            * informes;
            * conformidades;
            * evidencias;
            * documentación administrativa.

    - OT cancelada:
        no permite nuevas operaciones documentales.

    IMPORTANTE:
    El valor "CANCELADA" corresponde al valor funcional
    utilizado actualmente por los estados de OT.
    """

    if orden_trabajo.estado == "CANCELADA":
        raise ValidationError(
            _(
                "No se pueden gestionar archivos "
                "en una orden de trabajo cancelada."
            )
        )


# ======================================================
# NORMALIZACIÓN
# ======================================================


def _normalizar_descripcion(
    descripcion: str,
) -> str:
    """
    Normaliza la descripción del archivo.
    """

    return (
        descripcion
        or ""
    ).strip()


def _normalizar_motivo(
    motivo: str,
) -> str:
    """
    Normaliza y valida el motivo utilizado
    para retirar un archivo.
    """

    motivo = (
        motivo
        or ""
    ).strip()

    if not motivo:
        raise ValidationError(
            {
                "motivo_retiro": _(
                    "Debe indicar el motivo por el cual "
                    "se retira el archivo."
                )
            }
        )

    return motivo


# ======================================================
# VALIDACIÓN DEL ARCHIVO SUBIDO
# ======================================================


def _validar_archivo_subido(
    archivo,
) -> None:
    """
    Realiza las validaciones básicas sobre
    el archivo recibido.

    Por ahora se verifica:

    - existencia del archivo;
    - que no sea un archivo vacío.

    Las restricciones de tamaño máximo,
    extensiones o tipos MIME pueden incorporarse
    posteriormente como política documental.
    """

    if not archivo:
        raise ValidationError(
            {
                "archivo": _(
                    "Debe seleccionar un archivo."
                )
            }
        )

    tamanio = getattr(
        archivo,
        "size",
        None,
    )

    if tamanio == 0:
        raise ValidationError(
            {
                "archivo": _(
                    "El archivo seleccionado está vacío."
                )
            }
        )


# ======================================================
# ADJUNTAR ARCHIVO
# ======================================================


@transaction.atomic
def adjuntar_archivo_ot(
    *,
    orden_trabajo: OrdenTrabajo,
    usuario: Usuario,
    archivo,
    descripcion: str = "",
    fecha_documento=None,
) -> OrdenTrabajoArchivo:
    """
    Adjunta un nuevo archivo a una Orden de Trabajo.

    El archivo queda registrado como parte
    del historial documental de la OT.

    El usuario que realiza la carga se registra
    automáticamente y no debe ser seleccionado
    manualmente desde la interfaz.

    La fecha funcional utiliza:

        fecha_documento explícita
            ↓
        timezone.now()

    El registro comienza siempre activo.

    Una vez creado, el archivo no debe
    modificarse ni reemplazarse directamente.
    Si deja de ser válido debe utilizarse
    retirar_archivo_ot().
    """

    # ==================================================
    # VALIDACIONES PREVIAS
    # ==================================================

    _validar_orden_guardada(
        orden_trabajo
    )

    _validar_usuario(
        usuario
    )

    _validar_archivo_subido(
        archivo
    )

    # ==================================================
    # BLOQUEAR OT
    # ==================================================

    orden_bloqueada = (
        _bloquear_orden(
            orden_trabajo
        )
    )

    # ==================================================
    # REGLAS FUNCIONALES
    # ==================================================

    _validar_gestion_documental(
        orden_bloqueada
    )

    # ==================================================
    # NORMALIZAR DATOS
    # ==================================================

    descripcion = (
        _normalizar_descripcion(
            descripcion
        )
    )

    # ==================================================
    # RESOLVER FECHA FUNCIONAL
    # ==================================================

    fecha_resuelta = (
        _resolver_fecha_hora(
            fecha_explicita=fecha_documento,
        )
    )

    # ==================================================
    # CREAR REGISTRO
    # ==================================================

    registro = OrdenTrabajoArchivo(
        orden_trabajo=orden_bloqueada,
        usuario=usuario,
        archivo=archivo,
        descripcion=descripcion,
        fecha_documento=fecha_resuelta,
        is_active=True,
        fecha_retiro=None,
        usuario_retiro=None,
        motivo_retiro="",
    )

    # ==================================================
    # VALIDAR MODELO
    # ==================================================

    registro.full_clean()

    # ==================================================
    # GUARDAR
    # ==================================================

    registro.save()

    return registro


# ======================================================
# RETIRAR ARCHIVO
# ======================================================


@transaction.atomic
def retirar_archivo_ot(
    *,
    archivo_ot: OrdenTrabajoArchivo,
    usuario: Usuario,
    motivo: str,
    fecha_retiro=None,
) -> OrdenTrabajoArchivo:
    """
    Retira lógicamente un archivo asociado
    a una Orden de Trabajo.

    El retiro NO:

    - elimina el registro de la base de datos;
    - elimina físicamente el archivo del storage;
    - reemplaza el documento original.

    El retiro SÍ registra:

    - is_active = False;
    - fecha_retiro;
    - usuario_retiro;
    - motivo_retiro.

    Esto permite conservar completamente
    la trazabilidad documental.
    """

    # ==================================================
    # VALIDACIONES PREVIAS
    # ==================================================

    _validar_archivo_guardado(
        archivo_ot
    )

    _validar_usuario(
        usuario
    )

    # ==================================================
    # MOTIVO
    # ==================================================

    motivo = (
        _normalizar_motivo(
            motivo
        )
    )

    # ==================================================
    # BLOQUEAR ARCHIVO
    # ==================================================

    archivo_bloqueado = (
        _bloquear_archivo(
            archivo_ot
        )
    )

    # ==================================================
    # BLOQUEAR OT
    # ==================================================

    orden_bloqueada = (
        _bloquear_orden(
            archivo_bloqueado.orden_trabajo
        )
    )

    # ==================================================
    # REGLAS DE LA OT
    # ==================================================

    _validar_gestion_documental(
        orden_bloqueada
    )

    # ==================================================
    # VALIDAR ESTADO ACTUAL
    # ==================================================

    if not archivo_bloqueado.is_active:
        raise ValidationError(
            _(
                "El archivo ya fue retirado "
                "anteriormente."
            )
        )

    # ==================================================
    # FECHA DEL RETIRO
    # ==================================================

    fecha_resuelta = (
        _resolver_fecha_hora(
            fecha_explicita=fecha_retiro,
            fecha_existente=(
                archivo_bloqueado.fecha_retiro
            ),
        )
    )

    # ==================================================
    # APLICAR RETIRO
    # ==================================================

    archivo_bloqueado.is_active = False

    archivo_bloqueado.fecha_retiro = (
        fecha_resuelta
    )

    archivo_bloqueado.usuario_retiro = (
        usuario
    )

    archivo_bloqueado.motivo_retiro = (
        motivo
    )

    # ==================================================
    # VALIDACIÓN DEL MODELO
    # ==================================================

    archivo_bloqueado.full_clean()

    # ==================================================
    # GUARDAR
    # ==================================================

    archivo_bloqueado.save(
        update_fields=[
            "is_active",
            "fecha_retiro",
            "usuario_retiro",
            "motivo_retiro",
            "updated_at",
        ]
    )

    return archivo_bloqueado


# ======================================================
# EXPORTS
# ======================================================


__all__ = [
    "adjuntar_archivo_ot",
    "retirar_archivo_ot",
]