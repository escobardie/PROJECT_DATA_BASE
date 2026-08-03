from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    QUOTE_TELECOM_CODE_PREFIX,
    MAX_ADDRESS_LENGTH,
    MAX_PERCENTAGE_DIGITS,
    PERCENTAGE_DECIMAL_PLACES,
    DEFAULT_AMOUNT,
    MAX_NAME_LENGTH,
)

from apps.common.choices import TipoTrabajoTelecomChoices
from apps.cuenta_cliente.models.sucursal import Sucursal

from .zona import ZonaTelecom
from .recargo import RecargoTelecom


class PresupuestoTelecom(CodeModel):
    """
    Cálculo de costo de una obra de telecom (instalación,
    desinstalación o reinstalación).

    La sucursal es opcional: el presupuesto puede vincularse
    a una sucursal existente, o quedar suelto (por ejemplo,
    para un sitio que todavía no es cliente). Si se indica
    una sucursal, su provincia debe coincidir con la de la
    zona elegida (ver clean()), para que el factor aplicado
    sea el que realmente corresponde al lugar de la obra.

    Guarda una copia histórica del factor de la zona y del
    recargo elegidos al momento de crearse, para que un
    cambio posterior en esos catálogos no altere presupuestos
    ya calculados.

    IMPORTANTE: mano de obra y materiales se mantienen como
    subtotales separados (pesos y dólares respectivamente),
    igual que en la planilla de origen. No se calcula un
    total combinado para no inventar un tipo de cambio.
    """

    CODE_PREFIX = QUOTE_TELECOM_CODE_PREFIX

    # ======================================================
    # RELACIONES
    # ======================================================
    sucursal = models.ForeignKey(
        Sucursal,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="presupuestos_telecom",
        verbose_name=_("Sucursal"),
    )
    
    
    zona = models.ForeignKey(
        ZonaTelecom,
        on_delete=models.PROTECT,
        related_name="presupuestos_telecom",
        verbose_name=_("Zona"),
    )

    recargo = models.ForeignKey(
        RecargoTelecom,
        on_delete=models.PROTECT,
        related_name="presupuestos_telecom",
        blank=True,
        null=True,
        verbose_name=_("Recargo aplicado"),
        help_text=_(
            "Recargo por turno/distancia/día, si "
            "corresponde. Puede no llevar ninguno."
        ),
    )

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    codigo_wo = models.CharField(
        max_length=MAX_NAME_LENGTH,
        blank=True,
        verbose_name=_("WO"),
        help_text=_(
            "Número de Work Order (orden de trabajo) con "
            "el que la empresa de telecom identifica este "
            "trabajo."
        ),
    )


    fecha_solicitud = models.DateField(
        default=timezone.localdate,
        verbose_name=_("Fecha de solicitud"),
    )

    sitio_obra = models.CharField(
        max_length=MAX_ADDRESS_LENGTH,
        verbose_name=_("Sitio de obra"),
    )

    tipo_trabajo = models.CharField(
        max_length=20,
        choices=TipoTrabajoTelecomChoices.choices,
        verbose_name=_("Tipo de trabajo"),
    )

    distancia_km = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Distancia (km)"),
        help_text=_(
            "Distancia por ruta (ida y vuelta) entre la "
            "ciudad cabecera y el sitio de obra. Es "
            "informativa: si corresponde recargo por "
            "kilometraje, agregalo como línea de detalle "
            "del catálogo, igual que en la planilla original."
        ),
    )

    # ======================================================
    # FACTORES HISTÓRICOS
    # ======================================================

    factor_multiplicador_zona = models.DecimalField(
        max_digits=MAX_PERCENTAGE_DIGITS,
        decimal_places=PERCENTAGE_DECIMAL_PLACES,
        editable=False,
        default=Decimal("1.00"),
        verbose_name=_("Factor de zona aplicado"),
    )

    factor_recargo = models.DecimalField(
        max_digits=MAX_PERCENTAGE_DIGITS,
        decimal_places=PERCENTAGE_DECIMAL_PLACES,
        editable=False,
        default=Decimal("1.00"),
        verbose_name=_("Factor de recargo aplicado"),
    )

    # ======================================================
    # TOTALES CALCULADOS
    # ======================================================

    subtotal_mano_obra = models.DecimalField(
        max_digits=14,
        decimal_places=PERCENTAGE_DECIMAL_PLACES,
        editable=False,
        default=DEFAULT_AMOUNT,
        verbose_name=_("Subtotal mano de obra (ARS)"),
    )

    subtotal_materiales = models.DecimalField(
        max_digits=14,
        decimal_places=PERCENTAGE_DECIMAL_PLACES,
        editable=False,
        default=DEFAULT_AMOUNT,
        verbose_name=_("Subtotal materiales (USD)"),
    )

    # ======================================================
    # OBSERVACIONES
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        verbose_name=_("Observaciones"),
    )

    class Meta:
        verbose_name = _("Presupuesto de telecom")
        verbose_name_plural = _("Presupuestos de telecom")

        ordering = (
            "-fecha_solicitud",
        )

    # ======================================================
    # VALIDACIÓN
    # ======================================================

    def clean(self):
        """
        Si el presupuesto está vinculado a una sucursal,
        la provincia de esa sucursal debe coincidir con la
        de la zona elegida. Evita aplicar el factor de una
        provincia distinta a la del sitio real de la obra.
        """

        super().clean()

        if self.sucursal_id and self.zona_id:
            if self.sucursal.provincia != self.zona.provincia:
                raise ValidationError(
                    {
                        "zona": _(
                            "La zona elegida (%(zona_provincia)s) no "
                            "coincide con la provincia de la "
                            "sucursal (%(sucursal_provincia)s)."
                        )
                        % {
                            "zona_provincia": self.zona.provincia,
                            "sucursal_provincia": self.sucursal.provincia,
                        }
                    }
                )

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return f"{self.codigo} - {self.sitio_obra}"

    # ======================================================
    # PERSISTENCIA
    # ======================================================

    def save(self, *args, **kwargs):
        """
        Copia los factores de zona y recargo la primera
        vez que se guarda el presupuesto, para que queden
        fijos aunque el catálogo cambie después.
        """

        if self.pk is None:
            self.factor_multiplicador_zona = (
                self.zona.factor_multiplicador
            )

            self.factor_recargo = (
                self.recargo.factor
                if self.recargo_id
                else Decimal("1.00")
            )

        super().save(*args, **kwargs)

    # ======================================================
    # MÉTODOS DE NEGOCIO
    # ======================================================

    def recalcular_totales(self, commit: bool = True):
        """
        Recalcula los subtotales de mano de obra y
        materiales a partir de las líneas de detalle.
        """

        from apps.common.choices import TipoConceptoTelecomChoices

        detalles = self.detalles.all()

        self.subtotal_mano_obra = (
            detalles.filter(
                tipo=TipoConceptoTelecomChoices.MANO_DE_OBRA
            ).aggregate(
                total=models.Sum("subtotal")
            )["total"]
            or DEFAULT_AMOUNT
        )

        self.subtotal_materiales = (
            detalles.filter(
                tipo=TipoConceptoTelecomChoices.MATERIAL
            ).aggregate(
                total=models.Sum("subtotal")
            )["total"]
            or DEFAULT_AMOUNT
        )

        if commit:
            self.save(
                update_fields=[
                    "subtotal_mano_obra",
                    "subtotal_materiales",
                ]
            )

    # ======================================================
    # PROPIEDADES CALCULADAS
    # ======================================================

    @property
    def total_mano_obra_ajustado(self):
        """
        Mano de obra con el factor de zona y el recargo
        aplicados (en pesos).
        """

        return (
            self.subtotal_mano_obra
            * self.factor_multiplicador_zona
            * self.factor_recargo
        )