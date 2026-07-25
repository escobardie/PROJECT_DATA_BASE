from django.db import models

from apps.common.models import CodeModel
from apps.common.constants import (
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
    """

    CODE_PREFIX = "CLI"


    # ======================================================
    # TIPO DE CLIENTE
    # ======================================================

    tipo_cliente = models.CharField(
        max_length=20,
        choices=TipoClienteChoices.choices,
        default=TipoClienteChoices.PERSONA,
        verbose_name="Tipo de cliente",
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
        verbose_name="Apellido",
    )

    dni = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="DNI",
    )


    # ======================================================
    # DATOS EMPRESA
    # ======================================================

    razon_social = models.CharField(
        max_length=MAX_NAME_LENGTH,
        blank=True,
        null=True,
        verbose_name="Razón social",
    )

    cuit = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="CUIT",
    )


    # ======================================================
    # DOMICILIO PARTICULAR
    # ======================================================

    direccion = models.CharField(
        max_length=MAX_ADDRESS_LENGTH,
        verbose_name="Dirección",
    )

    numero = models.CharField(
        max_length=20,
        verbose_name="Número",
    )

    piso = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="Piso",
    )

    departamento = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="Departamento",
    )


    provincia = models.CharField(
        max_length=MAX_PROVINCE_LENGTH,
        verbose_name="Provincia",
    )

    ciudad = models.CharField(
        max_length=MAX_CITY_LENGTH,
        verbose_name="Ciudad",
    )

    codigo_postal = models.CharField(
        max_length=MAX_POSTAL_CODE_LENGTH,
        verbose_name="Código postal",
    )


    # ======================================================
    # CONTACTO
    # ======================================================

    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Teléfono",
    )

    celular = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Celular",
    )

    email = models.EmailField(
        max_length=MAX_EMAIL_LENGTH,
        blank=True,
        null=True,
        verbose_name="Email",
    )


    # ======================================================
    # INFORMACIÓN ADICIONAL
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones",
    )


    class Meta:
        verbose_name = "Cuenta Cliente"
        verbose_name_plural = "Cuentas Clientes"
        ordering = ["codigo"]


    def __str__(self):
        return f"{self.codigo}"