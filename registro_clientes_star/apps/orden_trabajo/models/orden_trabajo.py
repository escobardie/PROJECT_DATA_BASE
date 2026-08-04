from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel

from apps.common.constants import (
    ORDER_CODE_PREFIX,
    MAX_TITLE_LENGTH,
)

from apps.common.choices import (
    TipoOrdenTrabajoChoices,
    EstadoOrdenTrabajoChoices,
    PrioridadOrdenTrabajoChoices,
)

from apps.cuenta_cliente.models import Sucursal
from apps.instalacion.models import Instalacion
from apps.proyecto.models import Proyecto
from apps.servicio.models import ServicioContratado
from apps.telecom.models import PresupuestoTelecom
from apps.usuarios.models import Usuario


class OrdenTrabajo(CodeModel):
    """
    Representa una orden de trabajo operativa.

    Gestiona la planificación, ejecución y trazabilidad de trabajos
    técnicos relacionados con una sucursal, proyecto, servicio
    contratado, presupuesto Telecom o instalación.

    Una orden de trabajo no almacena información económica.
    """

    CODE_PREFIX = ORDER_CODE_PREFIX

    # ======================================================
    # RELACIONES
    # ======================================================

    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo",
        blank=True,
        null=True,
        verbose_name=_("Sucursal"),
        help_text=_(
            "Sucursal relacionada con la orden de trabajo, "
            "si corresponde."
        ),
    )

    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo",
        blank=True,
        null=True,
        verbose_name=_("Proyecto"),
        help_text=_(
            "Proyecto relacionado con la orden de trabajo, "
            "si corresponde."
        ),
    )

    servicio_contratado = models.ForeignKey(
        ServicioContratado,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo",
        blank=True,
        null=True,
        verbose_name=_("Servicio contratado"),
        help_text=_(
            "Servicio contratado relacionado con la orden de trabajo, "
            "si corresponde."
        ),
    )

    presupuesto_telecom = models.ForeignKey(
        PresupuestoTelecom,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo",
        blank=True,
        null=True,
        verbose_name=_("Presupuesto Telecom"),
        help_text=_(
            "Presupuesto Telecom relacionado con la orden de trabajo, "
            "si corresponde."
        ),
    )

    instalacion = models.OneToOneField(
        Instalacion,
        on_delete=models.PROTECT,
        related_name="orden_trabajo",
        blank=True,
        null=True,
        verbose_name=_("Instalación"),
        help_text=_(
            "Instalación generada o asociada directamente "
            "con esta orden de trabajo."
        ),
    )

    instalacion_relacionada = models.ForeignKey(
        Instalacion,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo_relacionadas",
        blank=True,
        null=True,
        verbose_name=_("Instalación relacionada"),
        help_text=_(
            "Instalación existente sobre la cual se realizará "
            "el trabajo."
        ),
    )

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    titulo = models.CharField(
        max_length=MAX_TITLE_LENGTH,
        verbose_name=_("Título"),
        help_text=_(
            "Título descriptivo de la orden de trabajo."
        ),
    )

    descripcion = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Descripción"),
        help_text=_(
            "Descripción detallada del trabajo que debe realizarse."
        ),
    )

    # ======================================================
    # CLASIFICACIÓN
    # ======================================================

    tipo = models.CharField(
        max_length=30,
        choices=TipoOrdenTrabajoChoices.choices,
        default=TipoOrdenTrabajoChoices.INSTALACION,
        db_index=True,
        verbose_name=_("Tipo"),
    )

    estado = models.CharField(
        max_length=30,
        choices=EstadoOrdenTrabajoChoices.choices,
        default=EstadoOrdenTrabajoChoices.BORRADOR,
        db_index=True,
        verbose_name=_("Estado"),
    )

    prioridad = models.CharField(
        max_length=20,
        choices=PrioridadOrdenTrabajoChoices.choices,
        default=PrioridadOrdenTrabajoChoices.MEDIA,
        db_index=True,
        verbose_name=_("Prioridad"),
    )

    # ======================================================
    # RECEPCIÓN DE LA SOLICITUD
    # ======================================================

    fecha_recepcion_solicitud = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de recepción de la solicitud"),
        help_text=_(
            "Fecha y hora en que la empresa recibió "
            "la solicitud del cliente."
        ),
    )

    usuario_recepcion_solicitud = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo_recibidas",
        blank=True,
        null=True,
        verbose_name=_("Recepcionado por"),
        help_text=_(
            "Usuario que registró la recepción de la solicitud."
        ),
    )

    # ======================================================
    # PLANIFICACIÓN Y EJECUCIÓN
    # ======================================================

    responsable = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo_responsable",
        verbose_name=_("Responsable"),
        help_text=_(
            "Usuario responsable de coordinar la orden de trabajo."
        ),
    )

    fecha_programada = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_("Fecha programada"),
        help_text=_(
            "Fecha y hora programadas para ejecutar la orden."
        ),
    )

    fecha_inicio = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de inicio"),
        help_text=_(
            "Fecha y hora en que comenzó la ejecución de la orden."
        ),
    )

    usuario_inicio = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo_iniciadas",
        blank=True,
        null=True,
        verbose_name=_("Iniciado por"),
        help_text=_(
            "Usuario que registró el inicio de la orden."
        ),
    )

    fecha_finalizacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de finalización"),
        help_text=_(
            "Fecha y hora en que finalizó la ejecución de la orden."
        ),
    )

    usuario_finalizacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo_finalizadas",
        blank=True,
        null=True,
        verbose_name=_("Finalizado por"),
        help_text=_(
            "Usuario que registró la finalización de la orden."
        ),
    )

    # ======================================================
    # TRAZABILIDAD
    # ======================================================

    fecha_envio_cliente = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de envío al cliente"),
        help_text=_(
            "Fecha y hora en que la orden fue enviada al cliente."
        ),
    )

    usuario_envio_cliente = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo_enviadas",
        blank=True,
        null=True,
        verbose_name=_("Enviado por"),
        help_text=_(
            "Usuario que registró el envío de la orden al cliente."
        ),
    )

    fecha_aceptacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de aceptación"),
        help_text=_(
            "Fecha y hora en que el cliente aceptó la orden."
        ),
    )

    usuario_aceptacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo_aceptadas",
        blank=True,
        null=True,
        verbose_name=_("Aceptación registrada por"),
        help_text=_(
            "Usuario que registró la aceptación del cliente."
        ),
    )

    fecha_facturacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de facturación"),
        help_text=_(
            "Fecha y hora en que se facturó la orden."
        ),
    )

    usuario_facturacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo_facturadas",
        blank=True,
        null=True,
        verbose_name=_("Facturado por"),
        help_text=_(
            "Usuario que registró la facturación de la orden."
        ),
    )

    fecha_cobro = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de cobro"),
        help_text=_(
            "Fecha y hora en que se registró el cobro de la orden."
        ),
    )

    usuario_cobro = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo_cobradas",
        blank=True,
        null=True,
        verbose_name=_("Cobrado por"),
        help_text=_(
            "Usuario que registró el cobro de la orden."
        ),
    )

    # ======================================================
    # OBSERVACIONES
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Observaciones"),
        help_text=_(
            "Observaciones generales sobre la orden de trabajo."
        ),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:
        verbose_name = _("Orden de trabajo")
        verbose_name_plural = _("Órdenes de trabajo")

        ordering = (
            "-created_at",
        )

        indexes = [
            models.Index(
                fields=[
                    "estado",
                ],
                name="idx_ot_estado",
            ),
            models.Index(
                fields=[
                    "prioridad",
                ],
                name="idx_ot_prioridad",
            ),
            models.Index(
                fields=[
                    "fecha_programada",
                ],
                name="idx_ot_fecha_prog",
            ),
            models.Index(
                fields=[
                    "responsable",
                ],
                name="idx_ot_responsable",
            ),
            models.Index(
                fields=[
                    "proyecto",
                    "estado",
                ],
                name="idx_ot_proy_estado",
            ),
        ]

    # ======================================================
    # VALIDACIONES
    # ======================================================

    def clean(self):
        """
        Ejecuta las validaciones de negocio de la orden de trabajo.
        """

        super().clean()

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return (
            f"{self.codigo} - "
            f"{self.titulo}"
        )

    # ======================================================
    # PROPIEDADES
    # ======================================================

    @property
    def tiene_instalacion(self):
        """
        Indica si la orden posee una instalación asociada
        directamente.
        """

        return self.instalacion_id is not None

    @property
    def tiene_instalacion_relacionada(self):
        """
        Indica si la orden se ejecuta sobre una instalación
        existente.
        """

        return self.instalacion_relacionada_id is not None

    @property
    def esta_finalizada(self):
        """
        Indica si la orden está finalizada.
        """

        return (
            self.estado
            == EstadoOrdenTrabajoChoices.FINALIZADA
        )

    @property
    def esta_facturada(self):
        """
        Indica si la orden fue facturada.
        """

        return self.fecha_facturacion is not None

    @property
    def esta_cobrada(self):
        """
        Indica si la orden fue cobrada.
        """

        return self.fecha_cobro is not None

    @property
    def fue_enviada_cliente(self):
        """
        Indica si la orden fue enviada al cliente.
        """

        return self.fecha_envio_cliente is not None

    @property
    def fue_aceptada(self):
        """
        Indica si la aceptación del cliente fue registrada.
        """

        return self.fecha_aceptacion is not None