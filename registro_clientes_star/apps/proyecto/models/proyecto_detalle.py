from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from apps.catalogo.models import ItemCatalogo

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
    Representa un concepto comercial o técnico incluido
    dentro de un proyecto.

    El detalle puede originarse desde:

    - un dispositivo del catálogo técnico;
    - un ítem del catálogo general.

    Cada detalle almacena una copia de la descripción,
    unidad y precio utilizados en el proyecto, para conservar
    su información histórica aunque el catálogo cambie.
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
            MinValueValidator(Decimal("0.01")),
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
        y que dicho origen coincida con el tipo seleccionado.
        """

        super().clean()

        errores = {}

        tiene_dispositivo = self.dispositivo_id is not None
        tiene_item_catalogo = self.item_catalogo_id is not None

        # Debe existir exactamente uno.
        if not tiene_dispositivo and not tiene_item_catalogo:
            mensaje = _(
                "Debe seleccionar un dispositivo o un ítem de catálogo."
            )

            errores["dispositivo"] = mensaje
            errores["item_catalogo"] = mensaje

        if tiene_dispositivo and tiene_item_catalogo:
            mensaje = _(
                "No puede seleccionar simultáneamente "
                "un dispositivo y un ítem de catálogo."
            )

            errores["dispositivo"] = mensaje
            errores["item_catalogo"] = mensaje

        # Los dispositivos deben utilizar el tipo DISPOSITIVO.
        if (
            tiene_dispositivo
            and self.tipo
            != TipoProyectoDetalleChoices.DISPOSITIVO
        ):
            errores["tipo"] = _(
                "Cuando se selecciona un dispositivo, "
                "el tipo debe ser Dispositivo."
            )

        # Los ítems deben coincidir con su clasificación.
        if tiene_item_catalogo:
            tipo_esperado = self.item_catalogo.tipo

            if self.tipo != tipo_esperado:
                errores["tipo"] = _(
                    "El tipo del detalle debe coincidir con el tipo "
                    "del ítem seleccionado: %(tipo)s."
                ) % {
                    "tipo": self.item_catalogo.get_tipo_display(),
                }

        if self.descuento_importe > self.importe_bruto:
            errores["descuento_importe"] = _(
                "El descuento no puede ser mayor "
                "que el importe bruto."
            )

        if errores:
            raise ValidationError(errores)

    # ======================================================
    # MÉTODOS DE NEGOCIO
    # ======================================================

    def completar_desde_origen(self):
        """
        Completa valores iniciales desde el dispositivo
        o desde el ítem de catálogo.

        Los valores ya cargados manualmente no se reemplazan,
        salvo el tipo, que debe reflejar el origen seleccionado.
        """

        if self.dispositivo_id:
            self.tipo = TipoProyectoDetalleChoices.DISPOSITIVO

            if not self.descripcion:
                self.descripcion = (
                    self.dispositivo.nombre_comercial
                )

            if self.precio_unitario == Decimal("0.00"):
                self.precio_unitario = (
                    self.dispositivo.precio_mercado
                )

            self.unidad = UnidadMedidaChoices.UNIDAD

            return

        if self.item_catalogo_id:
            self.tipo = self.item_catalogo.tipo

            if not self.descripcion:
                self.descripcion = self.item_catalogo.nombre

            if self.precio_unitario == Decimal("0.00"):
                self.precio_unitario = (
                    self.item_catalogo.precio_venta
                )

            self.unidad = self.item_catalogo.unidad

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
        Guarda el detalle, completa los datos desde su origen,
        calcula los importes y actualiza el proyecto.
        """

        self.completar_desde_origen()
        self.calcular_importes()

        with transaction.atomic():
            super().save(*args, **kwargs)
            self.proyecto.actualizar_totales()

    # ======================================================
    # DELETE
    # ======================================================

    def delete(self, *args, **kwargs):
        """
        Elimina el detalle y actualiza los totales
        del proyecto relacionado.
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
        Devuelve el importe anterior a descuentos e impuestos.
        """

        cantidad = self.cantidad or Decimal("0.00")
        precio = self.precio_unitario or Decimal("0.00")

        return cantidad * precio

    @property
    def es_dispositivo(self):
        return self.dispositivo_id is not None

    @property
    def es_item_catalogo(self):
        return self.item_catalogo_id is not None

    @property
    def origen(self):
        """
        Devuelve el dispositivo o ítem asociado.
        """

        return self.dispositivo or self.item_catalogo

    @property
    def controla_stock(self):
        """
        Indica si el detalle proviene de un ítem inventariable.
        """

        return bool(
            self.item_catalogo_id
            and self.item_catalogo.es_inventariable
        )