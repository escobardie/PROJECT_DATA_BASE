from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel

from apps.common.constants import (
    CATALOG_ITEM_CODE_PREFIX,
    MAX_DESCRIPTION_LENGTH,
    MAX_NAME_LENGTH,
    MAX_PRICE_DIGITS,
    PRICE_DECIMAL_PLACES,
)

from apps.common.choices import (
    UnidadMedidaChoices,
)

from apps.common.choices import (
    TipoItemCatalogoChoices,
)

from .categoria_catalogo import CategoriaCatalogo


class ItemCatalogo(CodeModel):
    """
    Representa un concepto valorizado reutilizable.

    Puede corresponder a materiales, insumos, mano de obra,
    servicios, licencias, viáticos u otros conceptos comerciales.

    Los materiales e insumos pueden participar posteriormente
    del control de stock.
    """

    CODE_PREFIX = CATALOG_ITEM_CODE_PREFIX

    # ======================================================
    # RELACIONES
    # ======================================================

    categoria = models.ForeignKey(
        CategoriaCatalogo,
        on_delete=models.PROTECT,
        related_name="items",
        verbose_name=_("Categoría"),
        help_text=_(
            "Categoría utilizada para organizar el ítem."
        ),
    )

    # ======================================================
    # CLASIFICACIÓN
    # ======================================================

    tipo = models.CharField(
        max_length=20,
        choices=TipoItemCatalogoChoices.choices,
        db_index=True,
        verbose_name=_("Tipo"),
        help_text=_(
            "Tipo comercial u operativo del concepto."
        ),
    )

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    nombre = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name=_("Nombre"),
        help_text=_(
            "Nombre comercial o identificativo del ítem."
        ),
    )

    descripcion = models.TextField(
        max_length=MAX_DESCRIPTION_LENGTH,
        blank=True,
        default="",
        verbose_name=_("Descripción"),
        help_text=_(
            "Descripción comercial, técnica u operativa del ítem."
        ),
    )

    unidad = models.CharField(
        max_length=10,
        choices=UnidadMedidaChoices.choices,
        default=UnidadMedidaChoices.UNIDAD,
        verbose_name=_("Unidad de medida"),
        help_text=_(
            "Unidad utilizada para calcular la cantidad del concepto."
        ),
    )

    # ======================================================
    # INFORMACIÓN ECONÓMICA
    # ======================================================

    costo = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
        verbose_name=_("Costo"),
        help_text=_(
            "Costo interno o valor de adquisición del concepto."
        ),
    )

    precio_venta = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
        verbose_name=_("Precio de venta"),
        help_text=_(
            "Precio sugerido para utilizar en proyectos "
            "y documentos comerciales."
        ),
    )

    # ======================================================
    # INVENTARIO
    # ======================================================

    controla_stock = models.BooleanField(
        default=False,
        verbose_name=_("Controla stock"),
        help_text=_(
            "Indica si el ítem deberá participar del control "
            "de existencias."
        ),
    )

    # ======================================================
    # ORGANIZACIÓN
    # ======================================================

    orden = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_("Orden"),
        help_text=_(
            "Orden de presentación del ítem dentro de su categoría."
        ),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:
        verbose_name = _("Ítem de catálogo")
        verbose_name_plural = _("Ítems de catálogo")

        ordering = (
            "categoria",
            "orden",
            "nombre",
        )

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "categoria",
                    "nombre",
                ],
                name="unique_item_categoria_nombre",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "categoria",
                    "tipo",
                ],
                name="idx_itemcat_cat_tipo",
            ),
            models.Index(
                fields=[
                    "tipo",
                    "controla_stock",
                ],
                name="idx_itemcat_tipo_stock",
            ),
            models.Index(
                fields=[
                    "categoria",
                    "orden",
                    "nombre",
                ],
                name="idx_itemcat_cat_orden",
            ),
        ]

    # ======================================================
    # VALIDACIONES
    # ======================================================

    def clean(self):
        """
        Valida la coherencia comercial y de inventario del ítem.
        """

        super().clean()

        errores = {}

        tipos_con_stock = {
            TipoItemCatalogoChoices.MATERIAL,
            TipoItemCatalogoChoices.INSUMO,
        }

        if (
            self.controla_stock
            and self.tipo not in tipos_con_stock
        ):
            errores["controla_stock"] = _(
                "Solamente los materiales e insumos pueden "
                "participar del control de stock."
            )

        if (
            self.precio_venta > Decimal("0.00")
            and self.precio_venta < self.costo
        ):
            errores["precio_venta"] = _(
                "El precio de venta no puede ser menor que el costo."
            )

        if errores:
            raise ValidationError(errores)

    # ======================================================
    # NORMALIZACIÓN
    # ======================================================

    def normalizar_datos(self):
        """
        Normaliza el nombre antes de guardar el ítem.
        """

        if self.nombre:
            self.nombre = " ".join(
                self.nombre.strip().split()
            )

    # ======================================================
    # SAVE
    # ======================================================

    def save(self, *args, **kwargs):
        """
        Guarda el ítem normalizando previamente sus datos.
        """

        self.normalizar_datos()

        super().save(*args, **kwargs)

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return (
            f"{self.codigo} - "
            f"{self.nombre}"
        )

    # ======================================================
    # PROPIEDADES
    # ======================================================

    @property
    def margen_bruto(self):
        """
        Devuelve la diferencia entre el precio de venta y el costo.
        """

        return self.precio_venta - self.costo

    @property
    def porcentaje_margen(self):
        """
        Devuelve el margen bruto calculado sobre el costo.
        """

        if self.costo <= Decimal("0.00"):
            return Decimal("0.00")

        return (
            (self.margen_bruto / self.costo)
            * Decimal("100.00")
        )

    @property
    def es_material(self):
        return (
            self.tipo
            == TipoItemCatalogoChoices.MATERIAL
        )

    @property
    def es_insumo(self):
        return (
            self.tipo
            == TipoItemCatalogoChoices.INSUMO
        )

    @property
    def es_mano_obra(self):
        return (
            self.tipo
            == TipoItemCatalogoChoices.MANO_OBRA
        )

    @property
    def es_servicio(self):
        return (
            self.tipo
            == TipoItemCatalogoChoices.SERVICIO
        )

    @property
    def es_inventariable(self):
        """
        Indica si el ítem participa del control de stock.
        """

        return (
            self.controla_stock
            and self.tipo
            in {
                TipoItemCatalogoChoices.MATERIAL,
                TipoItemCatalogoChoices.INSUMO,
            }
        )