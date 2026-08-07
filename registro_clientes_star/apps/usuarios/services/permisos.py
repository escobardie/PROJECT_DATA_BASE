from django.contrib.auth.models import AbstractBaseUser

from .roles import (
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
    Indica si el objeto representa un usuario
    autenticado y activo.
    """

    return bool(
        usuario
        and usuario.is_authenticated
        and usuario.is_active
    )


def tiene_permiso(
    usuario: AbstractBaseUser | None,
    permiso: str,
) -> bool:
    """
    Comprueba un permiso de Django.

    El permiso debe utilizar el formato:

        app_label.codename

    Ejemplo:

        proyecto.add_proyecto
        orden_trabajo.change_ordentrabajo
    """

    if not _usuario_activo(usuario):
        return False

    return bool(
        es_superadmin(usuario)
        or usuario.has_perm(permiso)
    )


def tiene_permisos(
    usuario: AbstractBaseUser | None,
    permisos: tuple[str, ...] | list[str] | set[str],
) -> bool:
    """
    Indica si el usuario posee todos los permisos indicados.
    """

    if not _usuario_activo(usuario):
        return False

    return all(
        tiene_permiso(usuario, permiso)
        for permiso in permisos
    )


def tiene_algun_permiso(
    usuario: AbstractBaseUser | None,
    permisos: tuple[str, ...] | list[str] | set[str],
) -> bool:
    """
    Indica si el usuario posee al menos uno
    de los permisos indicados.
    """

    if not _usuario_activo(usuario):
        return False

    return any(
        tiene_permiso(usuario, permiso)
        for permiso in permisos
    )


# ======================================================
# PERMISOS DE CLIENTES Y SUCURSALES
# ======================================================

def puede_ver_clientes(
    usuario: AbstractBaseUser | None,
) -> bool:
    """
    Indica si el usuario puede consultar cuentas cliente.

    El alcance concreto de los registros debe aplicarse
    posteriormente mediante filtros de QuerySet.
    """

    return tiene_permiso(
        usuario,
        "cuenta_cliente.view_cuentacliente",
    )


def puede_crear_clientes(
    usuario: AbstractBaseUser | None,
) -> bool:
    return tiene_permiso(
        usuario,
        "cuenta_cliente.add_cuentacliente",
    )


def puede_editar_clientes(
    usuario: AbstractBaseUser | None,
) -> bool:
    return tiene_permiso(
        usuario,
        "cuenta_cliente.change_cuentacliente",
    )


def puede_ver_sucursales(
    usuario: AbstractBaseUser | None,
) -> bool:
    return tiene_permiso(
        usuario,
        "cuenta_cliente.view_sucursal",
    )


# ======================================================
# PERMISOS DE PROYECTOS
# ======================================================

def puede_ver_proyectos(
    usuario: AbstractBaseUser | None,
) -> bool:
    return tiene_permiso(
        usuario,
        "proyecto.view_proyecto",
    )


def puede_crear_proyectos(
    usuario: AbstractBaseUser | None,
) -> bool:
    """
    La autorización se concede mediante el permiso Django.

    El grupo CREADORES_PROYECTO recibe este permiso
    desde el comando crear_roles.
    """

    return bool(
        tiene_permiso(
            usuario,
            "proyecto.add_proyecto",
        )
        and (
            es_superadmin(usuario)
            or es_gerencia(usuario)
            or es_creador_proyecto(usuario)
        )
    )


def puede_editar_proyectos(
    usuario: AbstractBaseUser | None,
) -> bool:
    return tiene_permiso(
        usuario,
        "proyecto.change_proyecto",
    )


def puede_eliminar_proyectos(
    usuario: AbstractBaseUser | None,
) -> bool:
    """
    Por política del ERP, solamente un superadministrador
    puede eliminar proyectos completos.
    """

    return bool(
        es_superadmin(usuario)
        and tiene_permiso(
            usuario,
            "proyecto.delete_proyecto",
        )
    )


def puede_ver_costos_proyecto(
    usuario: AbstractBaseUser | None,
) -> bool:
    """
    Indica si el usuario puede consultar costos,
    precios internos y márgenes de proyectos.
    """

    return bool(
        _usuario_activo(usuario)
        and (
            es_superadmin(usuario)
            or es_gerencia(usuario)
            or es_auditor(usuario)
        )
    )


# ======================================================
# PERMISOS DE ÓRDENES DE TRABAJO
# ======================================================

def puede_ver_ordenes_trabajo(
    usuario: AbstractBaseUser | None,
) -> bool:
    return tiene_permiso(
        usuario,
        "orden_trabajo.view_ordentrabajo",
    )


def puede_crear_ordenes_trabajo(
    usuario: AbstractBaseUser | None,
) -> bool:
    return tiene_permiso(
        usuario,
        "orden_trabajo.add_ordentrabajo",
    )


def puede_editar_ordenes_trabajo(
    usuario: AbstractBaseUser | None,
) -> bool:
    return tiene_permiso(
        usuario,
        "orden_trabajo.change_ordentrabajo",
    )


def puede_cerrar_orden_trabajo(
    usuario: AbstractBaseUser | None,
) -> bool:
    """
    Indica si el usuario puede registrar la finalización
    operativa de una orden.

    Técnicos, gerencia y superadministradores pueden hacerlo,
    siempre que tengan permiso de modificación.
    """

    return bool(
        puede_editar_ordenes_trabajo(usuario)
        and (
            es_superadmin(usuario)
            or es_gerencia(usuario)
            or es_tecnico(usuario)
        )
    )


def puede_asignar_tecnicos_ot(
    usuario: AbstractBaseUser | None,
) -> bool:
    """
    Indica si el usuario puede gestionar técnicos
    asignados a órdenes de trabajo.
    """

    return tiene_algun_permiso(
        usuario,
        {
            "orden_trabajo.add_ordentrabajotecnico",
            "orden_trabajo.change_ordentrabajotecnico",
        },
    )


def puede_agregar_seguimiento_ot(
    usuario: AbstractBaseUser | None,
) -> bool:
    return tiene_permiso(
        usuario,
        "orden_trabajo.add_ordentrabajoseguimiento",
    )


def puede_subir_archivo_ot(
    usuario: AbstractBaseUser | None,
) -> bool:
    return tiene_permiso(
        usuario,
        "orden_trabajo.add_ordentrabajoarchivo",
    )


def puede_facturar_orden_trabajo(
    usuario: AbstractBaseUser | None,
) -> bool:
    """
    Indica si el usuario puede registrar
    la facturación de una OT.
    """

    return bool(
        _usuario_activo(usuario)
        and (
            es_superadmin(usuario)
            or es_gerencia(usuario)
        )
        and puede_editar_ordenes_trabajo(usuario)
    )


def puede_registrar_cobro_ot(
    usuario: AbstractBaseUser | None,
) -> bool:
    """
    Indica si el usuario puede registrar el cobro
    de una orden de trabajo.
    """

    return puede_facturar_orden_trabajo(usuario)


# ======================================================
# PERMISOS DE INSTALACIONES
# ======================================================

def puede_ver_instalaciones(
    usuario: AbstractBaseUser | None,
) -> bool:
    return tiene_permiso(
        usuario,
        "instalacion.view_instalacion",
    )


def puede_crear_instalaciones(
    usuario: AbstractBaseUser | None,
) -> bool:
    return tiene_permiso(
        usuario,
        "instalacion.add_instalacion",
    )


def puede_editar_instalaciones(
    usuario: AbstractBaseUser | None,
) -> bool:
    return tiene_permiso(
        usuario,
        "instalacion.change_instalacion",
    )


def puede_finalizar_instalacion(
    usuario: AbstractBaseUser | None,
) -> bool:
    """
    Técnicos, gerencia y superadministradores pueden
    registrar la finalización de una instalación.
    """

    return bool(
        puede_editar_instalaciones(usuario)
        and (
            es_superadmin(usuario)
            or es_gerencia(usuario)
            or es_tecnico(usuario)
        )
    )


def puede_gestionar_dispositivos_instalados(
    usuario: AbstractBaseUser | None,
) -> bool:
    return tiene_algun_permiso(
        usuario,
        {
            "instalacion.add_instalaciondispositivo",
            "instalacion.change_instalaciondispositivo",
        },
    )


def puede_ver_credenciales_dispositivo(
    usuario: AbstractBaseUser | None,
) -> bool:
    """
    Restringe la visualización de credenciales técnicas.

    Los usuarios cliente, proveedores y auditores
    no acceden a contraseñas de dispositivos.
    """

    return bool(
        _usuario_activo(usuario)
        and not es_usuario_cliente(usuario)
        and (
            es_superadmin(usuario)
            or es_gerencia(usuario)
            or es_tecnico(usuario)
        )
    )


# ======================================================
# PERMISOS DE CATÁLOGO Y DISPOSITIVOS
# ======================================================

def puede_ver_catalogo(
    usuario: AbstractBaseUser | None,
) -> bool:
    return tiene_permiso(
        usuario,
        "catalogo.view_itemcatalogo",
    )


def puede_editar_catalogo(
    usuario: AbstractBaseUser | None,
) -> bool:
    return tiene_permiso(
        usuario,
        "catalogo.change_itemcatalogo",
    )


def puede_ver_dispositivos(
    usuario: AbstractBaseUser | None,
) -> bool:
    return tiene_permiso(
        usuario,
        "dispositivo.view_dispositivo",
    )


def puede_editar_dispositivos(
    usuario: AbstractBaseUser | None,
) -> bool:
    return tiene_permiso(
        usuario,
        "dispositivo.change_dispositivo",
    )


# ======================================================
# PERMISOS DE USUARIOS
# ======================================================

def puede_ver_usuarios(
    usuario: AbstractBaseUser | None,
) -> bool:
    return tiene_permiso(
        usuario,
        "usuarios.view_usuario",
    )


def puede_crear_usuarios(
    usuario: AbstractBaseUser | None,
) -> bool:
    return tiene_permiso(
        usuario,
        "usuarios.add_usuario",
    )


def puede_editar_usuarios(
    usuario: AbstractBaseUser | None,
) -> bool:
    return tiene_permiso(
        usuario,
        "usuarios.change_usuario",
    )


def puede_administrar_roles(
    usuario: AbstractBaseUser | None,
) -> bool:
    """
    Solamente un superadministrador puede cambiar
    grupos, permisos individuales o privilegios elevados.
    """

    return es_superadmin(usuario)