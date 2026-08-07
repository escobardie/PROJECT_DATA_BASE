from collections.abc import Collection

from django.contrib.auth.models import AbstractBaseUser


# ======================================================
# NOMBRES DE ROLES
# ======================================================

ROL_SUPERADMIN = "SUPERADMIN"
ROL_GERENCIA = "GERENCIA"
ROL_AUDITORES = "AUDITORES"
ROL_TECNICOS = "TECNICOS"
ROL_USUARIOS_CLIENTE = "USUARIOS_CLIENTE"
ROL_PROVEEDORES = "PROVEEDORES"
ROL_CREADORES_PROYECTO = "CREADORES_PROYECTO"


ROLES_INTERNOS = frozenset(
    {
        ROL_SUPERADMIN,
        ROL_GERENCIA,
        ROL_AUDITORES,
        ROL_TECNICOS,
        ROL_CREADORES_PROYECTO,
    }
)

ROLES_EXTERNOS = frozenset(
    {
        ROL_USUARIOS_CLIENTE,
        ROL_PROVEEDORES,
    }
)

ROLES_DISPONIBLES = frozenset(
    {
        *ROLES_INTERNOS,
        *ROLES_EXTERNOS,
    }
)


# ======================================================
# FUNCIONES INTERNAS
# ======================================================

def _usuario_autenticado(usuario: AbstractBaseUser | None) -> bool:
    """
    Indica si el objeto representa un usuario autenticado.
    """

    return bool(
        usuario
        and usuario.is_authenticated
    )


def obtener_nombres_grupos(
    usuario: AbstractBaseUser | None,
) -> set[str]:
    """
    Devuelve los nombres de los grupos del usuario.

    Si la relación ``groups`` fue precargada mediante
    ``prefetch_related()``, Django reutilizará dicha caché.
    """

    if not _usuario_autenticado(usuario):
        return set()

    return set(
        usuario.groups.values_list(
            "name",
            flat=True,
        )
    )


# ======================================================
# COMPROBACIONES GENERALES
# ======================================================

def pertenece_a_grupo(
    usuario: AbstractBaseUser | None,
    nombre_grupo: str,
) -> bool:
    """
    Indica si el usuario pertenece al grupo indicado.
    """

    if not _usuario_autenticado(usuario):
        return False

    return usuario.groups.filter(
        name=nombre_grupo,
    ).exists()


def pertenece_a_alguno(
    usuario: AbstractBaseUser | None,
    nombres_grupos: Collection[str],
) -> bool:
    """
    Indica si el usuario pertenece al menos
    a uno de los grupos proporcionados.
    """

    if not _usuario_autenticado(usuario):
        return False

    return usuario.groups.filter(
        name__in=nombres_grupos,
    ).exists()


def pertenece_a_todos(
    usuario: AbstractBaseUser | None,
    nombres_grupos: Collection[str],
) -> bool:
    """
    Indica si el usuario pertenece a todos
    los grupos proporcionados.
    """

    if not _usuario_autenticado(usuario):
        return False

    grupos_requeridos = set(nombres_grupos)

    if not grupos_requeridos:
        return True

    grupos_usuario = obtener_nombres_grupos(usuario)

    return grupos_requeridos.issubset(grupos_usuario)


# ======================================================
# ROLES ESPECÍFICOS
# ======================================================

def es_superadmin(
    usuario: AbstractBaseUser | None,
) -> bool:
    """
    Indica si el usuario es superusuario de Django
    o pertenece al grupo SUPERADMIN.
    """

    if not _usuario_autenticado(usuario):
        return False

    return bool(
        usuario.is_superuser
        or pertenece_a_grupo(
            usuario,
            ROL_SUPERADMIN,
        )
    )


def es_gerencia(
    usuario: AbstractBaseUser | None,
) -> bool:
    return pertenece_a_grupo(
        usuario,
        ROL_GERENCIA,
    )


def es_auditor(
    usuario: AbstractBaseUser | None,
) -> bool:
    return pertenece_a_grupo(
        usuario,
        ROL_AUDITORES,
    )


def es_tecnico(
    usuario: AbstractBaseUser | None,
) -> bool:
    return pertenece_a_grupo(
        usuario,
        ROL_TECNICOS,
    )


def es_usuario_cliente(
    usuario: AbstractBaseUser | None,
) -> bool:
    return pertenece_a_grupo(
        usuario,
        ROL_USUARIOS_CLIENTE,
    )


def es_proveedor(
    usuario: AbstractBaseUser | None,
) -> bool:
    return pertenece_a_grupo(
        usuario,
        ROL_PROVEEDORES,
    )


def es_creador_proyecto(
    usuario: AbstractBaseUser | None,
) -> bool:
    return pertenece_a_grupo(
        usuario,
        ROL_CREADORES_PROYECTO,
    )


# ======================================================
# CLASIFICACIÓN GENERAL
# ======================================================

def es_usuario_interno(
    usuario: AbstractBaseUser | None,
) -> bool:
    """
    Indica si el usuario pertenece a algún rol interno.
    """

    if es_superadmin(usuario):
        return True

    return pertenece_a_alguno(
        usuario,
        ROLES_INTERNOS,
    )


def es_usuario_externo(
    usuario: AbstractBaseUser | None,
) -> bool:
    """
    Indica si el usuario pertenece a algún rol externo.
    """

    return pertenece_a_alguno(
        usuario,
        ROLES_EXTERNOS,
    )


def tiene_acceso_global(
    usuario: AbstractBaseUser | None,
) -> bool:
    """
    Indica si el usuario puede trabajar inicialmente
    con información de todas las cuentas.

    La autorización concreta seguirá dependiendo
    de los permisos de Django y de cada operación.
    """

    return bool(
        es_superadmin(usuario)
        or es_gerencia(usuario)
        or es_auditor(usuario)
    )