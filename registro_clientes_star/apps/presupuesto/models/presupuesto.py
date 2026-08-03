from decimal import Decimal
from datetime import timedelta
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _


from apps.common.models import CodeModel

from apps.common.constants import (
    BUDGET_CODE_PREFIX,
    MAX_NAME_LENGTH,
    MAX_PRICE_DIGITS,
    PRICE_DECIMAL_PLACES,
)

from apps.common.choices import (
    MonedaPresupuestoChoices,
)

from apps.common.choices import (
    EstadoPresupuestoChoices,
)

from apps.cuenta_cliente.models import Sucursal


class Presupuesto(CodeModel):
    """
    Representa una propuesta comercial realizada a una sucursal.

    Un presupuesto define los conceptos comerciales ofrecidos al cliente,
    independientemente de la ejecución posterior del trabajo.

    Puede dar origen a un proyecto y posteriormente a una o varias
    órdenes de trabajo, una vez aprobado por el cliente.
    """

    CODE_PREFIX = BUDGET_CODE_PREFIX

    _UPDATE_TOTAL_FIELDS = (
        "subtotal",
        "descuento_total",
        "impuestos",
        "total",
    )

    # ======================================================
    # RELACIONES
    # ======================================================

    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        related_name="presupuestos",
        verbose_name=_("Sucursal"),
    )

    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="presupuestos",
        verbose_name=_("Vendedor"),
        help_text=_(
            "Usuario responsable de la elaboración del presupuesto."
        ),
    )

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    titulo = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name=_("Título"),
        db_index=True,
        help_text=_(
            "Nombre o referencia del presupuesto."
        ),
    )

    descripcion = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Descripción"),
    )

    # ======================================================
    # CONDICIONES COMERCIALES
    # ======================================================

    moneda = models.CharField(
        max_length=3,
        choices=MonedaPresupuestoChoices.choices,
        default=MonedaPresupuestoChoices.ARS,
        verbose_name=_("Moneda"),
    )

    # ======================================================
    # FECHAS
    # ======================================================

    fecha_emision = models.DateField(
        verbose_name=_("Fecha de emisión"),
        db_index=True,
        help_text=_(
            "Fecha en la que se emitió el presupuesto."
        ),
    )
    dias_validez = models.PositiveSmallIntegerField(
        default=15,
        verbose_name=_("Días de validez"),
        help_text=_(
            "Cantidad de días de validez del presupuesto."
        ),
    )

    fecha_vencimiento = models.DateField( #TODO: Calcular automáticamente a partir de fecha_emision + dias_validez
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_("Fecha de vencimiento"),
        help_text=_(
            "Fecha hasta la cual el presupuesto mantiene su validez."
        ),
    )

    # ======================================================
    # CLASIFICACIÓN
    # ======================================================

    estado = models.CharField(
        max_length=20,
        choices=EstadoPresupuestoChoices.choices,
        default=EstadoPresupuestoChoices.BORRADOR,
        db_index=True,
        verbose_name=_("Estado"),
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
    # IMPORTES
    # ======================================================

    subtotal = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=0,
        editable=False,
        verbose_name=_("Subtotal"),
        help_text=_(
            "Suma de los subtotales de los conceptos del presupuesto."
        ),
    )

    descuento_total = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=0,
        editable=False,
        verbose_name=_("Descuento total"),
        help_text=_(
            "Descuento total aplicado al presupuesto."
        ),
    )

    impuestos = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=0,
        editable=False,
        verbose_name=_("Impuestos"),
        help_text=_(
            "Importe total correspondiente a impuestos."
        ),
    )

    total = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=0,
        editable=False,
        verbose_name=_("Total"),
        help_text=_(
            "Importe final del presupuesto."
        ),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:
        verbose_name = _("Presupuesto")
        verbose_name_plural = _("Presupuestos")

        ordering = (
            "-created_at",
        )

        indexes = [

            models.Index(
                fields=[
                    "sucursal",
                    "estado",
                ],
                name="idx_pres_sucursal_estado",
            ),

            models.Index(
                fields=[
                    "fecha_emision",
                ],
                name="idx_pres_emision",
            ),

            models.Index(
                fields=[
                    "fecha_vencimiento",
                ],
                name="idx_pres_venc",
            ),

        ]

    # ======================================================
    # VALIDACIONES
    # ======================================================

    def clean(self):
        """
        Validaciones de negocio.
        """

        super().clean()

        if (
            self.fecha_vencimiento
            and self.fecha_vencimiento < self.fecha_emision
        ):
            raise ValidationError(
                {
                    "fecha_vencimiento": _(
                        "La fecha de vencimiento no puede ser anterior a la fecha de emisión."
                    )
                }
            )

    # ======================================================
    # MÉTODOS DE NEGOCIO
    # ======================================================

    def actualizar_totales(self, commit=True):
        """
        Recalcula automáticamente los importes del presupuesto
        a partir de sus conceptos comerciales.
        """

        resumen = self.items.aggregate(
            subtotal=Sum("subtotal"),
            descuento_total=Sum("descuento_importe"),
            impuestos=Sum("impuestos_importe"),
        )

        self.subtotal = (
            resumen["subtotal"]
            or Decimal("0.00")
        )

        self.descuento_total = (
            resumen["descuento_total"]
            or Decimal("0.00")
        )

        self.impuestos = (
            resumen["impuestos"]
            or Decimal("0.00")
        )

        self.total = (
            self.subtotal
            - self.descuento_total
            + self.impuestos
        )

        if commit:
            self.save(
                update_fields=self._UPDATE_TOTAL_FIELDS,
            )

    # ======================================================
    # ESTADO
    # ======================================================
    def cambiar_estado(self, estado, commit=True):
        """
        Actualiza el estado del presupuesto.
        """

        self.estado = estado

        if commit:
            self.save(
                update_fields=["estado"]
            )
    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return (
            f"{self.codigo} - "
            f"{self.titulo} "
            f"({self.sucursal})"
        )
    
    # ======================================================
    # SAVE
    # ======================================================

    def save(self, *args, **kwargs):

        if self.fecha_emision:

            self.fecha_vencimiento = (
                self.fecha_emision
                + timedelta(
                    days=self.dias_validez
                )
            )

        super().save(*args, **kwargs)

    # ======================================================
    # PROPIEDADES
    # ======================================================

    @property
    def esta_vencido(self):
        """
        Indica si el presupuesto se encuentra vencido.
        """

        from django.utils import timezone

        return (
            self.fecha_vencimiento
            and self.fecha_vencimiento < timezone.localdate()
        )

    @property
    def aprobado(self):
        """
        Indica si el presupuesto fue aprobado.
        """

        return (
            self.estado
            == EstadoPresupuestoChoices.APROBADO
        )

    @property
    def rechazado(self):
        """
        Indica si el presupuesto fue rechazado.
        """

        return (
            self.estado
            == EstadoPresupuestoChoices.RECHAZADO
        )

    @property
    def cantidad_items(self):
        """
        Cantidad de conceptos comerciales del presupuesto.
        """

        return self.items.count()

    @property
    def enviado(self):
        return (
            self.estado
            == EstadoPresupuestoChoices.ENVIADO
        )
    @property
    def borrador(self):
        return (
            self.estado
            == EstadoPresupuestoChoices.BORRADOR
        )