from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.constants import (
    DEVICE_CODE_PREFIX,
    MAX_DESCRIPTION_LENGTH,
    MAX_NAME_LENGTH,
    MAX_PRICE_DIGITS,
    PRICE_DECIMAL_PLACES,
)

from apps.common.models import CodeModel

from .modelo_dispositivo import ModeloDispositivo


class Dispositivo(CodeModel):
    """
    Catálogo interno de dispositivos.

    Representa un producto administrado por la empresa.

    No representa un equipo físico instalado.

    El equipo físico pertenece a InstalacionDispositivo.

    Ejemplo:

        Código:
            DIS-000001

        Producto:
            Cámara Hikvision DS-2CD2043G2-I

        Precio:
            $120000
    """

    CODE_PREFIX = DEVICE_CODE_PREFIX

    # ======================================================
    # RELACIÓN
    # ======================================================

    modelo = models.ForeignKey(
        ModeloDispositivo,
        on_delete=models.PROTECT,
        related_name="dispositivos",
        verbose_name=_("Modelo"),
        help_text=_(
            "Modelo técnico del dispositivo."
        ),
    )

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    nombre_comercial = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name=_("Nombre comercial"),
        help_text=_(
            "Nombre utilizado internamente para el producto."
        ),
    )

    descripcion = models.TextField(
        max_length=MAX_DESCRIPTION_LENGTH,
        blank=True,
        verbose_name=_("Descripción"),
        help_text=_(
            "Descripción comercial del dispositivo."
        ),
    )

    # ======================================================
    # INFORMACIÓN ECONÓMICA
    # ======================================================

    precio_mercado = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=0,
        verbose_name=_("Precio de mercado"),
        help_text=_(
            "Valor de referencia del dispositivo."
        ),
    )

    costo = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=0,
        verbose_name=_("Costo"),
        help_text=_(
            "Costo interno de adquisición."
        ),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    orden = models.PositiveSmallIntegerField(
        default=0,
        db_index=True,
        verbose_name=_("Orden"),
        help_text=_(
            "Orden de visualización del catálogo."
        ),
    )

    # ======================================================
    # META
    # ======================================================

    class Meta:
        verbose_name = _("Dispositivo")
        verbose_name_plural = _("Dispositivos")

        ordering = (
            "orden",
            "nombre_comercial",
        )

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "modelo",
                    "nombre_comercial",
                ],
                name="unique_dispositivo_modelo_nombre",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "modelo",
                    "nombre_comercial",
                ],
                name="idx_dispositivo_modelo_nombre",
            ),
            models.Index(
                fields=[
                    "orden",
                    "nombre_comercial",
                ],
                name="idx_dispositivo_orden_nombre",
            ),
        ]

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return self.nombre_comercial