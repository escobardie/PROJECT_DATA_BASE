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
    Indica si el usuario puede registrar
    la facturación de una OT concreta.
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
        and not orden_trabajo.esta_facturada
    )


def puede_cobrar_ot(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Indica si el usuario puede registrar
    el cobro de una OT concreta.
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
        orden_trabajo.esta_facturada
        and not orden_trabajo.esta_cobrada
    )


def puede_crear_instalacion_desde_ot(
    usuario: AbstractBaseUser | None,
    orden_trabajo,
) -> bool:
    """
    Indica si puede crearse una instalación
    como resultado de una OT.

    Reglas:

    - el usuario debe poder editar la OT;
    - la OT no debe tener ya una instalación;
    - la OT debe tener un origen válido;
    - la OT no debe encontrarse finalizada.
    """

    if not puede_editar_orden_trabajo(
        usuario,
        orden_trabajo,
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
        and not orden_trabajo.esta_finalizada
    )


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
            ).exists()
            or instalacion.orden_trabajo.tecnicos.filter(
                tecnico=usuario,
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
    """

    if (
        not puede_finalizar_instalacion(usuario)
        or not puede_editar_instalacion(
            usuario,
            instalacion,
        )
    ):
        return False

    return bool(
        not instalacion.finalizada
        and not instalacion.cancelada
        and instalacion.fecha_inicio
    )


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