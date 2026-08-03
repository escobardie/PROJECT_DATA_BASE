from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel

from apps.common.constants import (
    BUDGET_ITEM_CODE_PREFIX,
    MAX_PRICE_DIGITS,
    PRICE_DECIMAL_PLACES,
)

from apps.common.choices import (
    UnidadMedidaChoices,
)

from .presupuesto import Presupuesto


class PresupuestoItem(CodeModel):
    """
    Representa un concepto comercial incluido en un presupuesto.

    Puede corresponder a un producto, servicio, mano de obra,
    licencia, viático o cualquier otro concepto comercial.
    """

    CODE_PREFIX = BUDGET_ITEM_CODE_PREFIX

    # ======================================================
    # RELACIONES
    # ======================================================

    presupuesto = models.ForeignKey(
        Presupuesto,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Presupuesto"),
    )

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    descripcion = models.TextField(
        verbose_name=_("Descripción"),
        help_text=_(
            "Descripción del concepto comercial."
        ),
    )

    # ======================================================
    # ORGANIZACIÓN
    # ======================================================

    orden = models.PositiveSmallIntegerField(
        default=1,
        validators=[
            MinValueValidator(1),
        ],
        verbose_name=_("Orden"),
        help_text=_(
            "Orden de presentación del concepto dentro del presupuesto."
        ),
    )

    # ======================================================
    # CANTIDADES
    # ======================================================

    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("1.00"),
        validators=[
            MinValueValidator(Decimal("0.01")),
        ],
        verbose_name=_("Cantidad"),
    )

    unidad = models.CharField(
        max_length=5,
        choices=UnidadMedidaChoices.choices,
        default=UnidadMedidaChoices.UNIDAD,
        verbose_name=_("Unidad"),
        help_text=_(
            "Unidad de medida del concepto."
        ),
    )

    # ======================================================
    # IMPORTES
    # ======================================================

    precio_unitario = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
        verbose_name=_("Precio unitario"),
    )

    descuento_importe = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
        verbose_name=_("Descuento"),
    )

    impuestos_importe = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
        verbose_name=_("Impuestos"),
    )

    subtotal = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=Decimal("0.00"),
        editable=False,
        verbose_name=_("Subtotal"),
    )

    total = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=Decimal("0.00"),
        editable=False,
        verbose_name=_("Total"),
    )

    # ======================================================
    # OBSERVACIONES
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Observaciones"),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:
        verbose_name = _("Concepto del presupuesto")
        verbose_name_plural = _("Conceptos del presupuesto")

        ordering = (
            "presupuesto",
            "orden",
            "codigo",
        )

        indexes = [

            models.Index(
                fields=[
                    "presupuesto",
                    "orden",
                ],
                name="idx_presitem_ord",
            ),

        ]

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "presupuesto",
                    "orden",
                ],
                name="unique_presupuesto_orden",
            ),

        ]

    # ======================================================
    # VALIDACIONES
    # ======================================================

    def clean(self):
        """
        Validaciones de negocio del concepto.
        """

        super().clean()

    # ======================================================
    # MÉTODOS DE NEGOCIO
    # ======================================================

    @property
    def importe_bruto(self):
        """
        Importe antes de descuentos e impuestos.
        """

        return (
            self.cantidad
            * self.precio_unitario
        )

    def calcular_importes(self):
        """
        Calcula automáticamente los importes del concepto.
        """

        self.subtotal = self.importe_bruto

        self.total = (
            self.subtotal
            - self.descuento_importe
            + self.impuestos_importe
        )

    # ======================================================
    # SAVE
    # ======================================================

    def save(self, *args, **kwargs):
        """
        Guarda el concepto recalculando previamente
        sus importes.
        """

        self.calcular_importes()

        with transaction.atomic():
            super().save(*args, **kwargs)
            self.presupuesto.actualizar_totales()

    # ======================================================
    # DELETE
    # ======================================================

    def delete(self, *args, **kwargs):
        """
        Elimina el concepto y actualiza los totales
        del presupuesto.
        """

        presupuesto = self.presupuesto

        with transaction.atomic():
            super().delete(*args, **kwargs)
            presupuesto.actualizar_totales()

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return (
            f"{self.orden}. "
            f"{self.descripcion}"
        )