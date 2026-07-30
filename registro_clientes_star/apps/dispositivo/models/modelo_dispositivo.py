from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.constants import (
    DEVICE_MODEL_CODE_PREFIX,
    MAX_NAME_LENGTH,
    MAX_DESCRIPTION_LENGTH,
)

from apps.common.models import CodeModel

from .marca import Marca
from .tipo_dispositivo import TipoDispositivo


class ModeloDispositivo(CodeModel):
    """
    Catálogo de modelos de dispositivos.

    Representa un modelo comercial específico fabricado
    por una marca determinada.

    Ejemplo:

    Marca:
        Hikvision

    Tipo:
        Cámara

    Modelo:
        DS-2CD2043G2-I
    """

    CODE_PREFIX = DEVICE_MODEL_CODE_PREFIX

    # ======================================================
    # RELACIONES
    # ======================================================

    marca = models.ForeignKey(
        Marca,
        on_delete=models.PROTECT,
        related_name="modelos",
        verbose_name=_("Marca"),
        help_text=_(
            "Marca fabricante del dispositivo."
        ),
    )

    tipo_dispositivo = models.ForeignKey(
        TipoDispositivo,
        on_delete=models.PROTECT,
        related_name="modelos",
        verbose_name=_("Tipo de dispositivo"),
        help_text=_(
            "Clasificación del dispositivo."
        ),
    )

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    nombre = models.CharField(
        max_length=MAX_NAME_LENGTH,
        db_index=True,
        verbose_name=_("Modelo"),
        help_text=_(
            "Nombre o código comercial del modelo."
        ),
    )
    codigo_fabricante = models.CharField(
        max_length=MAX_NAME_LENGTH,
        blank=True,
        verbose_name=_("Código fabricante"),
        help_text=_(
            "Código asignado por el fabricante al modelo."
        ),
    )

    descripcion = models.TextField(
        max_length=MAX_DESCRIPTION_LENGTH,
        blank=True,
        verbose_name=_("Descripción"),
        help_text=_(
            "Descripción general del modelo."
        ),
    )

    especificaciones = models.TextField(
        blank=True,
        verbose_name=_("Especificaciones técnicas"),
        help_text=_(
            "Características técnicas del modelo."
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
            "Orden utilizado para mostrar el catálogo."
        ),
    )

    # ======================================================
    # META
    # ======================================================

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
                    "codigo_fabricante",
                ],
                name="unique_modelo_marca_codigo_fabricante",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "marca",
                    "nombre",
                ],
                name="idx_modelo_marca_nombre",
            ),
            models.Index(
                fields=[
                    "tipo_dispositivo",
                    "nombre",
                ],
                name="idx_modelo_tipo_nombre",
            ),
        ]

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return (
            f"{self.marca.nombre} "
            f"{self.nombre}"
        )