from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel

from apps.common.constants import (
    PROJECT_CODE_PREFIX,
    MAX_NAME_LENGTH,
    MAX_PRICE_DIGITS,
    PRICE_DECIMAL_PLACES,
)

from apps.common.choices import (
    MonedaChoices,
)

from apps.cuenta_cliente.models import Sucursal

from apps.common.choices import (
    EstadoProyectoChoices,
)


class Proyecto(CodeModel):
    """
    Representa un trabajo comercial y operativo realizado
    para una sucursal.

    El proyecto concentra la planificación, cotización,
    aprobación, ejecución y cierre de un trabajo.

    Puede incluir dispositivos, materiales, servicios,
    mano de obra, licencias, viáticos y otros conceptos
    mediante sus detalles.

    A partir de un proyecto pueden generarse una o varias
    órdenes de trabajo.
    """

    CODE_PREFIX = PROJECT_CODE_PREFIX

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
        related_name="proyectos",
        verbose_name=_("Sucursal"),
        help_text=_(
            "Sucursal para la cual se realiza el proyecto."
        ),
    )

    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="proyectos_responsable",
        verbose_name=_("Responsable"),
        help_text=_(
            "Usuario responsable de administrar el proyecto."
        ),
    )

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    nombre = models.CharField(
        max_length=MAX_NAME_LENGTH,
        db_index=True,
        verbose_name=_("Nombre"),
        help_text=_(
            "Nombre o referencia principal del proyecto."
        ),
    )

    descripcion = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Descripción"),
        help_text=_(
            "Descripción general del alcance del proyecto."
        ),
    )

    # ======================================================
    # CONDICIONES COMERCIALES
    # ======================================================

    moneda = models.CharField(
        max_length=3,
        choices=MonedaChoices.choices,
        default=MonedaChoices.ARS,
        verbose_name=_("Moneda"),
    )

    # ======================================================
    # FECHAS
    # ======================================================

    fecha_creacion = models.DateField(
        db_index=True,
        verbose_name=_("Fecha de creación"),
        help_text=_(
            "Fecha comercial u operativa de creación del proyecto."
        ),
    )

    fecha_planificada = models.DateField(
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_("Fecha planificada"),
        help_text=_(
            "Fecha prevista para comenzar la ejecución del proyecto."
        ),
    )

    fecha_inicio = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de inicio"),
        help_text=_(
            "Fecha real en que comenzó la ejecución del proyecto."
        ),
    )

    fecha_finalizacion = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de finalización"),
        help_text=_(
            "Fecha real en que finalizó el proyecto."
        ),
    )

    # ======================================================
    # ESTADO
    # ======================================================

    estado = models.CharField(
        max_length=30,
        choices=EstadoProyectoChoices.choices,
        default=EstadoProyectoChoices.BORRADOR,
        db_index=True,
        verbose_name=_("Estado"),
        help_text=_(
            "Estado actual del ciclo de vida del proyecto."
        ),
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
        default=Decimal("0.00"),
        editable=False,
        verbose_name=_("Subtotal"),
        help_text=_(
            "Suma de los subtotales de los detalles del proyecto."
        ),
    )

    descuento_total = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=Decimal("0.00"),
        editable=False,
        verbose_name=_("Descuento total"),
        help_text=_(
            "Suma de los descuentos aplicados a los detalles."
        ),
    )

    impuestos = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=Decimal("0.00"),
        editable=False,
        verbose_name=_("Impuestos"),
        help_text=_(
            "Suma de los impuestos aplicados a los detalles."
        ),
    )

    total = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=Decimal("0.00"),
        editable=False,
        verbose_name=_("Total"),
        help_text=_(
            "Importe final del proyecto."
        ),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:
        verbose_name = _("Proyecto")
        verbose_name_plural = _("Proyectos")

        ordering = (
            "-created_at",
        )

        indexes = [
            models.Index(
                fields=[
                    "estado",
                ],
                name="idx_proy_estado",
            ),
            models.Index(
                fields=[
                    "fecha_creacion",
                ],
                name="idx_proy_fec_crea",
            ),
            models.Index(
                fields=[
                    "fecha_planificada",
                ],
                name="idx_proy_fec_plan",
            ),
            models.Index(
                fields=[
                    "sucursal",
                    "estado",
                ],
                name="idx_proy_suc_estado",
            ),
        ]

    # ======================================================
    # VALIDACIONES
    # ======================================================

    def clean(self):
        """
        Valida la coherencia temporal del proyecto.
        """

        super().clean()

        errores = {}

        if (
            self.fecha_planificada
            and self.fecha_planificada < self.fecha_creacion
        ):
            errores["fecha_planificada"] = _(
                "La fecha planificada no puede ser anterior "
                "a la fecha de creación."
            )

        if (
            self.fecha_inicio
            and self.fecha_inicio < self.fecha_creacion
        ):
            errores["fecha_inicio"] = _(
                "La fecha de inicio no puede ser anterior "
                "a la fecha de creación."
            )

        if (
            self.fecha_finalizacion
            and not self.fecha_inicio
        ):
            errores["fecha_finalizacion"] = _(
                "Debe registrar la fecha de inicio antes "
                "de indicar la fecha de finalización."
            )

        if (
            self.fecha_inicio
            and self.fecha_finalizacion
            and self.fecha_finalizacion < self.fecha_inicio
        ):
            errores["fecha_finalizacion"] = _(
                "La fecha de finalización no puede ser anterior "
                "a la fecha de inicio."
            )

        if errores:
            raise ValidationError(errores)

    # ======================================================
    # MÉTODOS DE NEGOCIO
    # ======================================================

    def actualizar_totales(self, commit=True):
        """
        Recalcula los importes del proyecto a partir
        de sus detalles.
        """

        resumen = self.detalles.aggregate(
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

    def cambiar_estado(self, estado, commit=True):
        """
        Cambia el estado actual del proyecto.
        """

        estados_validos = {
            valor
            for valor, _etiqueta in EstadoProyectoChoices.choices
        }

        if estado not in estados_validos:
            raise ValidationError(
                {
                    "estado": _(
                        "El estado indicado no es válido."
                    )
                }
            )

        self.estado = estado

        if commit:
            self.save(
                update_fields=(
                    "estado",
                ),
            )

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return (
            f"{self.codigo} - "
            f"{self.nombre} "
            f"({self.sucursal})"
        )

    # ======================================================
    # PROPIEDADES
    # ======================================================

    @property
    def cantidad_detalles(self):
        """
        Devuelve la cantidad de detalles del proyecto.
        """

        return self.detalles.count()

    @property
    def cantidad_ordenes_trabajo(self):
        """
        Devuelve la cantidad de órdenes de trabajo
        relacionadas con el proyecto.
        """

        return self.ordenes_trabajo.count()

    @property
    def borrador(self):
        """
        Indica si el proyecto está en borrador.
        """

        return (
            self.estado
            == EstadoProyectoChoices.BORRADOR
        )

    @property
    def pendiente_aprobacion(self):
        """
        Indica si el proyecto está pendiente de aprobación.
        """

        return (
            self.estado
            == EstadoProyectoChoices.PENDIENTE_APROBACION
        )

    @property
    def aprobado(self):
        """
        Indica si el proyecto fue aprobado.
        """

        return (
            self.estado
            == EstadoProyectoChoices.APROBADO
        )

    @property
    def planificado(self):
        """
        Indica si el proyecto está planificado.
        """

        return (
            self.estado
            == EstadoProyectoChoices.PLANIFICADO
        )

    @property
    def en_ejecucion(self):
        """
        Indica si el proyecto está en ejecución.
        """

        return (
            self.estado
            == EstadoProyectoChoices.EN_EJECUCION
        )

    @property
    def finalizado(self):
        """
        Indica si el proyecto está finalizado.
        """

        return (
            self.estado
            == EstadoProyectoChoices.FINALIZADO
        )

    @property
    def cancelado(self):
        """
        Indica si el proyecto fue cancelado.
        """

        return (
            self.estado
            == EstadoProyectoChoices.CANCELADO
        )