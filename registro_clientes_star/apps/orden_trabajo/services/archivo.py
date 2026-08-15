"""
Servicios relacionados con archivos
de órdenes de trabajo.

Este módulo centraliza:

- carga de archivos;
- actualización de descripción;
- eliminación de archivos.

Todas las operaciones de escritura se ejecutan
dentro de transacciones atómicas.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.orden_trabajo.models import (
    OrdenTrabajo,
    OrdenTrabajoArchivo,
)

from apps.usuarios.models import Usuario


# ======================================================
# FUNCIONES PRIVADAS
# ======================================================

def _validar_orden(
    orden_trabajo: OrdenTrabajo | None,
) -> None:
    """
    Valida que la orden exista y esté guardada.
    """

    if orden_trabajo is None:
        raise ValueError(
            "Debe proporcionar una orden de trabajo válida."
        )

    if not orden_trabajo.pk:
        raise ValueError(
            "La orden de trabajo debe estar guardada."
        )


def _validar_usuario(
    usuario: Usuario | None,
) -> None:
    """
    Valida que el usuario exista y esté guardado.
    """

    if usuario is None:
        raise ValueError(
            "Debe proporcionar un usuario válido."
        )

    if not usuario.pk:
        raise ValueError(
            "El usuario debe estar guardado."
        )


def _validar_archivo(
    archivo,
) -> None:
    """
    Valida que se haya proporcionado un archivo.
    """

    if not archivo:
        raise ValidationError(
            {
                "archivo": _(
                    "Debe proporcionar un archivo."
                )
            }
        )


def _normalizar_descripcion(
    descripcion: str | None,
) -> str:
    """
    Normaliza la descripción del archivo.
    """

    return (
        descripcion
        or ""
    ).strip()


def _bloquear_orden(
    orden_trabajo: OrdenTrabajo,
) -> OrdenTrabajo:
    """
    Recupera y bloquea la OT durante
    la transacción actual.
    """

    _validar_orden(
        orden_trabajo
    )

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
    Recupera y bloquea un archivo asociado
    a una orden de trabajo.
    """

    if archivo_ot is None:
        raise ValueError(
            "Debe proporcionar un archivo válido."
        )

    if not archivo_ot.pk:
        raise ValueError(
            "El archivo debe estar guardado."
        )

    return (
        OrdenTrabajoArchivo.objects
        .select_for_update()
        .select_related(
            "orden_trabajo",
            "usuario",
        )
        .get(
            pk=archivo_ot.pk,
        )
    )


# ======================================================
# CREAR ARCHIVO
# ======================================================

@transaction.atomic
def crear_archivo_ot(
    *,
    orden_trabajo: OrdenTrabajo,
    usuario: Usuario,
    archivo,
    descripcion: str = "",
) -> OrdenTrabajoArchivo:
    """
    Carga un archivo asociado a una orden de trabajo.

    Args:
        orden_trabajo:
            Orden a la cual se asociará el archivo.

        usuario:
            Usuario que realiza la carga.

        archivo:
            Archivo recibido por Django.

        descripcion:
            Descripción breve opcional.

    Returns:
        OrdenTrabajoArchivo:
            Registro creado.
    """

    _validar_usuario(
        usuario
    )

    _validar_archivo(
        archivo
    )

    orden = _bloquear_orden(
        orden_trabajo
    )

    registro = OrdenTrabajoArchivo(
        orden_trabajo=orden,
        usuario=usuario,
        archivo=archivo,
        descripcion=_normalizar_descripcion(
            descripcion
        ),
    )

    registro.full_clean()

    registro.save()

    return registro


# ======================================================
# ACTUALIZAR DESCRIPCIÓN
# ======================================================

@transaction.atomic
def actualizar_archivo_ot(
    *,
    archivo_ot: OrdenTrabajoArchivo,
    descripcion: str,
) -> OrdenTrabajoArchivo:
    """
    Actualiza únicamente la descripción
    de un archivo existente.

    El archivo físico y el usuario que realizó
    la carga no se modifican mediante este service.
    """

    registro = _bloquear_archivo(
        archivo_ot
    )

    _bloquear_orden(
        registro.orden_trabajo
    )

    registro.descripcion = (
        _normalizar_descripcion(
            descripcion
        )
    )

    registro.full_clean()

    registro.save(
        update_fields=(
            "descripcion",
        ),
    )

    return registro


# ======================================================
# ELIMINAR ARCHIVO
# ======================================================

@transaction.atomic
def eliminar_archivo_ot(
    *,
    archivo_ot: OrdenTrabajoArchivo,
    eliminar_archivo_fisico: bool = True,
) -> tuple[int, dict[str, int]]:
    """
    Elimina un archivo asociado a una OT.

    Si ``eliminar_archivo_fisico`` es True,
    también elimina el archivo del storage.

    Args:
        archivo_ot:
            Registro que debe eliminarse.

        eliminar_archivo_fisico:
            Indica si debe eliminarse el archivo
            físico almacenado.

    Returns:
        tuple:
            Resultado estándar de Django al eliminar.
    """

    registro = _bloquear_archivo(
        archivo_ot
    )

    _bloquear_orden(
        registro.orden_trabajo
    )

    campo_archivo = registro.archivo

    resultado = registro.delete()

    if (
        eliminar_archivo_fisico
        and campo_archivo
    ):
        campo_archivo.delete(
            save=False,
        )

    return resultado


__all__ = (
    "crear_archivo_ot",
    "actualizar_archivo_ot",
    "eliminar_archivo_ot",
)