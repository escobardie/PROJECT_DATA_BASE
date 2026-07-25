from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    SERVICE_CODE_PREFIX,
    MAX_NAME_LENGTH,
    MAX_PRICE_DIGITS,
    PRICE_DECIMAL_PLACES,
    DEFAULT_AMOUNT,
)
from apps.sistema.models import Sistema

from .categoria import CategoriaServicio


class Servicio(CodeModel):
    """
    Representa un servicio ofrecido por la empresa.
    Corresponde al catálogo comercial y no a un servicio
    contratado por un cliente.
    """

    CODE_PREFIX = SERVICE_CODE_PREFIX

    # ======================================================
    # RELACIONES
    # ======================================================

    categoria = models.ForeignKey(
        CategoriaServicio,
        on_delete=models.PROTECT,
        related_name="servicios",
        verbose_name=_("Categoría"),
    )
    sistemas = models.ManyToManyField(
        Sistema,
        through="ServicioSistema",
        related_name="servicios",
        verbose_name=_("Sistemas"),
        blank=True,
    )

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    nombre = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name=_("Nombre"),
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name=_("Descripción"),
    )

    # ======================================================
    # INFORMACIÓN COMERCIAL
    # ======================================================

    precio_abono = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=DEFAULT_AMOUNT,
        verbose_name=_("Precio abono"),
    )

    # ======================================================
    # CONFIGURACIÓN DEL SERVICIO
    # ======================================================

    requiere_dispositivos = models.BooleanField(
        default=True,
        verbose_name=_("Requiere dispositivos"),
    )

    requiere_instalacion = models.BooleanField(
        default=True,
        verbose_name=_("Requiere instalación"),
    )

    genera_abono = models.BooleanField(
        default=True,
        verbose_name=_("Genera abono"),
    )

    permite_facturacion = models.BooleanField(
        default=True,
        verbose_name=_("Permite facturación"),
    )

    # ======================================================
    # OBSERVACIONES
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        verbose_name=_("Observaciones"),
    )

    class Meta:
        verbose_name = _("Servicio")
        verbose_name_plural = _("Servicios")
        ordering = ("nombre",)

        constraints = [
            models.UniqueConstraint(
                fields=["categoria","nombre",],
                name="unique_servicio_categoria_nombre",
            )
        ]

    def __str__(self):
        return self.nombre