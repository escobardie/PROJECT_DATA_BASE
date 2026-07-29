from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    CONCEPT_TELECOM_CODE_PREFIX,
    MAX_NAME_LENGTH,
    MAX_PRICE_DIGITS,
    PRICE_DECIMAL_PLACES,
    DEFAULT_AMOUNT,
)
from apps.common.choices import (
    TipoConceptoTelecomChoices,
    MonedaChoices,
)


class ConceptoTelecom(CodeModel):
    """
    Ítem del catálogo de telecom: una tarea de mano de
    obra o un material, con su precio unitario de
    referencia.

    Es el catálogo comercial. Un presupuesto no apunta
    directamente a los cambios de precio de este catálogo:
    cada línea de presupuesto (DetallePresupuestoTelecom)
    guarda una copia histórica del precio al momento de
    agregarse.
    """

    CODE_PREFIX = CONCEPT_TELECOM_CODE_PREFIX

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    tipo = models.CharField(
        max_length=20,
        choices=TipoConceptoTelecomChoices.choices,
        verbose_name=_("Tipo"),
    )

    nombre = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name=_("Nombre"),
        help_text=_(
            "Nombre corto del ítem, para listados y "
            "selección rápida."
        ),
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name=_("Descripción"),
        help_text=_(
            "Detalle completo de lo que incluye el ítem."
        ),
    )

    # ======================================================
    # INFORMACIÓN COMERCIAL
    # ======================================================

    moneda = models.CharField(
        max_length=10,
        choices=MonedaChoices.choices,
        default=MonedaChoices.PESOS,
        verbose_name=_("Moneda"),
    )

    precio_unitario = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=DEFAULT_AMOUNT,
        verbose_name=_("Precio unitario"),
    )

    class Meta:
        verbose_name = _("Concepto de telecom")
        verbose_name_plural = _("Conceptos de telecom")

        ordering = (
            "tipo",
            "nombre",
        )

        constraints = [
            models.UniqueConstraint(
                fields=(
                    "tipo",
                    "nombre",
                ),
                name="unique_concepto_telecom_tipo_nombre",
            )
        ]

    def __str__(self):
        return self.nombre
