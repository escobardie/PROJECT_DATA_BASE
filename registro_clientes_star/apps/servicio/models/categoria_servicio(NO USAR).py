from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    SERVICE_CATEGORY_CODE_PREFIX,
    MAX_NAME_LENGTH,
    MAX_DESCRIPTION_LENGTH,
)


class CategoriaServicio(CodeModel):
    """
    Catálogo de categorías de servicios.

    Ejemplos:
        - Seguridad electrónica
        - Mantenimiento
        - Instalaciones
    """

    CODE_PREFIX = SERVICE_CATEGORY_CODE_PREFIX

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    nombre = models.CharField(
        max_length=MAX_NAME_LENGTH,
        unique=True,
        verbose_name=_("Nombre"),
    )

    descripcion = models.CharField(
        max_length=MAX_DESCRIPTION_LENGTH,
        blank=True,
        verbose_name=_("Descripción"),
    )

    class Meta:
        verbose_name = _("Categoría de servicio")
        verbose_name_plural = _("Categorías de servicios")

        ordering = (
            "nombre",
        )

    def __str__(self):
        return self.nombre