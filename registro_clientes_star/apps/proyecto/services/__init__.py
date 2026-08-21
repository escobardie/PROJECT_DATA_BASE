from .detalle import (
    actualizar_detalle_proyecto,
    crear_detalle_proyecto,
    eliminar_detalle_proyecto,
)

from .estado import (
    finalizar_proyecto,
    planificar_proyecto,
    registrar_aceptacion_proyecto,
    registrar_envio_proyecto,
    registrar_recepcion_proyecto,
    registrar_rechazo_proyecto,
)

from .totales import (
    actualizar_totales_proyecto,
    calcular_importes_detalle,
    completar_detalle_desde_origen,
)
from .orden_trabajo import (
    crear_orden_trabajo_desde_proyecto,
)

__all__ = (
    # Detalles
    "crear_detalle_proyecto",
    "actualizar_detalle_proyecto",
    "eliminar_detalle_proyecto",

    # Estado
    "planificar_proyecto",
    "registrar_aceptacion_proyecto",
    "registrar_envio_proyecto",
    "registrar_recepcion_proyecto",
    "registrar_rechazo_proyecto",
    "finalizar_proyecto",

    # Totales
    "actualizar_totales_proyecto",
    "calcular_importes_detalle",
    "completar_detalle_desde_origen",

    # Orden de trabajo
    "crear_orden_trabajo_desde_proyecto",
)