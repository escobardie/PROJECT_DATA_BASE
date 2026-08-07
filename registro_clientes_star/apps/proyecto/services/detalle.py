"""
Casos de uso relacionados con los detalles de un proyecto.

Este módulo permite:

- crear un detalle;
- actualizar un detalle;
- eliminar un detalle;
- recalcular los totales del proyecto asociado.

Todas las operaciones de escritura se ejecutan
dentro de transacciones atómicas.
"""

from decimal import Decimal
from typing import Any

from django.db import transaction
from django.db.models import Max

from apps.catalogo.models import ItemCatalogo
from apps.dispositivo.models import Dispositivo

from apps.proyecto.models import (
    Proyecto,
    ProyectoDetalle,
)

from .totales import (
    actualizar_totales_proyecto,
    calcular_importes_detalle,
    completar_detalle_desde_origen,
)


# ======================================================
# CONSTANTES
# ======================================================

CERO = Decimal("0.00")

CANTIDAD_PREDETERMINADA = Decimal(
    "1.00"
)

_NO_CAMBIAR = object()


# ======================================================
# FUNCIONES PRIVADAS
# ======================================================

def _bloquear_proyecto(
    proyecto: Proyecto,
) -> Proyecto:
    """
    Obtiene y bloquea el proyecto durante
    la transacción actual.

    El bloqueo evita que dos operaciones concurrentes
    modifiquen simultáneamente los detalles y totales
    del mismo proyecto.

    Raises:
        ValueError:
            Cuando el proyecto no existe o no fue guardado.
    """

    if proyecto is None:
        raise ValueError(
            "Debe proporcionar un proyecto válido."
        )

    if not proyecto.pk:
        raise ValueError(
            "Debe proporcionar un proyecto guardado."
        )

    return (
        Proyecto.objects
        .select_for_update()
        .get(
            pk=proyecto.pk,
        )
    )


def _obtener_siguiente_orden(
    proyecto: Proyecto,
) -> int:
    """
    Devuelve el siguiente número de orden disponible
    dentro del proyecto.

    El proyecto debe encontrarse bloqueado dentro
    de la transacción antes de llamar esta función.
    """

    ultimo_orden = (
        proyecto.detalles
        .aggregate(
            maximo=Max(
                "orden"
            ),
        )
        .get(
            "maximo"
        )
        or 0
    )

    return ultimo_orden + 1


def _guardar_detalle_sin_override(
    detalle: ProyectoDetalle,
    *,
    force_insert: bool = False,
    force_update: bool = False,
    update_fields: tuple[str, ...] | None = None,
) -> None:
    """
    Guarda el detalle utilizando el método save()
    de la clase padre.

    Esto evita ejecutar temporalmente el save()
    personalizado de ProyectoDetalle, que todavía
    recalcula los totales por compatibilidad con
    código anterior.

    Se conserva el save() de CodeModel, incluida
    la generación automática del código.
    """

    super(
        ProyectoDetalle,
        detalle,
    ).save(
        force_insert=force_insert,
        force_update=force_update,
        update_fields=update_fields,
    )


def _eliminar_detalle_sin_override(
    detalle: ProyectoDetalle,
) -> tuple[int, dict[str, int]]:
    """
    Elimina el detalle sin ejecutar el delete()
    personalizado definido actualmente en el modelo.
    """

    return super(
        ProyectoDetalle,
        detalle,
    ).delete()


def _preparar_detalle(
    detalle: ProyectoDetalle,
) -> ProyectoDetalle:
    """
    Completa, calcula y valida el detalle antes
    de persistirlo.

    El orden aplicado es:

    1. Completar valores desde el origen.
    2. Calcular y redondear importes.
    3. Ejecutar todas las validaciones del modelo.
    """

    completar_detalle_desde_origen(
        detalle
    )

    calcular_importes_detalle(
        detalle
    )

    detalle.full_clean()

    return detalle


def _asignar_cambio(
    detalle: ProyectoDetalle,
    campo: str,
    valor: Any,
) -> None:
    """
    Asigna el valor al campo solamente cuando fue
    proporcionado explícitamente al servicio.
    """

    if valor is _NO_CAMBIAR:
        return

    setattr(
        detalle,
        campo,
        valor,
    )


# ======================================================
# CREAR DETALLE
# ======================================================

@transaction.atomic
def crear_detalle_proyecto(
    *,
    proyecto: Proyecto,
    dispositivo: Dispositivo | None = None,
    item_catalogo: ItemCatalogo | None = None,
    descripcion: str = "",
    orden: int | None = None,
    cantidad: Decimal = CANTIDAD_PREDETERMINADA,
    precio_unitario: Decimal = CERO,
    descuento_importe: Decimal = CERO,
    impuestos_importe: Decimal = CERO,
    observaciones: str = "",
    is_active: bool = True,
) -> ProyectoDetalle:
    """
    Crea un detalle comercial o técnico
    dentro de un proyecto.

    El detalle debe tener exactamente uno
    de estos orígenes:

    - dispositivo;
    - ítem del catálogo.

    Cuando no se informa el orden, el servicio
    asigna automáticamente el siguiente número
    disponible dentro del proyecto.

    El tipo, la unidad, la descripción y el precio
    pueden completarse automáticamente desde
    el origen seleccionado.

    Args:
        proyecto:
            Proyecto al que pertenecerá el detalle.

        dispositivo:
            Dispositivo técnico asociado.

        item_catalogo:
            Material, insumo, mano de obra, servicio,
            licencia, viático u otro concepto asociado.

        descripcion:
            Descripción histórica utilizada
            dentro del proyecto.

        orden:
            Posición dentro del proyecto. Si es None,
            se asigna automáticamente.

        cantidad:
            Cantidad presupuestada.

        precio_unitario:
            Precio comercial aplicado al detalle.
            Si es cero, podrá tomarse desde el origen.

        descuento_importe:
            Descuento monetario aplicado.

        impuestos_importe:
            Impuestos monetarios aplicados.

        observaciones:
            Información complementaria.

        is_active:
            Estado lógico del registro.

    Returns:
        ProyectoDetalle:
            Detalle creado y guardado.

    Raises:
        ValidationError:
            Cuando los datos no cumplen las reglas
            definidas en el modelo.

        ValueError:
            Cuando el proyecto no es válido
            o no está guardado.
    """

    proyecto_bloqueado = (
        _bloquear_proyecto(
            proyecto
        )
    )

    if orden is None:
        orden = (
            _obtener_siguiente_orden(
                proyecto_bloqueado
            )
        )

    detalle = ProyectoDetalle(
        proyecto=proyecto_bloqueado,
        dispositivo=dispositivo,
        item_catalogo=item_catalogo,
        descripcion=descripcion,
        orden=orden,
        cantidad=cantidad,
        precio_unitario=precio_unitario,
        descuento_importe=(
            descuento_importe
        ),
        impuestos_importe=(
            impuestos_importe
        ),
        observaciones=observaciones,
        is_active=is_active,
    )

    _preparar_detalle(
        detalle
    )

    _guardar_detalle_sin_override(
        detalle,
        force_insert=True,
    )

    actualizar_totales_proyecto(
        proyecto_bloqueado,
    )

    return detalle


# ======================================================
# ACTUALIZAR DETALLE
# ======================================================

@transaction.atomic
def actualizar_detalle_proyecto(
    *,
    detalle: ProyectoDetalle,
    dispositivo: Dispositivo | None | object = _NO_CAMBIAR,
    item_catalogo: ItemCatalogo | None | object = _NO_CAMBIAR,
    descripcion: str | object = _NO_CAMBIAR,
    orden: int | object = _NO_CAMBIAR,
    cantidad: Decimal | object = _NO_CAMBIAR,
    precio_unitario: Decimal | object = _NO_CAMBIAR,
    descuento_importe: Decimal | object = _NO_CAMBIAR,
    impuestos_importe: Decimal | object = _NO_CAMBIAR,
    observaciones: str | object = _NO_CAMBIAR,
    is_active: bool | object = _NO_CAMBIAR,
    reiniciar_desde_origen: bool = False,
) -> ProyectoDetalle:
    """
    Actualiza un detalle existente y recalcula
    los totales del proyecto.

    Cuando se proporciona un nuevo dispositivo,
    el ítem de catálogo se elimina automáticamente.

    Cuando se proporciona un nuevo ítem de catálogo,
    el dispositivo se elimina automáticamente.

    Con ``reiniciar_desde_origen=True`` se limpian
    la descripción y el precio para volver a obtenerlos
    desde el dispositivo o ítem seleccionado.

    Args:
        detalle:
            Detalle guardado que debe modificarse.

        reiniciar_desde_origen:
            Indica si la información comercial debe
            completarse nuevamente desde el origen.

    Returns:
        ProyectoDetalle:
            Detalle actualizado y guardado.

    Raises:
        ValueError:
            Cuando el detalle no es válido
            o todavía no fue guardado.

        ValidationError:
            Cuando los nuevos valores no cumplen
            las reglas del modelo.
    """

    if detalle is None:
        raise ValueError(
            "Debe proporcionar un detalle válido."
        )

    if not detalle.pk:
        raise ValueError(
            "Debe proporcionar un detalle guardado."
        )

    detalle_bloqueado = (
        ProyectoDetalle.objects
        .select_for_update()
        .select_related(
            "proyecto",
            "dispositivo",
            "item_catalogo",
        )
        .get(
            pk=detalle.pk,
        )
    )

    proyecto_bloqueado = (
        _bloquear_proyecto(
            detalle_bloqueado.proyecto
        )
    )

    # ==================================================
    # CAMBIO DE ORIGEN
    # ==================================================

    if dispositivo is not _NO_CAMBIAR:
        detalle_bloqueado.dispositivo = (
            dispositivo
        )

        if dispositivo is not None:
            detalle_bloqueado.item_catalogo = (
                None
            )

    if item_catalogo is not _NO_CAMBIAR:
        detalle_bloqueado.item_catalogo = (
            item_catalogo
        )

        if item_catalogo is not None:
            detalle_bloqueado.dispositivo = (
                None
            )

    if reiniciar_desde_origen:
        detalle_bloqueado.descripcion = ""
        detalle_bloqueado.precio_unitario = (
            CERO
        )

    # ==================================================
    # INFORMACIÓN GENERAL
    # ==================================================

    _asignar_cambio(
        detalle_bloqueado,
        "descripcion",
        descripcion,
    )

    _asignar_cambio(
        detalle_bloqueado,
        "orden",
        orden,
    )

    _asignar_cambio(
        detalle_bloqueado,
        "cantidad",
        cantidad,
    )

    _asignar_cambio(
        detalle_bloqueado,
        "precio_unitario",
        precio_unitario,
    )

    _asignar_cambio(
        detalle_bloqueado,
        "descuento_importe",
        descuento_importe,
    )

    _asignar_cambio(
        detalle_bloqueado,
        "impuestos_importe",
        impuestos_importe,
    )

    _asignar_cambio(
        detalle_bloqueado,
        "observaciones",
        observaciones,
    )

    _asignar_cambio(
        detalle_bloqueado,
        "is_active",
        is_active,
    )

    _preparar_detalle(
        detalle_bloqueado
    )

    _guardar_detalle_sin_override(
        detalle_bloqueado,
        force_update=True,
    )

    actualizar_totales_proyecto(
        proyecto_bloqueado,
    )

    return detalle_bloqueado


# ======================================================
# ELIMINAR DETALLE
# ======================================================

@transaction.atomic
def eliminar_detalle_proyecto(
    *,
    detalle: ProyectoDetalle,
) -> tuple[int, dict[str, int]]:
    """
    Elimina un detalle y recalcula los totales
    del proyecto relacionado.

    Args:
        detalle:
            Detalle guardado que debe eliminarse.

    Returns:
        tuple:
            Resultado estándar de Django:

            - cantidad total de registros eliminados;
            - detalle de eliminaciones por modelo.

    Raises:
        ValueError:
            Cuando el detalle no es válido
            o todavía no fue guardado.
    """

    if detalle is None:
        raise ValueError(
            "Debe proporcionar un detalle válido."
        )

    if not detalle.pk:
        raise ValueError(
            "Debe proporcionar un detalle guardado."
        )

    detalle_bloqueado = (
        ProyectoDetalle.objects
        .select_for_update()
        .select_related(
            "proyecto",
        )
        .get(
            pk=detalle.pk,
        )
    )

    proyecto_bloqueado = (
        _bloquear_proyecto(
            detalle_bloqueado.proyecto
        )
    )

    resultado = (
        _eliminar_detalle_sin_override(
            detalle_bloqueado
        )
    )

    actualizar_totales_proyecto(
        proyecto_bloqueado,
    )

    return resultado


__all__ = (
    "crear_detalle_proyecto",
    "actualizar_detalle_proyecto",
    "eliminar_detalle_proyecto",
)