from decimal import Decimal

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from apps.common.constants import (
    MAX_NAME_LENGTH,
    MAX_PRICE_DIGITS,
    PRICE_DECIMAL_PLACES,
    DEFAULT_AMOUNT,
)
from apps.common.choices import (
    TipoConceptoTelecomChoices,
    MonedaChoices,
)

from .presupuesto import PresupuestoTelecom
from .concepto import ConceptoTelecom


class DetallePresupuestoTelecom(models.Model):
    """
    Línea de un presupuesto de telecom.

    Guarda una copia histórica del nombre, tipo, moneda y
    precio unitario del concepto al momento de agregarse,
    para que un cambio posterior en el catálogo no altere
    presupuestos ya calculados.
    """

    # ======================================================
    # RELACIONES
    # ======================================================

    presupuesto = models.ForeignKey(
        PresupuestoTelecom,
        on_delete=models.CASCADE,
        related_name="detalles",
        verbose_name=_("Presupuesto"),
    )

    concepto = models.ForeignKey(
        ConceptoTelecom,
        on_delete=models.PROTECT,
        related_name="detalles_presupuesto",
        verbose_name=_("Concepto"),
    )

    # ======================================================
    # INFORMACIÓN HISTÓRICA
    # ======================================================

    nombre_concepto = models.CharField(
        max_length=MAX_NAME_LENGTH,
        editable=False,
        verbose_name=_("Concepto"),
    )

    tipo = models.CharField(
        max_length=20,
        choices=TipoConceptoTelecomChoices.choices,
        editable=False,
        verbose_name=_("Tipo"),
    )

    moneda = models.CharField(
        max_length=10,
        choices=MonedaChoices.choices,
        editable=False,
        verbose_name=_("Moneda"),
    )

    precio_unitario = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        editable=False,
        default=DEFAULT_AMOUNT,
        verbose_name=_("Precio unitario"),
    )

    # ======================================================
    # INFORMACIÓN COMERCIAL
    # ======================================================

    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("1.00"),
        verbose_name=_("Cantidad"),
    )

    subtotal = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        editable=False,
        default=DEFAULT_AMOUNT,
        verbose_name=_("Subtotal"),
    )

    class Meta:
        verbose_name = _("Detalle de presupuesto de telecom")
        verbose_name_plural = _(
            "Detalles de presupuesto de telecom"
        )

        ordering = (
            "presupuesto",
            "id",
        )

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return self.nombre_concepto

    # ======================================================
    # MÉTODOS PRIVADOS
    # ======================================================

    def _copiar_datos_del_concepto(self):
        """
        Copia la información del concepto solamente
        cuando el detalle se crea.
        """

        if self.pk:
            return

        self.nombre_concepto = self.concepto.nombre
        self.tipo = self.concepto.tipo
        self.moneda = self.concepto.moneda
        self.precio_unitario = self.concepto.precio_unitario

    def calcular_subtotal(self):
        """
        Calcula el subtotal del detalle.
        """

        return self.cantidad * self.precio_unitario

    # ======================================================
    # PERSISTENCIA
    # ======================================================

    def save(self, *args, **kwargs):

        with transaction.atomic():

            self._copiar_datos_del_concepto()

            self.subtotal = self.calcular_subtotal()

            super().save(*args, **kwargs)

            self.presupuesto.recalcular_totales()

    def delete(self, *args, **kwargs):

        with transaction.atomic():

            presupuesto = self.presupuesto

            super().delete(*args, **kwargs)

            presupuesto.recalcular_totales()
