from typing import TypeVar

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import Q, QuerySet

from .roles import (
    es_creador_proyecto,
    es_tecnico,
    es_usuario_cliente,
    tiene_acceso_global,
)


ModelType = TypeVar("ModelType")


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


def _sin_resultados(
    queryset: QuerySet[ModelType],
) -> QuerySet[ModelType]:
    """
    Devuelve un QuerySet vacío conservando
    el modelo y la configuración original.
    """

    return queryset.none()


def _cuenta_cliente_id(
    usuario: AbstractBaseUser,
) -> int | None:
    """
    Devuelve la cuenta cliente asignada al usuario.
    """

    return getattr(
        usuario,
        "cuenta_cliente_id",
        None,
    )


def _sucursal_id(
    usuario: AbstractBaseUser,
) -> int | None:
    """
    Devuelve la sucursal asignada al usuario.
    """

    return getattr(
        usuario,
        "sucursal_id",
        None,
    )


# ======================================================
# CUENTAS CLIENTE
# ======================================================

def filtrar_cuentas_cliente(
    usuario: AbstractBaseUser | None,
    queryset: QuerySet[ModelType],
) -> QuerySet[ModelType]:
    """
    Filtra las cuentas cliente visibles para el usuario.

    Acceso global:
        todas las cuentas.

    Usuario cliente:
        únicamente su cuenta asignada.

    Otros usuarios:
        sin resultados, salvo que posteriormente se defina
        una política específica.
    """

    if not _usuario_activo(usuario):
        return _sin_resultados(queryset)

    if tiene_acceso_global(usuario):
        return queryset

    if es_usuario_cliente(usuario):
        cuenta_id = _cuenta_cliente_id(usuario)

        if not cuenta_id:
            return _sin_resultados(queryset)

        return queryset.filter(
            pk=cuenta_id,
        )

    return _sin_resultados(queryset)


# ======================================================
# SUCURSALES
# ======================================================

def filtrar_sucursales(
    usuario: AbstractBaseUser | None,
    queryset: QuerySet[ModelType],
) -> QuerySet[ModelType]:
    """
    Filtra las sucursales visibles para el usuario.

    Usuario cliente con sucursal:
        solo esa sucursal.

    Usuario cliente sin sucursal:
        todas las sucursales de su cuenta.
    """

    if not _usuario_activo(usuario):
        return _sin_resultados(queryset)

    if tiene_acceso_global(usuario):
        return queryset

    if es_usuario_cliente(usuario):
        cuenta_id = _cuenta_cliente_id(usuario)
        sucursal_id = _sucursal_id(usuario)

        if not cuenta_id:
            return _sin_resultados(queryset)

        queryset = queryset.filter(
            cuenta_cliente_id=cuenta_id,
        )

        if sucursal_id:
            queryset = queryset.filter(
                pk=sucursal_id,
            )

        return queryset

    return _sin_resultados(queryset)


# ======================================================
# PROYECTOS
# ======================================================

def filtrar_proyectos(
    usuario: AbstractBaseUser | None,
    queryset: QuerySet[ModelType],
) -> QuerySet[ModelType]:
    """
    Filtra los proyectos visibles para el usuario.

    Acceso global:
        todos los proyectos.

    Usuario cliente:
        proyectos de su cuenta o sucursal.

    Técnico:
        proyectos vinculados con órdenes donde está asignado.

    Creador de proyectos:
        temporalmente puede consultar todos los proyectos.
        Cuando Proyecto tenga un campo ``creado_por``, este
        filtro podrá limitarse a los proyectos propios.
    """

    if not _usuario_activo(usuario):
        return _sin_resultados(queryset)

    if tiene_acceso_global(usuario):
        return queryset

    if es_usuario_cliente(usuario):
        cuenta_id = _cuenta_cliente_id(usuario)
        sucursal_id = _sucursal_id(usuario)

        if not cuenta_id:
            return _sin_resultados(queryset)

        queryset = queryset.filter(
            sucursal__cuenta_cliente_id=cuenta_id,
        )

        if sucursal_id:
            queryset = queryset.filter(
                sucursal_id=sucursal_id,
            )

        return queryset.distinct()

    if es_tecnico(usuario):
        return (
            queryset
            .filter(
                ordenes_trabajo__tecnicos__tecnico=usuario,
            )
            .distinct()
        )

    if es_creador_proyecto(usuario):
        return queryset

    return _sin_resultados(queryset)


# ======================================================
# DETALLES DE PROYECTO
# ======================================================

def filtrar_detalles_proyecto(
    usuario: AbstractBaseUser | None,
    queryset: QuerySet[ModelType],
) -> QuerySet[ModelType]:
    """
    Filtra los detalles según el acceso al proyecto principal.
    """

    if not _usuario_activo(usuario):
        return _sin_resultados(queryset)

    if tiene_acceso_global(usuario):
        return queryset

    if es_usuario_cliente(usuario):
        cuenta_id = _cuenta_cliente_id(usuario)
        sucursal_id = _sucursal_id(usuario)

        if not cuenta_id:
            return _sin_resultados(queryset)

        queryset = queryset.filter(
            proyecto__sucursal__cuenta_cliente_id=cuenta_id,
        )

        if sucursal_id:
            queryset = queryset.filter(
                proyecto__sucursal_id=sucursal_id,
            )

        return queryset.distinct()

    if es_tecnico(usuario):
        return (
            queryset
            .filter(
                proyecto__ordenes_trabajo__tecnicos__tecnico=usuario,
            )
            .distinct()
        )

    if es_creador_proyecto(usuario):
        return queryset

    return _sin_resultados(queryset)


# ======================================================
# ÓRDENES DE TRABAJO
# ======================================================

def filtrar_ordenes_trabajo(
    usuario: AbstractBaseUser | None,
    queryset: QuerySet[ModelType],
) -> QuerySet[ModelType]:
    """
    Filtra las órdenes de trabajo visibles.

    Acceso global:
        todas las órdenes.

    Técnico:
        únicamente órdenes donde está asignado.

    Usuario cliente:
        órdenes relacionadas con su cuenta o sucursal.
    """

    if not _usuario_activo(usuario):
        return _sin_resultados(queryset)

    if tiene_acceso_global(usuario):
        return queryset

    if es_tecnico(usuario):
        return (
            queryset
            .filter(
                tecnicos__tecnico=usuario,
            )
            .distinct()
        )

    if es_usuario_cliente(usuario):
        cuenta_id = _cuenta_cliente_id(usuario)
        sucursal_id = _sucursal_id(usuario)

        if not cuenta_id:
            return _sin_resultados(queryset)

        filtro_cuenta = (
            Q(
                sucursal__cuenta_cliente_id=cuenta_id,
            )
            | Q(
                proyecto__sucursal__cuenta_cliente_id=cuenta_id,
            )
            | Q(
                servicio_contratado__sucursal__cuenta_cliente_id=cuenta_id,
            )
        )

        queryset = queryset.filter(
            filtro_cuenta,
        )

        if sucursal_id:
            filtro_sucursal = (
                Q(
                    sucursal_id=sucursal_id,
                )
                | Q(
                    proyecto__sucursal_id=sucursal_id,
                )
                | Q(
                    servicio_contratado__sucursal_id=sucursal_id,
                )
            )

            queryset = queryset.filter(
                filtro_sucursal,
            )

        return queryset.distinct()

    if es_creador_proyecto(usuario):
        return queryset.filter(
            proyecto__isnull=False,
        ).distinct()

    return _sin_resultados(queryset)


# ======================================================
# TÉCNICOS DE ÓRDENES DE TRABAJO
# ======================================================

def filtrar_tecnicos_orden_trabajo(
    usuario: AbstractBaseUser | None,
    queryset: QuerySet[ModelType],
) -> QuerySet[ModelType]:
    """
    Filtra las asignaciones técnicas de órdenes de trabajo.
    """

    if not _usuario_activo(usuario):
        return _sin_resultados(queryset)

    if tiene_acceso_global(usuario):
        return queryset

    if es_tecnico(usuario):
        return queryset.filter(
            tecnico=usuario,
        )

    if es_usuario_cliente(usuario):
        cuenta_id = _cuenta_cliente_id(usuario)
        sucursal_id = _sucursal_id(usuario)

        if not cuenta_id:
            return _sin_resultados(queryset)

        filtro_cuenta = (
            Q(
                orden_trabajo__sucursal__cuenta_cliente_id=cuenta_id,
            )
            | Q(
                orden_trabajo__proyecto__sucursal__cuenta_cliente_id=cuenta_id,
            )
            | Q(
                orden_trabajo__servicio_contratado__sucursal__cuenta_cliente_id=cuenta_id,
            )
        )

        queryset = queryset.filter(
            filtro_cuenta,
        )

        if sucursal_id:
            filtro_sucursal = (
                Q(
                    orden_trabajo__sucursal_id=sucursal_id,
                )
                | Q(
                    orden_trabajo__proyecto__sucursal_id=sucursal_id,
                )
                | Q(
                    orden_trabajo__servicio_contratado__sucursal_id=sucursal_id,
                )
            )

            queryset = queryset.filter(
                filtro_sucursal,
            )

        return queryset.distinct()

    return _sin_resultados(queryset)


# ======================================================
# SEGUIMIENTOS DE ÓRDENES DE TRABAJO
# ======================================================

def filtrar_seguimientos_ot(
    usuario: AbstractBaseUser | None,
    queryset: QuerySet[ModelType],
) -> QuerySet[ModelType]:
    """
    Filtra los seguimientos según la visibilidad
    de su orden de trabajo.
    """

    if not _usuario_activo(usuario):
        return _sin_resultados(queryset)

    if tiene_acceso_global(usuario):
        return queryset

    if es_tecnico(usuario):
        return (
            queryset
            .filter(
                orden_trabajo__tecnicos__tecnico=usuario,
            )
            .distinct()
        )

    if es_usuario_cliente(usuario):
        cuenta_id = _cuenta_cliente_id(usuario)
        sucursal_id = _sucursal_id(usuario)

        if not cuenta_id:
            return _sin_resultados(queryset)

        filtro_cuenta = (
            Q(
                orden_trabajo__sucursal__cuenta_cliente_id=cuenta_id,
            )
            | Q(
                orden_trabajo__proyecto__sucursal__cuenta_cliente_id=cuenta_id,
            )
            | Q(
                orden_trabajo__servicio_contratado__sucursal__cuenta_cliente_id=cuenta_id,
            )
        )

        queryset = queryset.filter(
            filtro_cuenta,
        )

        if sucursal_id:
            filtro_sucursal = (
                Q(
                    orden_trabajo__sucursal_id=sucursal_id,
                )
                | Q(
                    orden_trabajo__proyecto__sucursal_id=sucursal_id,
                )
                | Q(
                    orden_trabajo__servicio_contratado__sucursal_id=sucursal_id,
                )
            )

            queryset = queryset.filter(
                filtro_sucursal,
            )

        return queryset.distinct()

    return _sin_resultados(queryset)


# ======================================================
# ARCHIVOS DE ÓRDENES DE TRABAJO
# ======================================================

def filtrar_archivos_ot(
    usuario: AbstractBaseUser | None,
    queryset: QuerySet[ModelType],
) -> QuerySet[ModelType]:
    """
    Filtra los archivos según la visibilidad
    de su orden de trabajo.
    """

    if not _usuario_activo(usuario):
        return _sin_resultados(queryset)

    if tiene_acceso_global(usuario):
        return queryset

    if es_tecnico(usuario):
        return (
            queryset
            .filter(
                orden_trabajo__tecnicos__tecnico=usuario,
            )
            .distinct()
        )

    if es_usuario_cliente(usuario):
        cuenta_id = _cuenta_cliente_id(usuario)
        sucursal_id = _sucursal_id(usuario)

        if not cuenta_id:
            return _sin_resultados(queryset)

        filtro_cuenta = (
            Q(
                orden_trabajo__sucursal__cuenta_cliente_id=cuenta_id,
            )
            | Q(
                orden_trabajo__proyecto__sucursal__cuenta_cliente_id=cuenta_id,
            )
            | Q(
                orden_trabajo__servicio_contratado__sucursal__cuenta_cliente_id=cuenta_id,
            )
        )

        queryset = queryset.filter(
            filtro_cuenta,
        )

        if sucursal_id:
            filtro_sucursal = (
                Q(
                    orden_trabajo__sucursal_id=sucursal_id,
                )
                | Q(
                    orden_trabajo__proyecto__sucursal_id=sucursal_id,
                )
                | Q(
                    orden_trabajo__servicio_contratado__sucursal_id=sucursal_id,
                )
            )

            queryset = queryset.filter(
                filtro_sucursal,
            )

        return queryset.distinct()

    return _sin_resultados(queryset)


# ======================================================
# INSTALACIONES
# ======================================================

def filtrar_instalaciones(
    usuario: AbstractBaseUser | None,
    queryset: QuerySet[ModelType],
) -> QuerySet[ModelType]:
    """
    Filtra instalaciones a través de la orden
    que les dio origen.
    """

    if not _usuario_activo(usuario):
        return _sin_resultados(queryset)

    if tiene_acceso_global(usuario):
        return queryset

    if es_tecnico(usuario):
        return (
            queryset
            .filter(
                Q(
                    tecnicos__usuario=usuario,
                )
                | Q(
                    orden_trabajo__tecnicos__tecnico=usuario,
                )
            )
            .distinct()
        )

    if es_usuario_cliente(usuario):
        cuenta_id = _cuenta_cliente_id(usuario)
        sucursal_id = _sucursal_id(usuario)

        if not cuenta_id:
            return _sin_resultados(queryset)

        filtro_cuenta = (
            Q(
                orden_trabajo__sucursal__cuenta_cliente_id=cuenta_id,
            )
            | Q(
                orden_trabajo__proyecto__sucursal__cuenta_cliente_id=cuenta_id,
            )
            | Q(
                orden_trabajo__servicio_contratado__sucursal__cuenta_cliente_id=cuenta_id,
            )
        )

        queryset = queryset.filter(
            filtro_cuenta,
        )

        if sucursal_id:
            filtro_sucursal = (
                Q(
                    orden_trabajo__sucursal_id=sucursal_id,
                )
                | Q(
                    orden_trabajo__proyecto__sucursal_id=sucursal_id,
                )
                | Q(
                    orden_trabajo__servicio_contratado__sucursal_id=sucursal_id,
                )
            )

            queryset = queryset.filter(
                filtro_sucursal,
            )

        return queryset.distinct()

    if es_creador_proyecto(usuario):
        return queryset.filter(
            orden_trabajo__proyecto__isnull=False,
        ).distinct()

    return _sin_resultados(queryset)


# ======================================================
# DISPOSITIVOS INSTALADOS
# ======================================================

def filtrar_dispositivos_instalados(
    usuario: AbstractBaseUser | None,
    queryset: QuerySet[ModelType],
) -> QuerySet[ModelType]:
    """
    Filtra dispositivos físicos instalados según
    el acceso a la instalación.
    """

    if not _usuario_activo(usuario):
        return _sin_resultados(queryset)

    if tiene_acceso_global(usuario):
        return queryset

    if es_tecnico(usuario):
        return (
            queryset
            .filter(
                Q(
                    instalacion__tecnicos__usuario=usuario,
                )
                | Q(
                    instalacion__orden_trabajo__tecnicos__tecnico=usuario,
                )
            )
            .distinct()
        )

    if es_usuario_cliente(usuario):
        cuenta_id = _cuenta_cliente_id(usuario)
        sucursal_id = _sucursal_id(usuario)

        if not cuenta_id:
            return _sin_resultados(queryset)

        filtro_cuenta = (
            Q(
                instalacion__orden_trabajo__sucursal__cuenta_cliente_id=cuenta_id,
            )
            | Q(
                instalacion__orden_trabajo__proyecto__sucursal__cuenta_cliente_id=cuenta_id,
            )
            | Q(
                instalacion__orden_trabajo__servicio_contratado__sucursal__cuenta_cliente_id=cuenta_id,
            )
        )

        queryset = queryset.filter(
            filtro_cuenta,
        )

        if sucursal_id:
            filtro_sucursal = (
                Q(
                    instalacion__orden_trabajo__sucursal_id=sucursal_id,
                )
                | Q(
                    instalacion__orden_trabajo__proyecto__sucursal_id=sucursal_id,
                )
                | Q(
                    instalacion__orden_trabajo__servicio_contratado__sucursal_id=sucursal_id,
                )
            )

            queryset = queryset.filter(
                filtro_sucursal,
            )

        return queryset.distinct()

    return _sin_resultados(queryset)


# ======================================================
# TÉCNICOS DE INSTALACIÓN
# ======================================================

def filtrar_tecnicos_instalacion(
    usuario: AbstractBaseUser | None,
    queryset: QuerySet[ModelType],
) -> QuerySet[ModelType]:
    """
    Filtra asignaciones de técnicos a instalaciones.
    """

    if not _usuario_activo(usuario):
        return _sin_resultados(queryset)

    if tiene_acceso_global(usuario):
        return queryset

    if es_tecnico(usuario):
        return queryset.filter(
            usuario=usuario,
        )

    if es_usuario_cliente(usuario):
        cuenta_id = _cuenta_cliente_id(usuario)
        sucursal_id = _sucursal_id(usuario)

        if not cuenta_id:
            return _sin_resultados(queryset)

        filtro_cuenta = (
            Q(
                instalacion__orden_trabajo__sucursal__cuenta_cliente_id=cuenta_id,
            )
            | Q(
                instalacion__orden_trabajo__proyecto__sucursal__cuenta_cliente_id=cuenta_id,
            )
            | Q(
                instalacion__orden_trabajo__servicio_contratado__sucursal__cuenta_cliente_id=cuenta_id,
            )
        )

        queryset = queryset.filter(
            filtro_cuenta,
        )

        if sucursal_id:
            filtro_sucursal = (
                Q(
                    instalacion__orden_trabajo__sucursal_id=sucursal_id,
                )
                | Q(
                    instalacion__orden_trabajo__proyecto__sucursal_id=sucursal_id,
                )
                | Q(
                    instalacion__orden_trabajo__servicio_contratado__sucursal_id=sucursal_id,
                )
            )

            queryset = queryset.filter(
                filtro_sucursal,
            )

        return queryset.distinct()

    return _sin_resultados(queryset)