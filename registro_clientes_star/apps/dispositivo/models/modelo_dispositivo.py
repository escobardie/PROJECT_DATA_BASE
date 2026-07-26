from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    DEVICE_MODEL_CODE_PREFIX,
    MAX_NAME_LENGTH,
    MAX_CODE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
)

from .tipo_dispositivo import TipoDispositivo
from .marca import Marca


class ModeloDispositivo(CodeModel):
    """
    Catálogo de modelos de dispositivos fabricados por una marca.

    Representa el modelo comercial/técnico de un equipo,
    no un dispositivo físico instalado.
    
    Ejemplos:
        - Hikvision DS-2CD2043G0-I
        - Dahua XVR5108HS
        - DSC PC1832
    """

    CODE_PREFIX = DEVICE_MODEL_CODE_PREFIX

    # ======================================================
    # RELACIONES
    # ======================================================

    tipo_dispositivo = models.ForeignKey(
        TipoDispositivo,
        on_delete=models.PROTECT,
        related_name="modelos",
        verbose_name=_("Tipo de dispositivo"),
    )

    marca = models.ForeignKey(
        Marca,
        on_delete=models.PROTECT,
        related_name="modelos",
        verbose_name=_("Marca"),
    )

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    nombre = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name=_("Nombre del modelo"),
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name=_("Descripción"),
    )

    # ======================================================
    # INFORMACIÓN DEL FABRICANTE
    # ======================================================

    fabricante_codigo = models.CharField(
        max_length=MAX_CODE_LENGTH,
        blank=True,
        verbose_name=_("Código del fabricante"),
        help_text=_(
            "Código o número de parte utilizado por el fabricante."
        ),
    )

    ean = models.CharField(
        max_length=MAX_CODE_LENGTH,
        blank=True,
        verbose_name=_("Código EAN"),
        help_text=_(
            "Código comercial EAN/GTIN del producto."
        ),
    )

    # ======================================================
    # INFORMACIÓN DEL FABRICANTE
    # ======================================================

    url_datas_heet = models.URLField(
        blank=True,
        verbose_name=_("URL Hoja de datos"),
        help_text=_(
            "Enlace a la hoja de datos técnica del producto."
        ),
    )

    # ======================================================
    # ESTADO DEL MODELO
    # ======================================================

    fabricado = models.BooleanField(
        default=True,
        verbose_name=_("Fabricado"),
        help_text=_(
            "Indica si el fabricante continúa produciendo este modelo."
        ),
    )

    # ======================================================
    # OBSERVACIONES
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        verbose_name=_("Observaciones"),
    )

    class Meta:
        verbose_name = _("Modelo de dispositivo")
        verbose_name_plural = _("Modelos de dispositivos")

        ordering = (
            "marca__nombre",
            "nombre",
        )

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "marca",
                    "nombre",
                ],
                name="unique_modelo_por_marca",
            )
        ]

    def __str__(self):
        return f"{self.marca} - {self.nombre}"