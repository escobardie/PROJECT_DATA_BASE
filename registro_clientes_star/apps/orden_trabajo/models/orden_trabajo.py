from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel

from apps.common.constants import (
    ORDER_CODE_PREFIX,
    MAX_NAME_LENGTH,
    MAX_TITLE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_OBSERVATION_LENGTH,
)

from apps.common.choices import (
    TipoOrdenTrabajoChoices,
    EstadoOrdenTrabajoChoices,
    PrioridadOrdenTrabajoChoices,
)

from apps.proyecto.models import Proyecto
from apps.usuarios.models import Usuario

from apps.cuenta_cliente.models import Sucursal

from apps.servicio.models import ServicioContratado

from apps.instalacion.models import Instalacion

from apps.telecom.models import PresupuestoTelecom


class OrdenTrabajo(CodeModel):
    """
    Representa una orden de trabajo operativa.

    Gestiona la ejecución de trabajos técnicos
    relacionados con un proyecto.

    No contiene información económica.
    """

    CODE_PREFIX = ORDER_CODE_PREFIX


    # # ======================================================
    # # RELACIONES BASE DE 
    # # ======================================================
    # proyecto = models.ForeignKey(
    #     Proyecto,
    #     on_delete=models.PROTECT,
    #     related_name="ordenes_trabajo",
    #     blank=True,
    #     null=True,
    #     verbose_name=_("Proyecto"),
    #     help_text=_("Instalación relacionada si corresponde."),
    # )

    # ======================================================
    # INFORMACIÓN GENERAL
    # CODIGO - TITULO - DESCRIPCION
    # ======================================================

    titulo = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name=_("Título"),
        help_text=_("Título de la orden de trabajo."),
    )

    descripcion = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Descripción"),
        help_text=_("Descripción detallada de la orden de trabajo."),
    )
    # ======================================================
    # ORIGEN DE LA ORDEN
    # SUCURSAL - PROYECTO - PRESUPUESTO - SERVICIO CONTRATADO - SERVICIO TECNICO - OTROS
    #     Estado de la revisión
    # Hasta ahora tenemos aprobado:
    # Organización de imports.
    # Relaciones.
    # Relación 1 OT ↔ 1 Instalación.
    # Orígenes opcionales de la OT.
    # Responsable de la OT.
    # Estructura general del modelo.
    # ======================================================
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo",
        blank=True,
        null=True,
        verbose_name=_("Sucursal"),
        help_text=_("Sucrusal relacionada si corresponde."),
    )
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo",
        blank=True,
        null=True,
        verbose_name=_("Proyecto"),
        help_text=_("Proyecto relacionado si corresponde."),
    )
    servicio_contratado = models.ForeignKey(
        ServicioContratado,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo",
        blank=True,
        null=True,
        verbose_name=_("Servicio Contratado"),
        help_text=_("Servicio contratado relacionado si corresponde."),
    )
    presupuesto_telecom = models.ForeignKey(
        PresupuestoTelecom,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo",
        blank=True,
        null=True,
        verbose_name=_("Presupuesto Telecom"),
        help_text=_("Presupuesto de telecom relacionado si corresponde."),
    )
    instalacion = models.OneToOneField(
        Instalacion,
        on_delete=models.PROTECT,
        related_name="orden_trabajo",
        blank=True,
        null=True,
        verbose_name=_("Instalación"),
        help_text=_("Instalación relacionada si corresponde."),
    )
    instalacion_relacionada = models.ForeignKey(
        Instalacion,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo_relacionadas",
        blank=True,
        null=True,
        verbose_name=_("Instalación relacionada"),
        help_text=_(
            "Instalación existente sobre la cual se realizará el trabajo."
        ),
    )

    # ======================================================
    # CLASIFICACIÓN
    # TIPO - ESTADO - PRIORIDAD
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
        verbose_name=_("Fecha recepción de la solicitud"),
        help_text=_(
            "Fecha y hora en que la empresa recibió la solicitud del cliente."
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
    # PLANIFICACIÓN
    # RESPONSABLE - FECHA PROGRAMADA - FECHA INICIO - FECHA FIN - TIEMPO ESTIMADO
    # ======================================================
    responsable = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo_responsable",
        verbose_name=_("Responsable"),
        help_text=_("Usuario responsable de coordinar la orden."),
    )

    fecha_programada = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha programada"),
        help_text=_("Fecha y hora programada para la ejecución de la orden."),
    )

    fecha_inicio = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha inicio"),
        help_text=_("Fecha y hora de inicio de la ejecución de la orden."),
    )

    usuario_inicio = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo_iniciadas",
        blank=True,
        null=True,
        verbose_name=_("Iniciado por"),
        help_text=_("Usuario que inició la ejecución de la orden."),
    )

    fecha_finalizacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha finalización"),
        help_text=_("Fecha y hora de finalización de la ejecución de la orden."),
    )

    usuario_finalizacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo_finalizadas",
        blank=True,
        null=True,
        verbose_name=_("Finalizado por"),
        help_text=_("Usuario que finalizó la ejecución de la orden."),
    )
    # ======================================================
    # TRAZABILIDAD
    # FECHA ENVIO CLIENTE - FECHA ACEPATADA CLIENTE - FECHA CIERRE - FECHA FACTURACION - TIEMPO TOTAL
    # ======================================================

    # ----------------------------
    # Envío al cliente
    # ----------------------------

    fecha_envio_cliente = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha envío al cliente"),
        help_text=_("Fecha y hora en que se envió la orden al cliente."),
    )

    usuario_envio_cliente = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo_enviadas",
        blank=True,
        null=True,
        verbose_name=_("Enviado por"),
        help_text=_("Usuario que envió la orden al cliente."),
    )

    # ----------------------------
    # Aceptación del cliente
    # ----------------------------

    fecha_aceptacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha aceptación"),
        help_text=_("Fecha y hora en que el cliente aceptó."),
    )

    usuario_aceptacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo_aceptadas",
        blank=True,
        null=True,
        verbose_name=_("Aceptado por"),
        help_text=_("Usuario que confirmo la aceptacion del cliente."),
    )

    # ----------------------------
    # Facturación
    # ----------------------------

    fecha_facturacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha facturación"),
        help_text=_("Fecha y hora en que se facturó la orden."),
    )

    usuario_facturacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo_facturadas",
        blank=True,
        null=True,
        verbose_name=_("Facturado por"),
        help_text=_("Usuario que facturó la orden."),
    )

    # ----------------------------
    # Cobro
    # ----------------------------

    fecha_cobro = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha cobro"),
        help_text=_("Fecha y hora en que se cobró la orden."),
    )

    usuario_cobro = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo_cobradas",
        blank=True,
        null=True,
        verbose_name=_("Cobrado por"),
        help_text=_("Usuario que realizó el cobro de la orden."),
    )

    # ======================================================
    # OBSERVACIONES
    # ======================================================
    observaciones = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Observaciones"),
        help_text=_("Observaciones generales sobre la orden de trabajo."),  
    )
    
    # ======================================================
    # AUDITORÍA
    # CREATED AT - CREATED BY - UPDATED AT - UPDATED BY
    # ======================================================

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

        ]

    # ======================================================
    # VALIDACIONES
    # ======================================================
    def clean(self):
        """
        Valida reglas de negocio de la orden de trabajo.
        """

        super().clean()

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return f"{self.codigo} - {self.titulo}"
    
    # ======================================================
    # PROPIEDADES
    # ======================================================

    @property
    def tiene_instalacion(self):
        """
        Indica si posee una instalación asociada.
        """

        return hasattr(
            self,
            "instalacion",
        )


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

        return bool(
            self.fecha_facturacion
        )
    