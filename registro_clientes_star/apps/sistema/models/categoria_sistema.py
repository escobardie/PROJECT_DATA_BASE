from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    SYSTEM_CATEGORY_CODE_PREFIX,
    MAX_NAME_LENGTH,
    MAX_DESCRIPTION_LENGTH,
)


class CategoriaSistema(CodeModel):
    """
    Catálogo de categorías de sistemas tecnológicos.

    Ejemplos:
        - Seguridad
        - Comunicaciones
        - Redes
        - Automatización
    """

    CODE_PREFIX = SYSTEM_CATEGORY_CODE_PREFIX

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    nombre = models.CharField(
        max_length=MAX_NAME_LENGTH,
        unique=True,
        verbose_name=_("Nombre"),
        help_text=_(
            "Nombre de la categoría tecnológica."
        ),
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name=_("Descripción"),
        help_text=_(
            "Descripción detallada de la categoría tecnológica."
        ),
    )

    class Meta:
        verbose_name = _("Categoría de sistema")
        verbose_name_plural = _("Categorías de sistemas")

        ordering = (
            "nombre",
        )

    def __str__(self):
        return self.nombre