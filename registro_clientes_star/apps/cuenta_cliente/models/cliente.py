from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


from apps.common.models import CodeModel
from apps.common.constants import (
    CLIENT_CODE_PREFIX,
    MAX_NAME_LENGTH,
    MAX_ADDRESS_LENGTH,
    MAX_CITY_LENGTH,
    MAX_PROVINCE_LENGTH,
    MAX_POSTAL_CODE_LENGTH,
    MAX_EMAIL_LENGTH,
)

from apps.common.choices import TipoClienteChoices


class CuentaCliente(CodeModel):
    """
    Representa una cuenta cliente dentro del sistema.

    Puede corresponder a una persona física
    o una empresa.
    """

    CODE_PREFIX = CLIENT_CODE_PREFIX


    # ======================================================
    # TIPO DE CLIENTE
    # ======================================================

    tipo_cliente = models.CharField(
        max_length=20,
        choices=TipoClienteChoices.choices,
        default=TipoClienteChoices.PERSONA,
        verbose_name=_("Tipo de cliente"),
    )


    # ======================================================
    # DATOS PERSONA FÍSICA
    # ======================================================

    nombre = models.CharField(
        max_length=MAX_NAME_LENGTH,
        blank=True,
        null=True,
        verbose_name="Nombre",
    )

    apellido = models.CharField(
        max_length=MAX_NAME_LENGTH,
        blank=True,
        null=True,
        verbose_name=_("Apellido"),
    )

    dni = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("DNI"),
    )


    # ======================================================
    # DATOS EMPRESA
    # ======================================================

    razon_social = models.CharField(
        max_length=MAX_NAME_LENGTH,
        blank=True,
        null=True,
        verbose_name=_("Razón social"),
    )

    cuit = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("CUIT"),
    )


    # ======================================================
    # DOMICILIO PARTICULAR
    # ======================================================

    direccion = models.CharField(
        max_length=MAX_ADDRESS_LENGTH,
        verbose_name=_("Dirección"),
    )

    numero = models.CharField(
        max_length=20,
        verbose_name=_("Número"),
    )

    piso = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name=_("Piso"),
    )

    departamento = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name=_("Departamento"),
    )

    provincia = models.CharField(
        max_length=MAX_PROVINCE_LENGTH,
        verbose_name=_("Provincia"),
    )

    ciudad = models.CharField(
        max_length=MAX_CITY_LENGTH,
        verbose_name=_("Ciudad"),
    )

    codigo_postal = models.CharField(
        max_length=MAX_POSTAL_CODE_LENGTH,
        verbose_name=_("Código postal"),
    )


    # ======================================================
    # CONTACTO
    # ======================================================

    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Teléfono"),
    )

    celular = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Celular"),
    )

    email = models.EmailField(
        max_length=MAX_EMAIL_LENGTH,
        blank=True,
        null=True,
        verbose_name=_("Email"),
    )


    # ======================================================
    # INFORMACIÓN ADICIONAL
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Observaciones"),
    )


    class Meta:
        verbose_name = _("Cuenta Cliente")
        verbose_name_plural = _("Cuentas Clientes")
        ordering = [
            "codigo",
        ]


    # ======================================================
    # VALIDACIONES
    # ======================================================

    def clean(self):
        """
        Valida la información según el tipo de cliente.
        """

        if self.tipo_cliente == TipoClienteChoices.PERSONA:

            if not self.nombre or not self.apellido:
                raise ValidationError(
                    "Una persona física debe tener nombre y apellido."
                )

            if not self.dni:
                raise ValidationError(
                    "Una persona física debe tener DNI."
                )


        if self.tipo_cliente == TipoClienteChoices.EMPRESA:

            if not self.razon_social:
                raise ValidationError(
                    "Una empresa debe tener razón social."
                )

            if not self.cuit:
                raise ValidationError(
                    "Una empresa debe tener CUIT."
                )


    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):

        if self.razon_social:
            return f"{self.codigo} - {self.razon_social}"

        return f"{self.codigo} - {self.apellido}, {self.nombre}"