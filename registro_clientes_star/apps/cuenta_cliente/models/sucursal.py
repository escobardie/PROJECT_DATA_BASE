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

from .cliente import CuentaCliente


class Sucursal(CodeModel):
    """
    Representa una sucursal o ubicación operativa
    perteneciente a una CuentaCliente.
    """

    CODE_PREFIX = "SUC"


    # ======================================================
    # RELACIÓN CON CUENTA CLIENTE
    # ======================================================

    cuenta_cliente = models.ForeignKey(
        CuentaCliente,
        on_delete=models.CASCADE,
        related_name="sucursales",
        verbose_name="Cuenta cliente",
    )


    # ======================================================
    # IDENTIFICACIÓN
    # ======================================================

    nombre = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name="Nombre de sucursal",
    )


    # ======================================================
    # DOMICILIO DE LA SUCURSAL
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

    email = models.EmailField(
        max_length=MAX_EMAIL_LENGTH,
        blank=True,
        null=True,
        verbose_name="Email",
    )


    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones",
    )


    class Meta:
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"
        ordering = ["codigo"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "cuenta_cliente",
                    "nombre",
                ],
                name="unique_sucursal_por_cliente",
            )
        ]


    def __str__(self):
        return f"{self.codigo} - {self.nombre}"