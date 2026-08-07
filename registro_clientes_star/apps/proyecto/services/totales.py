"""
Servicios económicos de proyectos.

Este módulo concentra la lógica relacionada con:

- completar detalles desde su origen;
- calcular y redondear importes de un detalle;
- recalcular los totales generales de un proyecto.
"""

from decimal import (
    Decimal,
    ROUND_HALF_UP,
)

from django.db import transaction
from django.db.models import Sum

from apps.common.choices import (
    TipoProyectoDetalleChoices,
    UnidadMedidaChoices,
)

from apps.common.constants import (
    PRICE_DECIMAL_PLACES,
)

from apps.proyecto.models import (
    Proyecto,
    ProyectoDetalle,
)


# ======================================================
# CONSTANTES
# ======================================================

CERO = Decimal("0.00")

CUANTIZADOR_MONETARIO = Decimal("1").scaleb(
    -PRICE_DECIMAL_PLACES
)

CAMPOS_TOTALES_PROYECTO = (
    "subtotal",
    "descuento_total",
    "impuestos",
    "total",
)


# ======================================================
# FUNCIONES PRIVADAS
# ======================================================

def _redondear_importe(
    importe: Decimal | int | float | None,
) -> Decimal:
    """
    Redondea un importe a la cantidad de decimales
    configurada para los campos monetarios.

    Args:
        importe:
            Valor monetario que debe redondearse.

    Returns:
        Decimal:
            Importe normalizado y redondeado.
    """

    if importe is None:
        importe_decimal = CERO
    elif isinstance(importe, Decimal):
        importe_decimal = importe
    else:
        importe_decimal = Decimal(
            str(importe)
        )

    return importe_decimal.quantize(
        CUANTIZADOR_MONETARIO,
        rounding=ROUND_HALF_UP,
    )


# ======================================================
# COMPLETAR DETALLE DESDE ORIGEN
# ======================================================

def completar_detalle_desde_origen(
    detalle: ProyectoDetalle,
) -> ProyectoDetalle:
    """
    Completa los valores iniciales del detalle a partir
    del dispositivo o del ítem de catálogo seleccionado.

    Los valores ingresados manualmente no se reemplazan,
    salvo el tipo y la unidad, que siempre deben coincidir
    con el origen seleccionado.

    Args:
        detalle:
            Detalle de proyecto que debe completarse.

    Returns:
        ProyectoDetalle:
            La misma instancia recibida, actualizada
            solamente en memoria.
    """

    if detalle.dispositivo_id:
        detalle.tipo = (
            TipoProyectoDetalleChoices.DISPOSITIVO
        )

        if not detalle.descripcion:
            detalle.descripcion = (
                detalle.dispositivo.nombre_comercial
            )

        if (
            detalle.precio_unitario is None
            or detalle.precio_unitario == CERO
        ):
            detalle.precio_unitario = (
                detalle.dispositivo.precio_mercado
            )

        detalle.unidad = (
            UnidadMedidaChoices.UNIDAD
        )

        return detalle

    if detalle.item_catalogo_id:
        detalle.tipo = (
            detalle.item_catalogo.tipo
        )

        if not detalle.descripcion:
            detalle.descripcion = (
                detalle.item_catalogo.nombre
            )

        if (
            detalle.precio_unitario is None
            or detalle.precio_unitario == CERO
        ):
            detalle.precio_unitario = (
                detalle.item_catalogo.precio_venta
            )

        detalle.unidad = (
            detalle.item_catalogo.unidad
        )

    return detalle


# ======================================================
# CÁLCULO DE IMPORTES DEL DETALLE
# ======================================================

def calcular_importes_detalle(
    detalle: ProyectoDetalle,
) -> ProyectoDetalle:
    """
    Calcula y redondea los importes económicos
    de un detalle de proyecto.

    Fórmulas:

        subtotal = cantidad * precio_unitario

        total = subtotal
                - descuento_importe
                + impuestos_importe

    Args:
        detalle:
            Detalle cuyos importes deben calcularse.

    Returns:
        ProyectoDetalle:
            La misma instancia recibida, con sus importes
            calculados y redondeados en memoria.
    """

    cantidad = (
        detalle.cantidad
        or CERO
    )

    precio_unitario = (
        detalle.precio_unitario
        or CERO
    )

    descuento = (
        detalle.descuento_importe
        or CERO
    )

    impuestos = (
        detalle.impuestos_importe
        or CERO
    )

    detalle.precio_unitario = (
        _redondear_importe(
            precio_unitario
        )
    )

    detalle.descuento_importe = (
        _redondear_importe(
            descuento
        )
    )

    detalle.impuestos_importe = (
        _redondear_importe(
            impuestos
        )
    )

    detalle.subtotal = (
        _redondear_importe(
            cantidad
            * detalle.precio_unitario
        )
    )

    detalle.total = (
        _redondear_importe(
            detalle.subtotal
            - detalle.descuento_importe
            + detalle.impuestos_importe
        )
    )

    return detalle


# ======================================================
# ACTUALIZACIÓN DE TOTALES DEL PROYECTO
# ======================================================

@transaction.atomic
def actualizar_totales_proyecto(
    proyecto: Proyecto,
    *,
    guardar: bool = True,
) -> Proyecto:
    """
    Recalcula los importes generales del proyecto
    a partir de los detalles guardados.

    Args:
        proyecto:
            Proyecto cuyos totales deben recalcularse.

        guardar:
            Indica si los valores deben persistirse
            inmediatamente en la base de datos.

    Returns:
        Proyecto:
            La misma instancia recibida con los totales
            actualizados en memoria.

    Raises:
        ValueError:
            Cuando no se proporciona un proyecto válido
            o el proyecto todavía no fue guardado.
    """

    if proyecto is None:
        raise ValueError(
            "Debe proporcionar un proyecto válido."
        )

    if not proyecto.pk:
        raise ValueError(
            "El proyecto debe estar guardado antes "
            "de actualizar sus totales."
        )

    resumen = (
        proyecto.detalles
        .aggregate(
            subtotal=Sum(
                "subtotal"
            ),
            descuento_total=Sum(
                "descuento_importe"
            ),
            impuestos=Sum(
                "impuestos_importe"
            ),
        )
    )

    proyecto.subtotal = (
        _redondear_importe(
            resumen["subtotal"]
            or CERO
        )
    )

    proyecto.descuento_total = (
        _redondear_importe(
            resumen["descuento_total"]
            or CERO
        )
    )

    proyecto.impuestos = (
        _redondear_importe(
            resumen["impuestos"]
            or CERO
        )
    )

    proyecto.total = (
        _redondear_importe(
            proyecto.subtotal
            - proyecto.descuento_total
            + proyecto.impuestos
        )
    )

    if guardar:
        Proyecto.objects.filter(
            pk=proyecto.pk,
        ).update(
            subtotal=proyecto.subtotal,
            descuento_total=(
                proyecto.descuento_total
            ),
            impuestos=proyecto.impuestos,
            total=proyecto.total,
        )

    return proyecto


__all__ = (
    "actualizar_totales_proyecto",
    "calcular_importes_detalle",
    "completar_detalle_desde_origen",
)