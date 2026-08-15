from .estado import (
    cancelar_orden_trabajo,
    finalizar_orden_trabajo,
    iniciar_orden_trabajo,
    pausar_orden_trabajo,
    programar_orden_trabajo,
    reanudar_orden_trabajo,
    registrar_aceptacion_cliente,
    registrar_cobro_ot,
    registrar_envio_cliente,
    registrar_facturacion_ot,
    registrar_recepcion_solicitud,
    registrar_rechazo_cliente,
)

from .tecnico import (
    asignar_tecnico_ot,
    actualizar_tecnico_ot,
    marcar_tecnico_principal,
    quitar_tecnico_ot,
)

from .seguimiento import (
    actualizar_seguimiento_ot,
    crear_seguimiento_ot,
    eliminar_seguimiento_ot,
)

from .archivo import (
    actualizar_archivo_ot,
    crear_archivo_ot,
    eliminar_archivo_ot,
)

from .instalacion import (
    crear_instalacion_desde_ot,
)


__all__ = (
    # Estado
    "registrar_recepcion_solicitud",
    "programar_orden_trabajo",
    "registrar_envio_cliente",
    "registrar_aceptacion_cliente",
    "registrar_rechazo_cliente",
    "iniciar_orden_trabajo",
    "pausar_orden_trabajo",
    "reanudar_orden_trabajo",
    "finalizar_orden_trabajo",
    "cancelar_orden_trabajo",
    "registrar_facturacion_ot",
    "registrar_cobro_ot",

    # Técnicos
    "asignar_tecnico_ot",
    "actualizar_tecnico_ot",
    "marcar_tecnico_principal",
    "quitar_tecnico_ot",

    # Seguimientos
    "crear_seguimiento_ot",
    "actualizar_seguimiento_ot",
    "eliminar_seguimiento_ot",

    # Archivos
    "crear_archivo_ot",
    "actualizar_archivo_ot",
    "eliminar_archivo_ot",

    # Instalación
    "crear_instalacion_desde_ot",
)