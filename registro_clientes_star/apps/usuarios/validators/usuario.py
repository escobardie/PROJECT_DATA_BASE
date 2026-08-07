from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.usuarios.services.roles import (
    es_usuario_cliente,
)


# ======================================================
# CUENTA CLIENTE Y SUCURSAL
# ======================================================

def validar_cuenta_y_sucursal(
    *,
    cuenta_cliente=None,
    sucursal=None,
) -> None:
    """
    Valida la coherencia entre una cuenta cliente
    y una sucursal.

    Reglas:

    - Una sucursal no puede asignarse sin una cuenta.
    - La sucursal debe pertenecer a la cuenta indicada.

    Lanza ValidationError cuando la combinación
    no es válida.
    """

    cuenta_cliente_id = getattr(
        cuenta_cliente,
        "pk",
        None,
    )

    sucursal_id = getattr(
        sucursal,
        "pk",
        None,
    )

    if sucursal_id and not cuenta_cliente_id:
        raise ValidationError(
            {
                "cuenta_cliente": _(
                    "Debe seleccionar una cuenta cliente "
                    "cuando se asigna una sucursal."
                ),
            }
        )

    if (
        sucursal_id
        and cuenta_cliente_id
        and sucursal.cuenta_cliente_id
        != cuenta_cliente_id
    ):
        raise ValidationError(
            {
                "sucursal": _(
                    "La sucursal seleccionada no pertenece "
                    "a la cuenta cliente indicada."
                ),
            }
        )


# ======================================================
# ALCANCE DE USUARIO CLIENTE
# ======================================================

def validar_alcance_usuario_cliente(
    usuario,
) -> None:
    """
    Valida que un usuario perteneciente al grupo
    USUARIOS_CLIENTE tenga una cuenta asignada.

    La sucursal es opcional:

    - sin sucursal: acceso a toda la cuenta;
    - con sucursal: acceso restringido a esa sucursal.
    """

    if not usuario or not usuario.pk:
        return

    if (
        es_usuario_cliente(usuario)
        and not usuario.cuenta_cliente_id
    ):
        raise ValidationError(
            {
                "cuenta_cliente": _(
                    "Los usuarios clientes deben tener "
                    "una cuenta cliente asignada."
                ),
            }
        )


# ======================================================
# USUARIOS INTERNOS
# ======================================================

def validar_usuario_interno_sin_cliente(
    usuario,
) -> None:
    """
    Valida que determinados usuarios internos no tengan
    asignado accidentalmente un alcance de cliente.

    Esta validación es opcional porque un usuario interno
    podría necesitar una cuenta asociada por una decisión
    futura del negocio.
    """

    if not usuario:
        return

    if (
        usuario.is_superuser
        and (
            usuario.cuenta_cliente_id
            or usuario.sucursal_id
        )
    ):
        raise ValidationError(
            {
                "cuenta_cliente": _(
                    "Un superusuario no debería estar limitado "
                    "a una cuenta cliente."
                ),
                "sucursal": _(
                    "Un superusuario no debería estar limitado "
                    "a una sucursal."
                ),
            }
        )


# ======================================================
# PRIVILEGIOS
# ======================================================

def validar_superusuario_staff(
    usuario,
) -> None:
    """
    Garantiza que un superusuario también tenga
    acceso al sitio administrativo.
    """

    if (
        usuario
        and usuario.is_superuser
        and not usuario.is_staff
    ):
        raise ValidationError(
            {
                "is_staff": _(
                    "Un superusuario también debe tener "
                    "habilitado el acceso administrativo."
                ),
            }
        )


# ======================================================
# VALIDACIÓN GENERAL
# ======================================================

def validar_usuario(
    usuario,
    *,
    validar_alcance_cliente: bool = False,
) -> None:
    """
    Ejecuta las validaciones generales reutilizables
    sobre un usuario.

    El alcance del usuario cliente se valida opcionalmente
    porque los grupos ManyToMany todavía no están disponibles
    durante la primera etapa de creación del usuario.
    """

    validar_cuenta_y_sucursal(
        cuenta_cliente=usuario.cuenta_cliente,
        sucursal=usuario.sucursal,
    )

    validar_superusuario_staff(usuario)

    if validar_alcance_cliente:
        validar_alcance_usuario_cliente(usuario)