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

from .archivo import (
    adjuntar_archivo_proyecto,
    retirar_archivo_proyecto,
    adjuntar_archivo_google_drive_proyecto,
)

from .google_drive import (
    GoogleDriveServiceError,
    generar_url_autorizacion_drive,
    google_drive_esta_conectado,
    obtener_archivo_drive,
    obtener_credenciales_drive,
    obtener_o_crear_carpeta_proyecto_drive,
    obtener_o_crear_carpeta_raiz_drive,
    obtener_servicio_drive,
    procesar_callback_oauth_drive,
    subir_archivo_proyecto_drive,
    eliminar_archivo_drive,
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

    # Archivos
    "adjuntar_archivo_proyecto",
    "retirar_archivo_proyecto",
    "adjuntar_archivo_google_drive_proyecto",

    #google drive
    "generar_url_autorizacion_drive",
    "GoogleDriveServiceError",
    "google_drive_esta_conectado",
    "obtener_archivo_drive",
    "obtener_credenciales_drive",
    "obtener_o_crear_carpeta_proyecto_drive",
    "obtener_o_crear_carpeta_raiz_drive",
    "obtener_servicio_drive",
    "procesar_callback_oauth_drive",
    "subir_archivo_proyecto_drive",
    "eliminar_archivo_drive",
    
)