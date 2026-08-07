from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.catalogo.models import ItemCatalogo

from apps.common.choices import (
    TipoProyectoDetalleChoices,
    UnidadMedidaChoices,
)

from apps.common.constants import (
    MAX_PRICE_DIGITS,
    PRICE_DECIMAL_PLACES,
    PROJECT_DETAIL_CODE_PREFIX,
)

from apps.common.models import CodeModel

from apps.dispositivo.models import Dispositivo

from .proyecto import Proyecto


class ProyectoDetalle(CodeModel):
    """
    Representa un concepto comercial o técnico incluido
    dentro de un proyecto.

    El detalle puede originarse desde:

    - un dispositivo del catálogo técnico;
    - un ítem del catálogo general.

    Cada detalle almacena una copia de la descripción,
    unidad y precio utilizados en el proyecto, para conservar
    su información histórica aunque el catálogo cambie.

    La creación, actualización, eliminación y cálculo
    económico se gestionan mediante apps.proyecto.services.
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
            "Dispositivo técnico asociado al detalle, "
            "si corresponde."
        ),
    )

    item_catalogo = models.ForeignKey(
        ItemCatalogo,
        on_delete=models.PROTECT,
        related_name="proyecto_detalles",
        blank=True,
        null=True,
        verbose_name=_("Ítem de catálogo"),
        help_text=_(
            "Material, insumo, mano de obra, servicio, licencia "
            "o viático asociado al detalle."
        ),
    )

    # ======================================================
    # CLASIFICACIÓN
    # ======================================================

    tipo = models.CharField(
        max_length=20,
        choices=TipoProyectoDetalleChoices.choices,
        db_index=True,
        verbose_name=_("Tipo"),
        help_text=_(
            "Clasificación comercial o técnica del detalle."
        ),
    )

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    descripcion = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Descripción"),
        help_text=_(
            "Descripción utilizada dentro del proyecto."
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
            MinValueValidator(
                Decimal("0.01")
            ),
        ],
        verbose_name=_("Cantidad"),
    )

    unidad = models.CharField(
        max_length=10,
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
            MinValueValidator(
                Decimal("0.00")
            ),
        ],
        verbose_name=_("Precio unitario"),
    )

    descuento_importe = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(
                Decimal("0.00")
            ),
        ],
        verbose_name=_("Descuento"),
    )

    impuestos_importe = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(
                Decimal("0.00")
            ),
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
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "proyecto",
                    "orden",
                ],
                name="unique_proyecto_detalle_orden",
            ),
        ]

    # ======================================================
    # VALIDACIONES
    # ======================================================

    def clean(self):
        """
        Valida que el detalle tenga exactamente un origen
        y que dicho origen sea coherente con su clasificación.
        """

        super().clean()

        errores = {}

        tiene_dispositivo = (
            self.dispositivo_id is not None
        )

        tiene_item_catalogo = (
            self.item_catalogo_id is not None
        )

        # ==================================================
        # ORIGEN
        # ==================================================

        if (
            not tiene_dispositivo
            and not tiene_item_catalogo
        ):
            mensaje = _(
                "Debe seleccionar un dispositivo "
                "o un ítem de catálogo."
            )

            errores["dispositivo"] = mensaje
            errores["item_catalogo"] = mensaje

        elif (
            tiene_dispositivo
            and tiene_item_catalogo
        ):
            mensaje = _(
                "No puede seleccionar simultáneamente "
                "un dispositivo y un ítem de catálogo."
            )

            errores["dispositivo"] = mensaje
            errores["item_catalogo"] = mensaje

        # ==================================================
        # CLASIFICACIÓN
        # ==================================================

        elif tiene_dispositivo:
            if (
                self.tipo
                != TipoProyectoDetalleChoices.DISPOSITIVO
            ):
                errores["__all__"] = _(
                    "El tipo del detalle debe ser Dispositivo "
                    "cuando se selecciona un dispositivo."
                )

        elif tiene_item_catalogo:
            tipo_esperado = (
                self.item_catalogo.tipo
            )

            if self.tipo != tipo_esperado:
                errores["__all__"] = _(
                    "El tipo del detalle debe coincidir con "
                    "el tipo del ítem seleccionado: %(tipo)s."
                ) % {
                    "tipo": (
                        self.item_catalogo.get_tipo_display()
                    ),
                }

        # ==================================================
        # DESCUENTO
        # ==================================================

        if (
            self.descuento_importe is not None
            and self.descuento_importe
            > self.importe_bruto
        ):
            errores["descuento_importe"] = _(
                "El descuento no puede ser mayor "
                "que el importe bruto."
            )

        if errores:
            raise ValidationError(
                errores
            )

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
        Devuelve el importe anterior a descuentos
        e impuestos.
        """

        cantidad = (
            self.cantidad
            or Decimal("0.00")
        )

        precio = (
            self.precio_unitario
            or Decimal("0.00")
        )

        return cantidad * precio

    @property
    def es_dispositivo(self):
        """
        Indica si el origen del detalle
        es un dispositivo.
        """

        return self.dispositivo_id is not None

    @property
    def es_item_catalogo(self):
        """
        Indica si el origen del detalle
        es un ítem del catálogo general.
        """

        return self.item_catalogo_id is not None

    @property
    def origen(self):
        """
        Devuelve el dispositivo o ítem
        asociado al detalle.
        """

        return (
            self.dispositivo
            or self.item_catalogo
        )

    @property
    def controla_stock(self):
        """
        Indica si el detalle proviene
        de un ítem inventariable.
        """

        return bool(
            self.item_catalogo_id
            and self.item_catalogo.es_inventariable
        )