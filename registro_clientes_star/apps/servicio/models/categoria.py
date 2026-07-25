from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    CATEGORY_SERVICE_CODE_PREFIX,
    MAX_NAME_LENGTH,
)


class CategoriaServicio(CodeModel):
    """
    Categoría utilizada para organizar el catálogo
    de servicios ofrecidos por la empresa.
    """

    CODE_PREFIX = CATEGORY_SERVICE_CODE_PREFIX

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    nombre = models.CharField(
        max_length=MAX_NAME_LENGTH,
        unique=True,
        verbose_name=_("Nombre"),
        help_text="Nombre de la categoría.",
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name=_("Descripción"),
        help_text="Descripción opcional de la categoría.",
    )

    class Meta:
        verbose_name = _("Categoría de servicio")
        verbose_name_plural = _("Categorías de servicios")
        ordering = ("nombre",)

    def __str__(self):
        return self.nombre