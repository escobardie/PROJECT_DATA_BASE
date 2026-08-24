from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.choices import (
    EstadoProyectoChoices,
)

from apps.proyecto.models import (
    Proyecto,
    ProyectoArchivo,
)

from apps.usuarios.models import Usuario


# ======================================================
# VALIDACIONES INTERNAS
# ======================================================


def _validar_proyecto_guardado(
    proyecto: Proyecto | None,
) -> None:
    """
    Verifica que el Proyecto exista físicamente
    en la base de datos.

    Los archivos solamente pueden gestionarse
    sobre un proyecto previamente guardado.
    """

    if (
        proyecto is None
        or not proyecto.pk
    ):
        raise ValidationError(
            _(
                "El proyecto debe estar guardado "
                "antes de gestionar archivos."
            )
        )


def _validar_usuario(
    usuario: Usuario | None,
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
    archivo_proyecto: ProyectoArchivo | None,
) -> None:
    """
    Verifica que el registro documental
    exista físicamente en la base de datos.
    """

    if (
        archivo_proyecto is None
        or not archivo_proyecto.pk
    ):
        raise ValidationError(
            _(
                "El archivo del proyecto debe estar "
                "guardado antes de realizar esta operación."
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
    Aplica la regla general de fechas:

    1. fecha proporcionada explícitamente;
    2. fecha ya existente;
    3. fecha y hora actuales.

    Permite registrar documentación histórica
    sin alterar created_at.
    """

    return (
        fecha_explicita
        or fecha_existente
        or timezone.now()
    )


# ======================================================
# BLOQUEOS
# ======================================================


def _bloquear_proyecto(
    proyecto: Proyecto,
) -> Proyecto:
    """
    Recupera y bloquea el Proyecto durante
    la transacción actual.
    """

    return (
        Proyecto.objects
        .select_for_update()
        .get(
            pk=proyecto.pk,
        )
    )


def _bloquear_archivo(
    archivo_proyecto: ProyectoArchivo,
) -> ProyectoArchivo:
    """
    Recupera y bloquea el archivo documental
    durante la transacción actual.
    """

    return (
        ProyectoArchivo.objects
        .select_for_update()
        .select_related(
            "proyecto",
            "usuario",
            "usuario_retiro",
        )
        .get(
            pk=archivo_proyecto.pk,
        )
    )


# ======================================================
# REGLAS DOCUMENTALES
# ======================================================


def _validar_gestion_documental(
    proyecto: Proyecto,
) -> None:
    """
    Determina si el estado del Proyecto permite
    operaciones documentales.

    Regla:

    - BORRADOR:
        permite documentación.

    - PLANIFICADO:
        permite documentación.

    - PENDIENTE_APROBACION:
        permite documentación.

    - APROBADO:
        permite documentación.

    - EN_EJECUCION:
        permite documentación.

    - FINALIZADO:
        permite documentación posterior,
        por ejemplo:
            * actas;
            * documentación conforme a obra;
            * informes finales;
            * conformidades;
            * documentación administrativa.

    - CANCELADO:
        bloquea nuevas operaciones documentales.
    """

    if (
        proyecto.estado
        == EstadoProyectoChoices.CANCELADO
    ):
        raise ValidationError(
            {
                "estado": _(
                    "No se pueden gestionar archivos "
                    "en un proyecto cancelado."
                )
            }
        )


# ======================================================
# NORMALIZACIÓN
# ======================================================


def _normalizar_descripcion(
    descripcion: str | None,
) -> str:
    """
    Normaliza la descripción documental.
    """

    return (
        descripcion
        or ""
    ).strip()


def _normalizar_motivo(
    motivo: str | None,
) -> str:
    """
    Normaliza y valida el motivo
    utilizado para retirar un archivo.
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
    Realiza validaciones básicas sobre
    el archivo recibido.

    Actualmente comprueba:

    - que exista;
    - que no esté vacío.

    La política de extensiones, tamaño máximo
    y MIME puede incorporarse posteriormente.
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
def adjuntar_archivo_proyecto(
    *,
    proyecto: Proyecto,
    usuario: Usuario,
    archivo,
    descripcion: str = "",
    fecha_documento=None,
) -> ProyectoArchivo:
    """
    Adjunta un nuevo archivo a un Proyecto.

    El registro forma parte del historial documental.

    El usuario se registra automáticamente
    y no debe seleccionarse manualmente.

    La fecha funcional se determina mediante:

        fecha_documento explícita
                ↓
        timezone.now()

    Todo documento nuevo comienza activo.

    Una vez registrado no debe reemplazarse
    ni modificarse directamente.

    Si deja de ser válido debe utilizarse
    retirar_archivo_proyecto().
    """

    # ==================================================
    # VALIDACIONES PREVIAS
    # ==================================================

    _validar_proyecto_guardado(
        proyecto
    )

    _validar_usuario(
        usuario
    )

    _validar_archivo_subido(
        archivo
    )

    # ==================================================
    # BLOQUEAR PROYECTO
    # ==================================================

    proyecto_bloqueado = (
        _bloquear_proyecto(
            proyecto
        )
    )

    # ==================================================
    # REGLAS FUNCIONALES
    # ==================================================

    _validar_gestion_documental(
        proyecto_bloqueado
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
    # RESOLVER FECHA DOCUMENTAL
    # ==================================================

    fecha_resuelta = (
        _resolver_fecha_hora(
            fecha_explicita=fecha_documento,
        )
    )

    # ==================================================
    # CREAR REGISTRO
    # ==================================================

    registro = ProyectoArchivo(
        proyecto=proyecto_bloqueado,
        usuario=usuario,
        archivo=archivo,
        fecha_documento=fecha_resuelta,
        descripcion=descripcion,

        # Documento nuevo.
        is_active=True,

        # Sin información de retiro.
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
def retirar_archivo_proyecto(
    *,
    archivo_proyecto: ProyectoArchivo,
    usuario: Usuario,
    motivo: str,
    fecha_retiro=None,
) -> ProyectoArchivo:
    """
    Retira lógicamente un archivo asociado
    a un Proyecto.

    El retiro NO:

    - elimina el registro;
    - elimina físicamente el archivo;
    - reemplaza el archivo original;
    - modifica quién realizó la carga original;
    - modifica created_at.

    El retiro SÍ registra:

    - is_active = False;
    - fecha_retiro;
    - usuario_retiro;
    - motivo_retiro.

    De esta forma se mantiene íntegramente
    la trazabilidad documental.
    """

    # ==================================================
    # VALIDACIONES PREVIAS
    # ==================================================

    _validar_archivo_guardado(
        archivo_proyecto
    )

    _validar_usuario(
        usuario
    )

    # ==================================================
    # NORMALIZAR MOTIVO
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
            archivo_proyecto
        )
    )

    # ==================================================
    # BLOQUEAR PROYECTO
    # ==================================================

    proyecto_bloqueado = (
        _bloquear_proyecto(
            archivo_bloqueado.proyecto
        )
    )

    # ==================================================
    # REGLAS DEL PROYECTO
    # ==================================================

    _validar_gestion_documental(
        proyecto_bloqueado
    )

    # ==================================================
    # VALIDAR ESTADO ACTUAL DEL DOCUMENTO
    # ==================================================

    if not archivo_bloqueado.is_active:
        raise ValidationError(
            _(
                "El archivo ya fue retirado "
                "anteriormente."
            )
        )

    # ==================================================
    # RESOLVER FECHA DE RETIRO
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
    # VALIDAR MODELO
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
    "adjuntar_archivo_proyecto",
    "retirar_archivo_proyecto",
]