from django.db import models
from django.utils.translation import gettext_lazy as _


from apps.common.models import CodeModel
from apps.common.constants import (
    BRANCH_CODE_PREFIX,
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

    CODE_PREFIX = BRANCH_CODE_PREFIX


    # ======================================================
    # RELACIÓN CON CUENTA CLIENTE
    # ======================================================

    cuenta_cliente = models.ForeignKey(
        CuentaCliente,
        on_delete=models.PROTECT,
        related_name="sucursales",
        verbose_name=_( "Cuenta cliente"),
    )


    # ======================================================
    # IDENTIFICACIÓN
    # ======================================================

    nombre = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name=_( "Nombre de sucursal"),
    )


    # ======================================================
    # DOMICILIO DE LA SUCURSAL
    # ======================================================

    direccion = models.CharField(
        max_length=MAX_ADDRESS_LENGTH,
        verbose_name=_( "Dirección"),
    )

    numero = models.CharField(
        max_length=20,
        verbose_name=_( "Número"),
    )

    piso = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name=_( "Piso"),
    )

    departamento = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name=_( "Departamento"),
    )

    provincia = models.CharField(
        max_length=MAX_PROVINCE_LENGTH,
        verbose_name=_( "Provincia"),
    )

    ciudad = models.CharField(
        max_length=MAX_CITY_LENGTH,
        verbose_name=_( "Ciudad"),
    )

    codigo_postal = models.CharField(
        max_length=MAX_POSTAL_CODE_LENGTH,
        verbose_name=_( "Código postal"),
    )


    # ======================================================
    # CONTACTO
    # ======================================================

    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_( "Teléfono"),
    )

    email = models.EmailField(
        max_length=MAX_EMAIL_LENGTH,
        blank=True,
        null=True,
        verbose_name=_( "Email"),
    )


    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name=_( "Observaciones"),
    )


    class Meta:
        verbose_name = _( "Sucursal")
        verbose_name_plural = _( "Sucursales")

        ordering = [
            "codigo",
        ]

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
        return (
            f"{self.codigo} - "
            f"{self.nombre} "
            f"({self.cuenta_cliente})"
        )