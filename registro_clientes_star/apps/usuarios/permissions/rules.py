from typing import Any

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import Model

from apps.usuarios.services.permisos import (
    puede_cerrar_orden_trabajo,
    puede_editar_instalaciones,
    puede_editar_proyectos,
    puede_editar_ordenes_trabajo,
    puede_facturar_orden_trabajo,
    puede_finalizar_instalacion,
    puede_registrar_cobro_ot,
    puede_ver_instalaciones,
    puede_ver_ordenes_trabajo,
    puede_ver_proyectos,
    
)

from apps.common.choices import (
    EstadoAceptacionOTChoices,
    EstadoInstalacionChoices,
    EstadoOrdenTrabajoChoices,
    TipoOrdenTrabajoChoices,
    EstadoProyectoChoices,
    RespuestaClienteProyectoChoices,
)

from apps.usuarios.services.querysets import (
    filtrar_instalaciones,
    filtrar_ordenes_trabajo,
    filtrar_proyectos,
)

from apps.usuarios.services.roles import (
    es_auditor,
    es_creador_proyecto,
    es_gerencia,
    es_superadmin,
    es_tecnico,
    es_usuario_cliente,
)


# ======================================================
# FUNCIONES INTERNAS
# ======================================================

def _usuario_activo(
    usuario: AbstractBaseUser | None,
) -> bool:
    """
    Indica si el usuario está autenticado y activo.
    """

    return bool(
        usuario
        and usuario.is_authenticated
        and usuario.is_active
    )


def _objeto_guardado(
    objeto: Model | None,
) -> bool:
    """
    Indica si el objeto existe y ya fue guardado.
    """

    return bool(
        objeto
        and objeto.pk
    )


def _objeto_en_queryset(
    *,
    objeto: Model | None,
    queryset,
) -> bool:
    """
    Comprueba si un objeto forma parte del QuerySet autorizado.

    Se utiliza para reaprovechar las mismas reglas de alcance
    definidas en services/querysets.py.
    """

    if not _objeto_guardado(objeto):
        return False

    return queryset.filter(
        pk=objeto.pk,
    ).exists()


# ======================================================
# PROYECTOS
# ======================================================

def puede_ver_proyecto(
    usuario: AbstractBaseUser | None,
    proyecto,
) -> bool:
    """
    Indica si el usuario puede consultar
    un proyecto concreto.
    """

    if (
        not _usuario_activo(usuario)
        or not _objeto_guardado(proyecto)
        or not puede_ver_proyectos(usuario)
    ):
        return False

    queryset = filtrar_proyectos(
        usuario,
        proyecto.__class__.objects.all(),
    )

    return _objeto_en_queryset(
        objeto=proyecto,
        queryset=queryset,
    )


def puede_editar_proyecto(
    usuario: AbstractBaseUser | None,
    proyecto,
) -> bool:
    """
    Indica si el usuario puede modificar
    un proyecto concreto.

    Además del permiso general, el proyecto debe
    encontrarse dentro del alcance visible del usuario.
    """

    if (
        not puede_editar_proyectos(usuario)
        or not puede_ver_proyecto(usuario, proyecto)
    ):
        return False

    if es_superadmin(usuario) or es_gerencia(usuario):
        return True

    if es_auditor(usuario) or es_usuario_cliente(usuario):
        return False

    if es_creador_proyecto(usuario):
        creado_por_id = getattr(
            proyecto,
            "creado_por_id",
            None,
        )

        # Mientras Proyecto todavía no tenga creado_por,
        # se utiliza el alcance definido en filtrar_proyectos().
        if creado_por_id is None:
            return True

        return creado_por_id == usuario.pk

    return False


def puede_eliminar_proyecto(
    usuario: AbstractBaseUser | None,
    proyecto,
) -> bool:
    """
    Por política del ERP, solamente los superadministradores
    pueden eliminar proyectos completos.
    """

    return bool(
        es_superadmin(usuario)
        and puede_ver_proyecto(usuario, proyecto)
        and usuario.has_perm(
            "proyecto.delete_proyecto"
        )
    )


def puede_ver_costos_del_proyecto(
    usuario: AbstractBaseUser | None,
    proyecto,
) -> bool:
    """
    Indica si el usuario puede consultar costos,
    precios internos y márgenes del proyecto concreto.
    """

    if not puede_ver_proyecto(usuario, proyecto):
        return False

    return bool(
        es_superadmin(usuario)
        or es_gerencia(usuario)
        or es_auditor(usuario)
    )

# ======================================================
# ARCHIVOS DE PROYECTO
# ======================================================

def puede_ver_archivo_proyecto(
    usuario: AbstractBaseUser | None,
    archivo_proyecto,
) -> bool:
    """
    Indica si un usuario puede consultar
    un archivo asociado a un Proyecto.

    Los archivos activos y retirados forman parte
    del historial documental.

    La visibilidad depende del permiso que el usuario
    tenga sobre el Proyecto correspondiente.
    """

    if not _objeto_guardado(
        archivo_proyecto
    ):
        return False

    proyecto = getattr(
        archivo_proyecto,
        "proyecto",
        None,
    )

    if not proyecto:
        return False

    return puede_ver_proyecto(
        usuario,
        proyecto,
    )


def puede_adjuntar_archivo_proyecto(
    usuario: AbstractBaseUser | None,
    proyecto,
) -> bool:
    """
    Determina si el usuario puede incorporar
    documentación a un Proyecto.

    REGLAS:

    - debe poder consultar el proyecto;
    - proyecto CANCELADO no admite nueva documentación;
    - proyecto FINALIZADO sí admite documentación posterior;
    - superadmin puede adjuntar;
    - gerencia puede adjuntar;
    - creador/gestor de proyectos puede adjuntar;
    - técnico no puede adjuntar por su condición de técnico;
    - auditor no puede adjuntar;
    - cliente no puede adjuntar.
    """

    # ==================================================
    # PROYECTO VÁLIDO
    # ==================================================

    if not _objeto_guardado(
        proyecto
    ):
        return False

    # ==================================================
    # DEBE PODER VER EL PROYECTO
    # ==================================================

    if not puede_ver_proyecto(
        usuario,
        proyecto,
    ):
        return False

    # ==================================================
    # CANCELADO
    # ==================================================

    if (
        proyecto.estado
        == EstadoProyectoChoices.CANCELADO
    ):
        return False

    # ==================================================
    # ROLES DE SOLO LECTURA
    # ==================================================

    if (
        es_auditor(usuario)
        or es_usuario_cliente(usuario)
        or es_tecnico(usuario)
    ):
        return False

    # ==================================================
    # ADMINISTRACIÓN
    # ==================================================

    if (
        es_superadmin(usuario)
        or es_gerencia(usuario)
    ):
        return True

    # ==================================================
    # GESTIÓN DE PROYECTOS
    # ==================================================

    if es_creador_proyecto(usuario):
        return True

    return False


def puede_retirar_archivo_proyecto(
    usuario: AbstractBaseUser | None,
    archivo_proyecto,
) -> bool:
    """
    Determina si el usuario puede retirar lógicamente
    un archivo del historial documental de Proyecto.

    Retirar NO elimina:

    - registro de base de datos;
    - archivo físico;
    - usuario que realizó la carga;
    - fecha documental;
    - created_at.

    Se registra:

    - is_active = False;
    - fecha_retiro;
    - usuario_retiro;
    - motivo_retiro.

    REGLAS:

    - archivo debe existir;
    - archivo debe seguir activo;
    - usuario debe poder ver el Proyecto;
    - Proyecto CANCELADO queda bloqueado;
    - superadmin puede retirar;
    - gerencia puede retirar;
    - creador/gestor de Proyecto puede retirar;
    - técnico no puede retirar;
    - auditor no puede retirar;
    - cliente no puede retirar.
    """

    # ==================================================
    # ARCHIVO VÁLIDO
    # ==================================================

    if not _objeto_guardado(
        archivo_proyecto
    ):
        return False

    # ==================================================
    # YA RETIRADO
    # ==================================================

    if not archivo_proyecto.is_active:
        return False

    # ==================================================
    # PROYECTO
    # ==================================================

    proyecto = getattr(
        archivo_proyecto,
        "proyecto",
        None,
    )

    if not proyecto:
        return False

    # ==================================================
    # VISIBILIDAD
    # ==================================================

    if not puede_ver_proyecto(
        usuario,
        proyecto,
    ):
        return False

    # ==================================================
    # CANCELADO
    # ==================================================

    if (
        proyecto.estado
        == EstadoProyectoChoices.CANCELADO
    ):
        return False

    # ==================================================
    # ROLES SIN PERMISO DE RETIRO
    # ==================================================

    if (
        es_auditor(usuario)
        or es_usuario_cliente(usuario)
        or es_tecnico(usuario)
    ):
        return False

    # ==================================================
    # ADMINISTRACIÓN
    # ==================================================

    if (
        es_superadmin(usuario)
        or es_gerencia(usuario)
    ):
        return True

    # ==================================================
    # GESTIÓN DE PROYECTOS
    # ==================================================

    if es_creador_proyecto(usuario):
        return True

    return False

# ======================================================
# ÓRDENES DE TRABAJO
# ======================================================

def puede_ver_orden_trabajo(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Indica si el usuario puede consultar
    una orden de trabajo concreta.
    """

    if (
        not _usuario_activo(usuario)
        or not _objeto_guardado(orden_trabajo)
        or not puede_ver_ordenes_trabajo(usuario)
    ):
        return False

    queryset = filtrar_ordenes_trabajo(
        usuario,
        orden_trabajo.__class__.objects.all(),
    )

    return _objeto_en_queryset(
        objeto=orden_trabajo,
        queryset=queryset,
    )


def puede_editar_orden_trabajo(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Indica si el usuario puede modificar
    una OT concreta.
    """

    if (
        not puede_editar_ordenes_trabajo(usuario)
        or not puede_ver_orden_trabajo(
            usuario,
            orden_trabajo,
        )
    ):
        return False

    if es_superadmin(usuario) or es_gerencia(usuario):
        return True

    if es_auditor(usuario) or es_usuario_cliente(usuario):
        return False

    if es_tecnico(usuario):
        return orden_trabajo.tecnicos.filter(
            tecnico=usuario,
            is_active=True,
        ).exists()

    if es_creador_proyecto(usuario):
        return orden_trabajo.proyecto_id is not None

    return False


def puede_cerrar_ot(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Indica si el usuario puede finalizar
    una orden de trabajo concreta.
    """

    if (
        not puede_cerrar_orden_trabajo(usuario)
        or not puede_editar_orden_trabajo(
            usuario,
            orden_trabajo,
        )
    ):
        return False

    if orden_trabajo.esta_finalizada:
        return False

    return True


def puede_facturar_ot(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Indica si puede registrarse formalmente
    la facturación de una OT.

    fecha_facturacion puede existir previamente.

    usuario_facturacion es quien determina
    que el hito ya fue registrado.
    """

    if (
        not puede_facturar_orden_trabajo(usuario)
        or not puede_ver_orden_trabajo(
            usuario,
            orden_trabajo,
        )
    ):
        return False

    return bool(
        orden_trabajo.esta_finalizada
        and not orden_trabajo.usuario_facturacion_id
    )


def puede_cobrar_ot(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Indica si puede registrarse formalmente
    el cobro de una OT.

    La facturación debe estar formalmente registrada.

    fecha_cobro puede estar previamente cargada.

    usuario_cobro determina si el hito de cobro
    ya fue registrado.
    """

    if (
        not puede_registrar_cobro_ot(usuario)
        or not puede_ver_orden_trabajo(
            usuario,
            orden_trabajo,
        )
    ):
        return False

    return bool(
        orden_trabajo.usuario_facturacion_id
        and orden_trabajo.fecha_facturacion
        and not orden_trabajo.usuario_cobro_id
    )


def puede_crear_instalacion_desde_ot(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Indica si puede generarse una instalación
    desde una OT.

    Reglas:

    - el usuario debe poder editar la OT;
    - la OT debe ser de tipo INSTALACION;
    - debe estar EN_PROCESO;
    - debe poseer un origen válido;
    - si requiere aprobación comercial,
      debe estar ACEPTADA;
    - no debe tener una instalación generada.
    """

    if not puede_editar_orden_trabajo(
        usuario,
        orden_trabajo,
    ):
        return False

    if (
        orden_trabajo.tipo
        != TipoOrdenTrabajoChoices.INSTALACION
    ):
        return False

    if (
        orden_trabajo.estado
        != EstadoOrdenTrabajoChoices.EN_PROCESO
    ):
        return False

    if (
        orden_trabajo.requiere_aceptacion_cliente
        and not orden_trabajo.fue_aceptada
    ):
        return False

    tiene_origen = bool(
        orden_trabajo.proyecto_id
        or orden_trabajo.servicio_contratado_id
        or orden_trabajo.presupuesto_telecom_id
    )

    return bool(
        tiene_origen
        and not orden_trabajo.tiene_instalacion
    )


def puede_ver_tecnico_ot(
    usuario: AbstractBaseUser | None,
    asignacion,
) -> bool:
    """
    Permite consultar una asignación técnica
    cuando el usuario puede consultar su OT.
    """

    if not _objeto_guardado(
        asignacion
    ):
        return False

    return puede_ver_orden_trabajo(
        usuario,
        asignacion.orden_trabajo,
    )

def puede_ver_seguimiento_ot(
    usuario: AbstractBaseUser | None,
    seguimiento,
) -> bool:
    """
    Permite consultar un seguimiento
    cuando el usuario puede consultar su OT.
    """

    if not _objeto_guardado(
        seguimiento
    ):
        return False

    return puede_ver_orden_trabajo(
        usuario,
        seguimiento.orden_trabajo,
    )

# ======================================================
# ARCHIVOS DE ÓRDENES DE TRABAJO
# ======================================================


def puede_ver_archivo_ot(
    usuario: AbstractBaseUser | None,
    archivo_ot,
) -> bool:
    """
    Indica si un usuario puede consultar
    un archivo asociado a una Orden de Trabajo.

    Se permite consultar tanto archivos activos
    como archivos retirados, ya que estos últimos
    forman parte del historial documental.

    El acceso depende del permiso de lectura
    sobre la OT correspondiente.
    """

    if not _objeto_guardado(
        archivo_ot
    ):
        return False

    orden_trabajo = getattr(
        archivo_ot,
        "orden_trabajo",
        None,
    )

    if not orden_trabajo:
        return False

    return puede_ver_orden_trabajo(
        usuario,
        orden_trabajo,
    )

def puede_adjuntar_archivo_ot(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Indica si el usuario puede adjuntar documentación
    a una Orden de Trabajo.

    Una OT FINALIZADA puede continuar recibiendo
    documentación posterior.

    Una OT CANCELADA queda bloqueada.
    """

    if not _objeto_guardado(
        orden_trabajo
    ):
        return False

    # Debe tener acceso de lectura a la OT.
    if not puede_ver_orden_trabajo(
        usuario,
        orden_trabajo,
    ):
        return False

    # Una OT cancelada no recibe nueva documentación.
    if (
        orden_trabajo.estado
        == EstadoOrdenTrabajoChoices.CANCELADA
    ):
        return False

    # Roles de solo lectura.
    if (
        es_auditor(usuario)
        or es_usuario_cliente(usuario)
    ):
        return False

    # Administración.
    if (
        es_superadmin(usuario)
        or es_gerencia(usuario)
    ):
        return True

    # Técnico únicamente mientras permanezca
    # asignado activamente a la OT.
    if es_tecnico(usuario):
        return orden_trabajo.tecnicos.filter(
            tecnico=usuario,
            is_active=True,
        ).exists()

    # Responsable/creador del proyecto.
    if es_creador_proyecto(usuario):
        return bool(
            orden_trabajo.proyecto_id
        )

    return False

def puede_retirar_archivo_ot(
    usuario: AbstractBaseUser | None,
    archivo_ot,
) -> bool:
    """
    Determina si el usuario puede retirar
    lógicamente un archivo de OT.
    """

    if not _objeto_guardado(
        archivo_ot
    ):
        return False

    if not archivo_ot.is_active:
        return False

    orden_trabajo = getattr(
        archivo_ot,
        "orden_trabajo",
        None,
    )

    if not orden_trabajo:
        return False

    if not puede_ver_orden_trabajo(
        usuario,
        orden_trabajo,
    ):
        return False

    if (
        orden_trabajo.estado
        == EstadoOrdenTrabajoChoices.CANCELADA
    ):
        return False

    if (
        es_auditor(usuario)
        or es_usuario_cliente(usuario)
        or es_tecnico(usuario)
    ):
        return False

    if (
        es_superadmin(usuario)
        or es_gerencia(usuario)
    ):
        return True

    if es_creador_proyecto(usuario):
        return bool(
            orden_trabajo.proyecto_id
        )

    return False

# ======================================================
# TÉCNICOS ASIGNADOS A OT
# ======================================================

def puede_gestionar_tecnicos_ot(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Indica si el usuario puede administrar
    el equipo técnico de una OT.

    Reglas:

    - debe poder ver y editar la OT;
    - auditores y usuarios cliente no administran técnicos;
    - un técnico asignado no obtiene este permiso
      solamente por pertenecer a la OT;
    - superadministración y gerencia pueden gestionar;
    - el creador/gestor de un Proyecto puede gestionar
      las OT pertenecientes a ese Proyecto;
    - una OT finalizada o cancelada no modifica equipo;
    - una vez generada la instalación, el equipo de la OT
      queda congelado.
    """

    if (
        not puede_editar_orden_trabajo(
            usuario,
            orden_trabajo,
        )
    ):
        return False

    if orden_trabajo.estado in {
        EstadoOrdenTrabajoChoices.FINALIZADA,
        EstadoOrdenTrabajoChoices.CANCELADA,
    }:
        return False

    if orden_trabajo.tiene_instalacion:
        return False

    if (
        es_auditor(usuario)
        or es_usuario_cliente(usuario)
    ):
        return False

    # Un técnico puede trabajar sobre la OT,
    # pero no administrar el equipo.
    if es_tecnico(usuario):
        return False

    if (
        es_superadmin(usuario)
        or es_gerencia(usuario)
    ):
        return True

    if es_creador_proyecto(usuario):
        return bool(
            orden_trabajo.proyecto_id
        )

    return False


def puede_asignar_tecnico_ot(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Indica si puede asignarse un técnico
    a la OT.
    """

    return puede_gestionar_tecnicos_ot(
        usuario,
        orden_trabajo,
    )


def puede_establecer_tecnico_principal_ot(
    usuario: AbstractBaseUser | None,
    asignacion,
) -> bool:
    """
    Indica si una asignación puede convertirse
    en técnico principal.
    """

    if not _objeto_guardado(
        asignacion
    ):
        return False

    if not asignacion.is_active:
        return False

    return puede_gestionar_tecnicos_ot(
        usuario,
        asignacion.orden_trabajo,
    )


def puede_desasignar_tecnico_ot(
    usuario: AbstractBaseUser | None,
    asignacion,
) -> bool:
    """
    Indica si puede desasignarse formalmente
    un técnico de una OT.

    No elimina el registro.
    """

    if not _objeto_guardado(
        asignacion
    ):
        return False

    if not asignacion.is_active:
        return False

    return puede_gestionar_tecnicos_ot(
        usuario,
        asignacion.orden_trabajo,
    )

# ======================================================
# SEGUIMIENTOS DE OT
# ======================================================

def puede_registrar_seguimiento_ot(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Indica si el usuario puede registrar
    un nuevo seguimiento operativo.

    Los seguimientos son históricos:

    - se agregan;
    - no se modifican;
    - no se eliminan desde el flujo funcional.

    Pueden registrar seguimiento:

    - superadministración;
    - gerencia;
    - creador/gestor del Proyecto;
    - técnicos actualmente asignados a la OT.
    """

    if not puede_editar_orden_trabajo(
        usuario,
        orden_trabajo,
    ):
        return False

    if orden_trabajo.estado in {
        EstadoOrdenTrabajoChoices.FINALIZADA,
        EstadoOrdenTrabajoChoices.CANCELADA,
    }:
        return False

    if (
        es_auditor(usuario)
        or es_usuario_cliente(usuario)
    ):
        return False

    if (
        es_superadmin(usuario)
        or es_gerencia(usuario)
    ):
        return True

    if es_tecnico(usuario):
        return orden_trabajo.tecnicos.filter(
            tecnico=usuario,
            is_active=True,
        ).exists()

    if es_creador_proyecto(usuario):
        return bool(
            orden_trabajo.proyecto_id
        )

    return False

# ======================================================
# INSTALACIONES
# ======================================================

def puede_ver_instalacion(
    usuario: AbstractBaseUser | None,
    instalacion,
) -> bool:
    """
    Indica si el usuario puede consultar
    una instalación concreta.
    """

    if (
        not _usuario_activo(usuario)
        or not _objeto_guardado(instalacion)
        or not puede_ver_instalaciones(usuario)
    ):
        return False

    queryset = filtrar_instalaciones(
        usuario,
        instalacion.__class__.objects.all(),
    )

    return _objeto_en_queryset(
        objeto=instalacion,
        queryset=queryset,
    )


def puede_editar_instalacion(
    usuario: AbstractBaseUser | None,
    instalacion,
) -> bool:
    """
    Indica si el usuario puede modificar
    una instalación concreta.
    """

    if (
        not puede_editar_instalaciones(usuario)
        or not puede_ver_instalacion(
            usuario,
            instalacion,
        )
    ):
        return False

    if es_superadmin(usuario) or es_gerencia(usuario):
        return True

    if es_auditor(usuario) or es_usuario_cliente(usuario):
        return False

    if es_tecnico(usuario):
        return bool(
            instalacion.tecnicos.filter(
                usuario=usuario,
                is_active=True,
            ).exists()
            or instalacion.orden_trabajo.tecnicos.filter(
                tecnico=usuario,
                is_active=True,
            ).exists()
        )

    return False


def puede_finalizar_instalacion_concreta(
    usuario: AbstractBaseUser | None,
    instalacion,
) -> bool:
    """
    Indica si el usuario puede finalizar
    una instalación concreta.

    La instalación debe estar formalmente
    EN_PROCESO.

    La existencia previa de fecha_inicio no determina
    por sí sola que el hito de inicio haya sido ejecutado.
    """

    if (
        not puede_finalizar_instalacion(usuario)
        or not puede_editar_instalacion(
            usuario,
            instalacion,
        )
    ):
        return False

    return (
        instalacion.estado
        == EstadoInstalacionChoices.EN_PROCESO
    )

def puede_programar_instalacion_concreta(
    usuario: AbstractBaseUser | None,
    instalacion,
) -> bool:
    """
    Indica si una instalación puede pasar
    de PENDIENTE a PROGRAMADA.
    """

    if not puede_editar_instalacion(
        usuario,
        instalacion,
    ):
        return False

    return (
        instalacion.estado
        == EstadoInstalacionChoices.PENDIENTE
    )


def puede_iniciar_instalacion_concreta(
    usuario: AbstractBaseUser | None,
    instalacion,
) -> bool:
    """
    Indica si una instalación programada
    puede comenzar su ejecución.
    """

    if not puede_editar_instalacion(
        usuario,
        instalacion,
    ):
        return False

    return (
        instalacion.estado
        == EstadoInstalacionChoices.PROGRAMADA
    )


def puede_cancelar_instalacion_concreta(
    usuario: AbstractBaseUser | None,
    instalacion,
) -> bool:
    """
    Indica si una instalación puede cancelarse.
    """

    if not puede_editar_instalacion(
        usuario,
        instalacion,
    ):
        return False

    return instalacion.estado in {
        EstadoInstalacionChoices.PENDIENTE,
        EstadoInstalacionChoices.PROGRAMADA,
        EstadoInstalacionChoices.EN_PROCESO,
    }


def puede_registrar_conformidad_instalacion(
    usuario: AbstractBaseUser | None,
    instalacion,
) -> bool:
    """
    Indica si puede registrarse formalmente
    la conformidad de una instalación.

    La instalación debe estar FINALIZADA.

    fecha_conformidad puede cargarse previamente.

    usuario_conformidad determina si el hito
    ya fue formalmente registrado.
    """

    if not puede_editar_instalacion(
        usuario,
        instalacion,
    ):
        return False

    if (
        instalacion.estado
        != EstadoInstalacionChoices.FINALIZADA
    ):
        return False

    if instalacion.usuario_conformidad_id:
        return False

    return True

def puede_ver_credenciales_instalacion(
    usuario: AbstractBaseUser | None,
    instalacion,
) -> bool:
    """
    Indica si el usuario puede consultar las credenciales
    técnicas de los dispositivos de una instalación.
    """

    if not puede_ver_instalacion(usuario, instalacion):
        return False

    return bool(
        es_superadmin(usuario)
        or es_gerencia(usuario)
        or es_tecnico(usuario)
    )


# ======================================================
# USUARIOS CLIENTE
# ======================================================

def puede_ver_cuenta_cliente(
    usuario: AbstractBaseUser | None,
    cuenta_cliente,
) -> bool:
    """
    Indica si un usuario puede consultar una cuenta concreta.
    """

    if (
        not _usuario_activo(usuario)
        or not _objeto_guardado(cuenta_cliente)
    ):
        return False

    if es_superadmin(usuario) or es_gerencia(usuario) or es_auditor(usuario):
        return True

    if es_usuario_cliente(usuario):
        return (
            getattr(
                usuario,
                "cuenta_cliente_id",
                None,
            )
            == cuenta_cliente.pk
        )

    return False


def puede_ver_sucursal(
    usuario: AbstractBaseUser | None,
    sucursal,
) -> bool:
    """
    Indica si un usuario puede consultar
    una sucursal concreta.
    """

    if (
        not _usuario_activo(usuario)
        or not _objeto_guardado(sucursal)
    ):
        return False

    if es_superadmin(usuario) or es_gerencia(usuario) or es_auditor(usuario):
        return True

    if not es_usuario_cliente(usuario):
        return False

    if (
        getattr(
            usuario,
            "cuenta_cliente_id",
            None,
        )
        != sucursal.cuenta_cliente_id
    ):
        return False

    sucursal_usuario_id = getattr(
        usuario,
        "sucursal_id",
        None,
    )

    return bool(
        not sucursal_usuario_id
        or sucursal_usuario_id == sucursal.pk
    )

# ======================================================
# TRANSICIONES DE ÓRDENES DE TRABAJO
# ======================================================

def puede_registrar_recepcion_ot(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Indica si puede registrarse formalmente
    la recepción de una OT.

    La fecha puede estar cargada previamente.

    El hito se considera registrado cuando existe
    usuario_recepcion_solicitud.
    """

    if not puede_editar_orden_trabajo(
        usuario,
        orden_trabajo,
    ):
        return False

    if (
        orden_trabajo.estado
        != EstadoOrdenTrabajoChoices.BORRADOR
    ):
        return False

    if orden_trabajo.usuario_recepcion_solicitud_id:
        return False

    return True

def puede_programar_ot(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Indica si una OT puede programarse.

    No exige que fecha_programada esté previamente
    guardada.

    Al presionar Programar:

    1. se utilizará la fecha escrita en el Admin;
    2. si no existe, la previamente guardada;
    3. si tampoco existe, la fecha/hora actual.
    """

    if not puede_editar_orden_trabajo(
        usuario,
        orden_trabajo,
    ):
        return False

    return (
        orden_trabajo.estado
        in {
            EstadoOrdenTrabajoChoices.BORRADOR,
            EstadoOrdenTrabajoChoices.PENDIENTE,
        }
    )

def puede_registrar_envio_ot(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Indica si puede registrarse el envío
    comercial al cliente.

    La fecha puede estar precargada.

    El envío se considera registrado cuando existe
    usuario_envio_cliente.

    Una OT generada desde Proyecto aprobado ya hereda
    fecha y usuario de envío, por lo que esta acción
    no vuelve a estar disponible.
    """

    if not puede_editar_orden_trabajo(
        usuario,
        orden_trabajo,
    ):
        return False

    if not orden_trabajo.requiere_aceptacion_cliente:
        return False

    if not orden_trabajo.fecha_recepcion_solicitud:
        return False

    # Envío ya confirmado o heredado.
    if orden_trabajo.usuario_envio_cliente_id:
        return False

    return orden_trabajo.estado in {
        EstadoOrdenTrabajoChoices.PENDIENTE,
        EstadoOrdenTrabajoChoices.PROGRAMADA,
    }

def puede_registrar_respuesta_ot(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Indica si puede registrarse formalmente
    la respuesta del cliente.

    Aplica tanto a aceptación como rechazo.

    fecha_aceptacion puede estar previamente cargada.

    usuario_aceptacion indica que la respuesta
    ya fue formalmente registrada.
    """

    if not puede_editar_orden_trabajo(
        usuario,
        orden_trabajo,
    ):
        return False

    if not orden_trabajo.requiere_aceptacion_cliente:
        return False

    # El envío debe haber sido confirmado.
    if not orden_trabajo.usuario_envio_cliente_id:
        return False

    # Ya existe una respuesta registrada formalmente.
    if orden_trabajo.usuario_aceptacion_id:
        return False

    return (
        orden_trabajo.estado_aceptacion
        == EstadoAceptacionOTChoices.PENDIENTE
    )

def puede_registrar_aceptacion_ot(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Alias semántico para la aceptación del cliente.
    """

    return puede_registrar_respuesta_ot(
        usuario,
        orden_trabajo,
    )

def puede_registrar_rechazo_ot(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Alias semántico para el rechazo del cliente.
    """

    return puede_registrar_respuesta_ot(
        usuario,
        orden_trabajo,
    )

def puede_registrar_envio_ot(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Indica si puede registrarse formalmente
    el envío comercial al cliente.

    La fecha de envío puede estar cargada previamente.

    El hito se considera registrado cuando existe
    usuario_envio_cliente.
    """

    if not puede_editar_orden_trabajo(
        usuario,
        orden_trabajo,
    ):
        return False

    if not orden_trabajo.requiere_aceptacion_cliente:
        return False

    # La recepción debe estar formalmente registrada.
    if not orden_trabajo.usuario_recepcion_solicitud_id:
        return False

    # El envío ya fue formalmente registrado.
    if orden_trabajo.usuario_envio_cliente_id:
        return False

    return (
        orden_trabajo.estado
        in {
            EstadoOrdenTrabajoChoices.PENDIENTE,
            EstadoOrdenTrabajoChoices.PROGRAMADA,
        }
    )

def puede_iniciar_ot(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Indica si una OT puede iniciarse.

    Proyecto y PresupuestoTelecom requieren
    aceptación previa del cliente.

    Una OT asociada únicamente a ServicioContratado
    no requiere aprobación comercial.
    """

    if not puede_editar_orden_trabajo(
        usuario,
        orden_trabajo,
    ):
        return False

    if orden_trabajo.estado not in {
        EstadoOrdenTrabajoChoices.PENDIENTE,
        EstadoOrdenTrabajoChoices.PROGRAMADA,
    }:
        return False

    if (
        orden_trabajo.requiere_aceptacion_cliente
        and not orden_trabajo.fue_aceptada
    ):
        return False

    return True


def puede_pausar_ot(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Indica si una OT puede pausarse.
    """

    if not puede_editar_orden_trabajo(
        usuario,
        orden_trabajo,
    ):
        return False

    return (
        orden_trabajo.estado
        == EstadoOrdenTrabajoChoices.EN_PROCESO
    )


def puede_reanudar_ot(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Indica si una OT pausada puede reanudarse.
    """

    if not puede_editar_orden_trabajo(
        usuario,
        orden_trabajo,
    ):
        return False

    return (
        orden_trabajo.estado
        == EstadoOrdenTrabajoChoices.PAUSADA
    )


def puede_finalizar_ot(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Indica si una OT puede finalizarse.

    Para una OT de tipo INSTALACION:

    - debe existir la instalación;
    - la instalación debe estar FINALIZADA.
    """

    if not puede_cerrar_ot(
        usuario,
        orden_trabajo,
    ):
        return False

    if (
        orden_trabajo.estado
        != EstadoOrdenTrabajoChoices.EN_PROCESO
    ):
        return False

    if (
        orden_trabajo.tipo
        == TipoOrdenTrabajoChoices.INSTALACION
    ):
        if not orden_trabajo.tiene_instalacion:
            return False

        if (
            orden_trabajo.instalacion.estado
            != EstadoInstalacionChoices.FINALIZADA
        ):
            return False

    return True

def puede_generar_ot_desde_proyecto(
    usuario,
    proyecto,
) -> bool:
    """
    Determina si el usuario puede generar una OT
    desde un proyecto.

    Requisitos:

    - poder editar el proyecto;
    - proyecto aprobado;
    - al menos un detalle activo.
    """

    if not puede_editar_proyecto(
        usuario,
        proyecto,
    ):
        return False

    if not proyecto.aprobado:
        return False

    if not proyecto.detalles.filter(
        is_active=True,
    ).exists():
        return False

    return True

def puede_registrar_recepcion_proyecto(
    usuario,
    proyecto,
) -> bool:
    """
    Permite confirmar la recepción de la solicitud.

    La fecha puede haber sido cargada previamente.
    El hito se considera registrado cuando existe
    usuario_recepcion_solicitud.
    """

    if not puede_editar_proyecto(
        usuario,
        proyecto,
    ):
        return False

    if (
        proyecto.estado
        != EstadoProyectoChoices.BORRADOR
    ):
        return False

    # El hito ya fue confirmado.
    if proyecto.usuario_recepcion_solicitud_id:
        return False

    return True

def puede_planificar_proyecto(
    usuario,
    proyecto,
) -> bool:
    """
    Permite planificar un proyecto cuya recepción
    ya fue registrada.

    La fecha planificada puede estar escrita en el
    formulario aunque todavía no haya sido guardada.
    """

    if not puede_editar_proyecto(
        usuario,
        proyecto,
    ):
        return False

    return bool(
        proyecto.estado
        == EstadoProyectoChoices.BORRADOR
        and proyecto.usuario_recepcion_solicitud_id
    )


def puede_registrar_envio_proyecto(
    usuario,
    proyecto,
) -> bool:
    """
    Permite registrar el envío del proyecto al cliente.

    La fecha puede cargarse previamente.
    El hito se considera registrado cuando existe
    usuario_envio_cliente.
    """

    if not puede_editar_proyecto(
        usuario,
        proyecto,
    ):
        return False

    if (
        proyecto.estado
        != EstadoProyectoChoices.PLANIFICADO
    ):
        return False

    if proyecto.usuario_envio_cliente_id:
        return False

    return True

def puede_registrar_respuesta_proyecto(
    usuario: AbstractBaseUser | None,
    proyecto,
) -> bool:
    """
    Permite registrar aceptación o rechazo
    mientras el proyecto esté pendiente de aprobación.
    """

    if not puede_editar_proyecto(
        usuario,
        proyecto,
    ):
        return False

    return bool(
        proyecto.estado
        == EstadoProyectoChoices.PENDIENTE_APROBACION
        and proyecto.fecha_envio_cliente
        and proyecto.respuesta_cliente
        == RespuestaClienteProyectoChoices.PENDIENTE
    )


def puede_registrar_aceptacion_proyecto(
    usuario: AbstractBaseUser | None,
    proyecto,
) -> bool:
    return puede_registrar_respuesta_proyecto(
        usuario,
        proyecto,
    )


def puede_registrar_rechazo_proyecto(
    usuario: AbstractBaseUser | None,
    proyecto,
) -> bool:
    return puede_registrar_respuesta_proyecto(
        usuario,
        proyecto,
    )

def puede_finalizar_proyecto(
    usuario: AbstractBaseUser | None,
    proyecto,
) -> bool:
    """
    Indica si un Proyecto puede finalizarse.

    Reglas:

    - el usuario debe poder editar el Proyecto;
    - debe estar APROBADO o EN_EJECUCION;
    - debe tener al menos una OT;
    - todas las OT deben estar FINALIZADA o CANCELADA.
    """

    if not puede_editar_proyecto(
        usuario,
        proyecto,
    ):
        return False

    if proyecto.estado not in {
        EstadoProyectoChoices.APROBADO,
        EstadoProyectoChoices.EN_EJECUCION,
    }:
        return False

    ordenes = proyecto.ordenes_trabajo.all()

    if not ordenes.exists():
        return False

    estados_cerrados = {
        EstadoOrdenTrabajoChoices.FINALIZADA,
        EstadoOrdenTrabajoChoices.CANCELADA,
    }

    existen_ordenes_abiertas = (
        ordenes
        .exclude(
            estado__in=estados_cerrados,
        )
        .exists()
    )

    if existen_ordenes_abiertas:
        return False

    return True