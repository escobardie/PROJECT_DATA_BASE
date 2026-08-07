from .detalle import (
    actualizar_detalle_proyecto,
    crear_detalle_proyecto,
    eliminar_detalle_proyecto,
)

from .estado import (
    cambiar_estado_proyecto,
)

from .totales import (
    actualizar_totales_proyecto,
    calcular_importes_detalle,
    completar_detalle_desde_origen,
)


__all__ = (
    # Detalles
    "crear_detalle_proyecto",
    "actualizar_detalle_proyecto",
    "eliminar_detalle_proyecto",

    # Estado
    "cambiar_estado_proyecto",

    # Totales
    "actualizar_totales_proyecto",
    "calcular_importes_detalle",
    "completar_detalle_desde_origen",
)