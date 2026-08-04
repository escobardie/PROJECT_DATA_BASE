from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel

from apps.common.constants import (
    PROJECT_DETAIL_CODE_PREFIX,
    MAX_PRICE_DIGITS,
    PRICE_DECIMAL_PLACES,
)

from apps.common.choices import (
    UnidadMedidaChoices,
)

from apps.dispositivo.models import Dispositivo

from apps.common.choices import (
    TipoProyectoDetalleChoices,
)

from .proyecto import Proyecto


class ProyectoDetalle(CodeModel):
    """
    Representa un concepto comercial o técnico incluido en un proyecto.

    Puede corresponder a un dispositivo del catálogo, servicio,
    material, mano de obra, licencia, viático u otro concepto.

    Los detalles definen el alcance económico y técnico del proyecto.
    """

    CODE_PREFIX = PROJECT_DETAIL_CODE_PREFIX

    # ======================================================
    # RELACIONES
    # ======================================================

    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name="detalles",
        verbose_name=_("Proyecto"),
    )

    dispositivo = models.ForeignKey(
        Dispositivo,
        on_delete=models.PROTECT,
        related_name="proyecto_detalles",
        blank=True,
        null=True,
        verbose_name=_("Dispositivo"),
        help_text=_(
            "Producto del catálogo asociado al detalle, si corresponde."
        ),
    )

    # ======================================================
    # CLASIFICACIÓN
    # ======================================================

    tipo = models.CharField(
        max_length=20,
        choices=TipoProyectoDetalleChoices.choices,
        default=TipoProyectoDetalleChoices.DISPOSITIVO,
        db_index=True,
        verbose_name=_("Tipo"),
    )

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    descripcion = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Descripción"),
        help_text=_(
            "Descripción comercial o técnica del concepto."
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
            "Orden de presentación del detalle dentro del proyecto."
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
        verbose_name = _("Detalle del proyecto")
        verbose_name_plural = _("Detalles del proyecto")

        ordering = (
            "proyecto",
            "orden",
            "codigo",
        )

        indexes = [
            models.Index(
                fields=[
                    "proyecto",
                    "orden",
                ],
                name="idx_proydet_proy_ord",
            ),
            models.Index(
                fields=[
                    "tipo",
                ],
                name="idx_proydet_tipo",
            ),
            models.Index(
                fields=[
                    "dispositivo",
                ],
                name="idx_proydet_dispositivo",
            ),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "proyecto",
                    "orden",
                ],
                name="uq_proydet_proy_orden",
            ),
        ]

    # ======================================================
    # VALIDACIONES
    # ======================================================

    def clean(self):
        """
        Valida la coherencia del detalle del proyecto.
        """

        super().clean()

        errores = {}

        if (
            self.tipo
            == TipoProyectoDetalleChoices.DISPOSITIVO
            and not self.dispositivo
        ):
            errores["dispositivo"] = _(
                "Debe seleccionar un dispositivo para un detalle "
                "clasificado como dispositivo."
            )

        if (
            self.tipo
            != TipoProyectoDetalleChoices.DISPOSITIVO
            and self.dispositivo
        ):
            errores["dispositivo"] = _(
                "Solo los detalles de tipo dispositivo pueden tener "
                "un dispositivo asociado."
            )

        if self.descuento_importe > self.importe_bruto:
            errores["descuento_importe"] = _(
                "El descuento no puede ser mayor que el importe bruto."
            )

        if errores:
            raise ValidationError(errores)

    # ======================================================
    # MÉTODOS DE NEGOCIO
    # ======================================================

    def completar_desde_dispositivo(self):
        """
        Completa valores comerciales iniciales utilizando
        el dispositivo seleccionado.

        Los valores ya ingresados manualmente no se reemplazan.
        """

        if not self.dispositivo:
            return

        if not self.descripcion:
            self.descripcion = self.dispositivo.nombre_comercial

        if self.precio_unitario == Decimal("0.00"):
            self.precio_unitario = self.dispositivo.precio_mercado

        self.unidad = UnidadMedidaChoices.UNIDAD

    def calcular_importes(self):
        """
        Calcula los importes económicos del detalle.
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
        Guarda el detalle y actualiza los totales del proyecto.
        """

        self.completar_desde_dispositivo()
        self.calcular_importes()

        with transaction.atomic():
            super().save(*args, **kwargs)
            self.proyecto.actualizar_totales()

    # ======================================================
    # DELETE
    # ======================================================

    def delete(self, *args, **kwargs):
        """
        Elimina el detalle y actualiza los totales del proyecto.
        """

        proyecto = self.proyecto

        with transaction.atomic():
            resultado = super().delete(*args, **kwargs)
            proyecto.actualizar_totales()

        return resultado

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return (
            f"{self.orden}. "
            f"{self.descripcion}"
        )

    # ======================================================
    # PROPIEDADES
    # ======================================================

    @property
    def importe_bruto(self):
        """
        Importe anterior a descuentos e impuestos.
        """

        return (
            self.cantidad
            * self.precio_unitario
        )

    @property
    def es_dispositivo(self):
        """
        Indica si el detalle representa un dispositivo.
        """

        return (
            self.tipo
            == TipoProyectoDetalleChoices.DISPOSITIVO
        )

    @property
    def es_concepto_libre(self):
        """
        Indica si el detalle no representa un dispositivo.
        """

        return not self.es_dispositivo