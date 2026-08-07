from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
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

    Utiliza el correo electrónico como identificador de acceso.

    Los roles funcionales se administran mediante los grupos
    y permisos de Django. Las relaciones con CuentaCliente
    y Sucursal delimitan el acceso de los usuarios clientes.
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
        default="",
        verbose_name=_("Teléfono"),
    )

    cargo = models.CharField(
        max_length=MAX_NAME_LENGTH,
        blank=True,
        default="",
        verbose_name=_("Cargo"),
        help_text=_(
            "Cargo laboral o función descriptiva del usuario. "
            "No reemplaza los grupos ni permisos."
        ),
    )

    # ======================================================
    # ALCANCE DEL USUARIO CLIENTE
    # ======================================================

    cuenta_cliente = models.ForeignKey(
        CuentaCliente,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="usuarios",
        verbose_name=_("Cuenta cliente"),
        help_text=_(
            "Cuenta a la que puede acceder el usuario cliente. "
            "Debe quedar vacía para usuarios internos."
        ),
    )

    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="usuarios",
        verbose_name=_("Sucursal"),
        help_text=_(
            "Sucursal específica a la que se limita el acceso. "
            "Si queda vacía, el usuario podrá acceder al alcance "
            "autorizado de toda la cuenta cliente."
        ),
    )

    # ======================================================
    # OBSERVACIONES
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Observaciones"),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:
        verbose_name = _("Usuario")
        verbose_name_plural = _("Usuarios")

        ordering = (
            "first_name",
            "last_name",
            "email",
        )

    # ======================================================
    # VALIDACIONES
    # ======================================================

    def clean(self):
        """
        Valida la coherencia entre la cuenta cliente
        y la sucursal asignadas.
        """

        super().clean()

        errores = {}

        if self.sucursal_id and not self.cuenta_cliente_id:
            errores["cuenta_cliente"] = _(
                "Debe seleccionar una cuenta cliente "
                "cuando se asigna una sucursal."
            )

        if (
            self.sucursal_id
            and self.cuenta_cliente_id
            and self.sucursal.cuenta_cliente_id
            != self.cuenta_cliente_id
        ):
            errores["sucursal"] = _(
                "La sucursal seleccionada no pertenece "
                "a la cuenta cliente indicada."
            )

        if errores:
            raise ValidationError(errores)

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def get_full_name(self):
        """
        Devuelve el nombre completo del usuario.
        """

        return (
            f"{self.first_name} {self.last_name}"
            .strip()
        )

    def __str__(self):
        return self.get_full_name() or self.email

    # ======================================================
    # PROPIEDADES DE ACCESO
    # ======================================================

    @property
    def es_usuario_cliente(self):
        """
        Indica si el usuario pertenece al grupo
        de usuarios clientes.
        """

        if not self.pk:
            return False

        return self.groups.filter(
            name="USUARIOS_CLIENTE",
        ).exists()

    @property
    def es_tecnico(self):
        """
        Indica si el usuario pertenece al grupo de técnicos.
        """

        if not self.pk:
            return False

        return self.groups.filter(
            name="TECNICOS",
        ).exists()

    @property
    def es_auditor(self):
        """
        Indica si el usuario pertenece al grupo de auditores.
        """

        if not self.pk:
            return False

        return self.groups.filter(
            name="AUDITORES",
        ).exists()

    @property
    def es_gerencia(self):
        """
        Indica si el usuario pertenece al grupo de gerencia.
        """

        if not self.pk:
            return False

        return self.groups.filter(
            name="GERENCIA",
        ).exists()