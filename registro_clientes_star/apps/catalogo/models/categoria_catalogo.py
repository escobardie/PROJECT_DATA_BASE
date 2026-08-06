from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel

from apps.common.constants import (
    CATALOG_CATEGORY_CODE_PREFIX,
    MAX_DESCRIPTION_LENGTH,
    MAX_NAME_LENGTH,
)


class CategoriaCatalogo(CodeModel):
    """
    Representa una categoría utilizada para organizar
    los ítems del catálogo general.

    Una categoría puede agrupar materiales, insumos,
    mano de obra, servicios, licencias, viáticos
    y otros conceptos valorizados.
    """

    CODE_PREFIX = CATALOG_CATEGORY_CODE_PREFIX

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    nombre = models.CharField(
        max_length=MAX_NAME_LENGTH,
        db_index=True,
        verbose_name=_("Nombre"),
        help_text=_(
            "Nombre identificativo de la categoría."
        ),
    )

    descripcion = models.TextField(
        max_length=MAX_DESCRIPTION_LENGTH,
        blank=True,
        default="",
        verbose_name=_("Descripción"),
        help_text=_(
            "Descripción general de los conceptos "
            "agrupados en esta categoría."
        ),
    )

    # ======================================================
    # ORGANIZACIÓN
    # ======================================================

    orden = models.PositiveSmallIntegerField(
        default=0,
        db_index=True,
        verbose_name=_("Orden"),
        help_text=_(
            "Orden de presentación de la categoría "
            "dentro del catálogo."
        ),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:
        verbose_name = _("Categoría de catálogo")
        verbose_name_plural = _("Categorías de catálogo")

        ordering = (
            "orden",
            "nombre",
        )

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "nombre",
                ],
                name="unique_categoria_catalogo_nombre",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "orden",
                    "nombre",
                ],
                name="idx_catcat_orden_nombre",
            ),
        ]

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return (
            f"{self.codigo} - "
            f"{self.nombre}"
        )