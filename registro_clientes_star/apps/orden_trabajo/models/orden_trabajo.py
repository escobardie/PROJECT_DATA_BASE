from django.core.exceptions import ObjectDoesNotExist, ValidationError
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
from apps.proyecto.models import Proyecto
from apps.servicio.models import ServicioContratado
from apps.telecom.models import PresupuestoTelecom
from apps.usuarios.models import Usuario


class OrdenTrabajo(CodeModel):
    """
    Representa una orden de trabajo operativa.

    Gestiona la planificación, ejecución y trazabilidad
    de trabajos técnicos relacionados con una sucursal,
    proyecto, servicio contratado, presupuesto Telecom
    o instalación existente.

    Una orden de trabajo puede generar una instalación,
    pero no almacena información económica.
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

    instalacion_relacionada = models.ForeignKey(
        "instalacion.Instalacion",
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
                    "proyecto",
                    "estado",
                ],
                name="idx_ot_proy_estado",
            ),
            models.Index(
                fields=[
                    "servicio_contratado",
                    "estado",
                ],
                name="idx_ot_serv_estado",
            ),
            models.Index(
                fields=[
                    "responsable",
                    "fecha_programada",
                ],
                name="idx_ot_resp_fecha",
            ),
        ]

    # ======================================================
    # VALIDACIONES
    # ======================================================

    def clean(self):
        """
        Valida el origen y la coherencia temporal
        de la orden de trabajo.
        """

        super().clean()

        errores = {}

        # ==================================================
        # ORIGEN DE LA ORDEN
        # ==================================================

        tiene_origen = any(
            (
                self.proyecto_id,
                self.servicio_contratado_id,
                self.presupuesto_telecom_id,
            )
        )

        if not tiene_origen:
            mensaje = _(
                "La orden de trabajo debe estar relacionada "
                "con un proyecto, un servicio contratado "
                "o un presupuesto Telecom."
            )

            errores["proyecto"] = mensaje
            errores["servicio_contratado"] = mensaje
            errores["presupuesto_telecom"] = mensaje

        # ==================================================
        # RECEPCIÓN E INICIO
        # ==================================================

        if (
            self.fecha_inicio
            and self.fecha_recepcion_solicitud
            and self.fecha_inicio < self.fecha_recepcion_solicitud
        ):
            errores["fecha_inicio"] = _(
                "La fecha de inicio no puede ser anterior "
                "a la recepción de la solicitud."
            )

        if (
            self.fecha_inicio
            and self.fecha_programada
            and self.fecha_inicio < self.fecha_programada
        ):
            errores["fecha_inicio"] = _(
                "La fecha de inicio no puede ser anterior "
                "a la fecha programada."
            )

        # ==================================================
        # FINALIZACIÓN
        # ==================================================

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

        # ==================================================
        # ENVÍO AL CLIENTE
        # ==================================================

        if (
            self.fecha_envio_cliente
            and not self.fecha_finalizacion
        ):
            errores["fecha_envio_cliente"] = _(
                "Debe finalizar la orden antes "
                "de enviarla al cliente."
            )

        if (
            self.fecha_finalizacion
            and self.fecha_envio_cliente
            and self.fecha_envio_cliente < self.fecha_finalizacion
        ):
            errores["fecha_envio_cliente"] = _(
                "La fecha de envío al cliente no puede ser anterior "
                "a la finalización de la orden."
            )

        # ==================================================
        # ACEPTACIÓN
        # ==================================================

        if (
            self.fecha_aceptacion
            and not self.fecha_envio_cliente
        ):
            errores["fecha_aceptacion"] = _(
                "Debe registrar el envío al cliente antes "
                "de registrar su aceptación."
            )

        if (
            self.fecha_envio_cliente
            and self.fecha_aceptacion
            and self.fecha_aceptacion < self.fecha_envio_cliente
        ):
            errores["fecha_aceptacion"] = _(
                "La fecha de aceptación no puede ser anterior "
                "a la fecha de envío al cliente."
            )

        # ==================================================
        # FACTURACIÓN
        # ==================================================

        if (
            self.fecha_facturacion
            and not self.fecha_finalizacion
        ):
            errores["fecha_facturacion"] = _(
                "Debe finalizar la orden antes "
                "de registrar su facturación."
            )

        if (
            self.fecha_finalizacion
            and self.fecha_facturacion
            and self.fecha_facturacion < self.fecha_finalizacion
        ):
            errores["fecha_facturacion"] = _(
                "La fecha de facturación no puede ser anterior "
                "a la finalización de la orden."
            )

        # ==================================================
        # COBRO
        # ==================================================

        if (
            self.fecha_cobro
            and not self.fecha_facturacion
        ):
            errores["fecha_cobro"] = _(
                "Debe registrar la facturación antes "
                "de registrar el cobro."
            )

        if (
            self.fecha_facturacion
            and self.fecha_cobro
            and self.fecha_cobro < self.fecha_facturacion
        ):
            errores["fecha_cobro"] = _(
                "La fecha de cobro no puede ser anterior "
                "a la fecha de facturación."
            )

        if errores:
            raise ValidationError(errores)

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
        Indica si la orden de trabajo generó una instalación.

        La instalación se obtiene mediante la relación inversa
        del OneToOneField definido en Instalacion.
        """

        try:
            self.instalacion
        except ObjectDoesNotExist:
            return False

        return True

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

    @property
    def tiene_proyecto(self):
        """
        Indica si la orden proviene de un proyecto.
        """

        return self.proyecto_id is not None


    @property
    def tiene_servicio_contratado(self):
        """
        Indica si la orden está relacionada
        con un servicio contratado.
        """

        return self.servicio_contratado_id is not None


    @property
    def tiene_presupuesto_telecom(self):
        """
        Indica si la orden proviene
        de un presupuesto Telecom.
        """

        return self.presupuesto_telecom_id is not None


    @property
    def origen_principal(self):
        """
        Devuelve el origen principal de la orden.
        """

        if self.proyecto_id:
            return self.proyecto

        if self.servicio_contratado_id:
            return self.servicio_contratado

        if self.presupuesto_telecom_id:
            return self.presupuesto_telecom

        return None