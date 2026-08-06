from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel
from apps.cuenta_cliente.models import CuentaCliente

from .usuario import Usuario


class UsuarioCuentaCliente(BaseModel):
    """
    Relaciona un usuario externo con una cuenta cliente.

    Permite limitar el acceso del usuario exclusivamente
    a la cuenta o cuentas que tenga asignadas.
    """

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="cuentas_cliente_asignadas",
        verbose_name=_("Usuario"),
    )

    cuenta_cliente = models.ForeignKey(
        CuentaCliente,
        on_delete=models.CASCADE,
        related_name="usuarios_asignados",
        verbose_name=_("Cuenta cliente"),
    )

    es_administrador = models.BooleanField(
        default=False,
        verbose_name=_("Administrador de la cuenta"),
        help_text=_(
            "Indica si puede administrar otros usuarios "
            "de la cuenta dentro del portal del cliente."
        ),
    )

    class Meta:
        verbose_name = _("Cuenta asignada al usuario")
        verbose_name_plural = _("Cuentas asignadas a usuarios")

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "usuario",
                    "cuenta_cliente",
                ],
                name="unique_usuario_cuenta_cliente",
            ),
        ]

    def __str__(self):
        return (
            f"{self.usuario} - "
            f"{self.cuenta_cliente}"
        )