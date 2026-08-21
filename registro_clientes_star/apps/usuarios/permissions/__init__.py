from .rules import (
    puede_ver_proyecto,
    puede_editar_proyecto,
    puede_eliminar_proyecto,
    puede_ver_costos_del_proyecto,

    puede_ver_orden_trabajo,
    puede_editar_orden_trabajo,
    puede_cerrar_ot,
    puede_facturar_ot,
    puede_cobrar_ot,
    puede_crear_instalacion_desde_ot,

    puede_ver_instalacion,
    puede_editar_instalacion,
    puede_finalizar_instalacion_concreta,
    puede_ver_credenciales_instalacion,

    puede_ver_cuenta_cliente,
    puede_ver_sucursal,

    # Transiciones OT
    puede_iniciar_ot,
    puede_pausar_ot,
    puede_programar_ot,
    puede_reanudar_ot,
    puede_registrar_recepcion_ot,
    puede_registrar_envio_ot,
    puede_registrar_respuesta_ot,
    puede_registrar_aceptacion_ot,
    puede_registrar_rechazo_ot,
    puede_finalizar_ot,

    puede_programar_instalacion_concreta,
    puede_iniciar_instalacion_concreta,
    puede_cancelar_instalacion_concreta,
    puede_registrar_conformidad_instalacion,

    puede_asignar_tecnico_ot,
    puede_desasignar_tecnico_ot,
    puede_establecer_tecnico_principal_ot,
    puede_gestionar_tecnicos_ot,
    puede_registrar_seguimiento_ot,
    puede_ver_seguimiento_ot,
    puede_ver_tecnico_ot,

    puede_adjuntar_archivo_ot,
    puede_retirar_archivo_ot,
    puede_ver_archivo_ot,

    # ======================================================
    # FLUJO DE PROYECTO
    # ======================================================
    puede_registrar_recepcion_proyecto,
    puede_planificar_proyecto,
    puede_registrar_envio_proyecto,
    puede_registrar_respuesta_proyecto,
    puede_registrar_aceptacion_proyecto,
    puede_registrar_rechazo_proyecto,
    puede_generar_ot_desde_proyecto,
    puede_finalizar_proyecto,
)


__all__ = (
    "puede_ver_proyecto",
    "puede_editar_proyecto",
    "puede_eliminar_proyecto",
    "puede_ver_costos_del_proyecto",

    "puede_ver_orden_trabajo",
    "puede_editar_orden_trabajo",
    "puede_cerrar_ot",
    "puede_facturar_ot",
    "puede_cobrar_ot",
    "puede_crear_instalacion_desde_ot",

    "puede_ver_instalacion",
    "puede_editar_instalacion",
    "puede_finalizar_instalacion_concreta",
    "puede_ver_credenciales_instalacion",

    "puede_ver_cuenta_cliente",
    "puede_ver_sucursal",

    # Transiciones OT
    "puede_iniciar_ot",
    "puede_pausar_ot",
    "puede_programar_ot",
    "puede_reanudar_ot",
    "puede_registrar_recepcion_ot",
    "puede_registrar_envio_ot",
    "puede_registrar_respuesta_ot",
    "puede_registrar_aceptacion_ot",
    "puede_registrar_rechazo_ot",
    "puede_finalizar_ot",

    "puede_programar_instalacion_concreta",
    "puede_iniciar_instalacion_concreta",
    "puede_cancelar_instalacion_concreta",
    "puede_registrar_conformidad_instalacion",

    "puede_asignar_tecnico_ot",
    "puede_desasignar_tecnico_ot",
    "puede_establecer_tecnico_principal_ot",
    "puede_gestionar_tecnicos_ot",
    "puede_registrar_seguimiento_ot",
    "puede_ver_seguimiento_ot",
    "puede_ver_tecnico_ot",
    "puede_ver_archivo_ot",
    "puede_adjuntar_archivo_ot",
    "puede_retirar_archivo_ot",


    # ======================================================
    # FLUJO DE PROYECTO
    # ======================================================
    "puede_registrar_recepcion_proyecto",
    "puede_planificar_proyecto",
    "puede_registrar_envio_proyecto",
    "puede_registrar_respuesta_proyecto",
    "puede_registrar_aceptacion_proyecto",
    "puede_registrar_rechazo_proyecto",
    "puede_generar_ot_desde_proyecto",
    "puede_finalizar_proyecto",
)