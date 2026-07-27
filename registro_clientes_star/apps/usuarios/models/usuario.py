from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.constants import (
    MAX_NAME_LENGTH,
    MAX_PHONE_LENGTH,
)

from apps.cuenta_cliente.models import (
    CuentaCliente,
    Sucursal,
)

from apps.usuarios.managers import UsuarioManager


class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado.

    Utiliza el correo electrónico como identificador para el inicio
    de sesión y permite representar tanto usuarios internos como
    usuarios clientes.
    """

    # ======================================================
    # AUTENTICACIÓN
    # ======================================================

    username = None

    email = models.EmailField(
        unique=True,
        verbose_name=_("Correo electrónico"),
    )

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = []

    objects = UsuarioManager()

    # ======================================================
    # INFORMACIÓN PERSONAL
    # ======================================================

    first_name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name=_("Nombre"),
    )

    last_name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name=_("Apellido"),
    )

    telefono = models.CharField(
        max_length=MAX_PHONE_LENGTH,
        blank=True,
        verbose_name=_("Teléfono"),
    )

    cargo = models.CharField(
        max_length=MAX_NAME_LENGTH,
        blank=True,
        verbose_name=_("Cargo"),
    )

    # ======================================================
    # RELACIONES
    # ======================================================

    cuenta_cliente = models.ForeignKey(
        CuentaCliente,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="usuarios",
        verbose_name=_("Cuenta cliente"),
    )

    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="usuarios",
        verbose_name=_("Sucursal"),
    )

    # ======================================================
    # OBSERVACIONES
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        verbose_name=_("Observaciones"),
    )

    class Meta:
        verbose_name = _("Usuario")
        verbose_name_plural = _("Usuarios")

        ordering = (
            "first_name",
            "last_name",
        )

    def get_full_name(self):
        """
        Devuelve el nombre completo del usuario.
        """
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return self.get_full_name() or self.email