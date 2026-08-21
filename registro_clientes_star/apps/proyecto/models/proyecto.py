from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.choices import (
    EstadoProyectoChoices,
    MonedaChoices,
    PrioridadProyectoChoices,
    RespuestaClienteProyectoChoices,
)

from apps.common.constants import (
    MAX_NAME_LENGTH,
    MAX_PRICE_DIGITS,
    PRICE_DECIMAL_PLACES,
    PROJECT_CODE_PREFIX,
)

from apps.common.models import CodeModel

from apps.cuenta_cliente.models import Sucursal


class Proyecto(CodeModel):
    """
    Representa un trabajo comercial y operativo realizado
    para una sucursal.

    El proyecto concentra:

    - recepción de la solicitud;
    - planificación;
    - clasificación;
    - cotización;
    - envío al cliente;
    - respuesta del cliente;
    - aprobación;
    - ejecución;
    - cierre.

    Puede incluir dispositivos, materiales, servicios,
    mano de obra, licencias, viáticos y otros conceptos
    mediante sus detalles.

    A partir de un proyecto aprobado pueden generarse
    una o varias órdenes de trabajo.
    """

    CODE_PREFIX = PROJECT_CODE_PREFIX

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
    # CLASIFICACIÓN
    # ======================================================

    prioridad = models.CharField(
        max_length=20,
        choices=PrioridadProyectoChoices.choices,
        default=PrioridadProyectoChoices.NORMAL,
        db_index=True,
        verbose_name=_("Prioridad"),
        help_text=_(
            "Prioridad comercial u operativa del proyecto."
        ),
    )

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
    # CONDICIONES COMERCIALES
    # ======================================================

    moneda = models.CharField(
        max_length=3,
        choices=MonedaChoices.choices,
        default=MonedaChoices.ARS,
        verbose_name=_("Moneda"),
    )

    # ======================================================
    # RECEPCIÓN DE LA SOLICITUD
    # ======================================================

    fecha_recepcion_solicitud = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_(
            "Fecha de recepción de la solicitud"
        ),
        help_text=_(
            "Fecha y hora en que se recibió "
            "la solicitud del cliente."
        ),
    )

    usuario_recepcion_solicitud = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="proyectos_recepcionados",
        blank=True,
        null=True,
        verbose_name=_("Recepcionado por"),
        help_text=_(
            "Usuario que registró la recepción "
            "de la solicitud del cliente."
        ),
    )

    # ======================================================
    # PLANIFICACIÓN
    # ======================================================

    fecha_creacion = models.DateField(
        db_index=True,
        verbose_name=_("Fecha de creación"),
        help_text=_(
            "Fecha comercial u operativa "
            "de creación del proyecto."
        ),
    )

    fecha_planificada = models.DateField(
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_("Fecha planificada"),
        help_text=_(
            "Fecha prevista para comenzar "
            "la ejecución del proyecto."
        ),
    )

    # ======================================================
    # ENVÍO AL CLIENTE
    # ======================================================

    fecha_envio_cliente = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_("Fecha de envío al cliente"),
        help_text=_(
            "Fecha y hora en que el proyecto "
            "fue enviado al cliente."
        ),
    )

    usuario_envio_cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="proyectos_enviados_cliente",
        blank=True,
        null=True,
        verbose_name=_("Enviado por"),
        help_text=_(
            "Usuario que registró el envío "
            "del proyecto al cliente."
        ),
    )

    # ======================================================
    # RESPUESTA DEL CLIENTE
    # ======================================================

    respuesta_cliente = models.CharField(
        max_length=20,
        choices=RespuestaClienteProyectoChoices.choices,
        default=RespuestaClienteProyectoChoices.PENDIENTE,
        db_index=True,
        verbose_name=_("Respuesta del cliente"),
        help_text=_(
            "Indica si el cliente todavía no respondió, "
            "aceptó o rechazó el proyecto."
        ),
    )

    fecha_respuesta_cliente = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_("Fecha de respuesta del cliente"),
        help_text=_(
            "Fecha y hora en que el cliente "
            "respondió respecto del proyecto."
        ),
    )

    usuario_respuesta_cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="proyectos_respuestas_cliente",
        blank=True,
        null=True,
        verbose_name=_("Respuesta registrada por"),
        help_text=_(
            "Usuario que registró la respuesta "
            "del cliente."
        ),
    )

    # ======================================================
    # EJECUCIÓN
    # ======================================================

    fecha_inicio = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de inicio"),
        help_text=_(
            "Fecha real en que comenzó "
            "la ejecución del proyecto."
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
            "Suma de los subtotales "
            "de los detalles del proyecto."
        ),
    )

    descuento_total = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=Decimal("0.00"),
        editable=False,
        verbose_name=_("Descuento total"),
        help_text=_(
            "Suma de los descuentos aplicados "
            "a los detalles."
        ),
    )

    impuestos = models.DecimalField(
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        default=Decimal("0.00"),
        editable=False,
        verbose_name=_("Impuestos"),
        help_text=_(
            "Suma de los impuestos aplicados "
            "a los detalles."
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
                    "prioridad",
                ],
                name="idx_proy_prioridad",
            ),
            models.Index(
                fields=[
                    "respuesta_cliente",
                ],
                name="idx_proy_resp_cli",
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
                    "fecha_recepcion_solicitud",
                ],
                name="idx_proy_fec_recep",
            ),
            models.Index(
                fields=[
                    "fecha_envio_cliente",
                ],
                name="idx_proy_fec_envio",
            ),
            models.Index(
                fields=[
                    "fecha_respuesta_cliente",
                ],
                name="idx_proy_fec_resp",
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
        Valida la coherencia temporal, comercial
        y operativa del proyecto.

        El proyecto puede permanecer en BORRADOR
        sin recepción, planificación, envío ni respuesta.

        Las fechas de los hitos pueden cargarse previamente
        antes de confirmar cada operación mediante los
        services correspondientes.
        """

        super().clean()

        errores = {}

        # ==================================================
        # FECHA DE CREACIÓN
        # ==================================================

        # fecha_creacion es obligatoria por definición
        # del modelo, por lo que Django valida su presencia.

        # ==================================================
        # RECEPCIÓN DE LA SOLICITUD
        # ==================================================

        # La recepción es opcional mientras el proyecto
        # permanece en borrador.
        #
        # No se exige:
        #
        # - fecha_recepcion_solicitud
        # - usuario_recepcion_solicitud
        #
        # hasta que el hito sea registrado mediante service.

        # ==================================================
        # PLANIFICACIÓN
        # ==================================================

        if (
            self.fecha_planificada
            and self.fecha_planificada < self.fecha_creacion
        ):
            errores["fecha_planificada"] = _(
                "La fecha planificada no puede ser anterior "
                "a la fecha de creación."
            )

        # Si existe una recepción, una planificación
        # no debería ser anterior a esa recepción.
        #
        # fecha_planificada es DateField y
        # fecha_recepcion_solicitud es DateTimeField,
        # por lo que comparamos solamente las fechas.

        if (
            self.fecha_planificada
            and self.fecha_recepcion_solicitud
            and self.fecha_planificada
            < self.fecha_recepcion_solicitud.date()
        ):
            errores["fecha_planificada"] = _(
                "La fecha planificada no puede ser anterior "
                "a la fecha de recepción de la solicitud."
            )

        # ==================================================
        # ENVÍO AL CLIENTE
        # ==================================================

        # La fecha de envío puede permanecer vacía mientras
        # el proyecto todavía no haya sido enviado.

        # Si existe fecha de envío y también existe recepción,
        # el envío no puede ser anterior a la recepción.

        if (
            self.fecha_envio_cliente
            and self.fecha_recepcion_solicitud
            and self.fecha_envio_cliente
            < self.fecha_recepcion_solicitud
        ):
            errores["fecha_envio_cliente"] = _(
                "La fecha de envío al cliente no puede ser "
                "anterior a la fecha de recepción "
                "de la solicitud."
            )

        # Si existe planificación, el envío no debería ser
        # anterior a la fecha planificada.
        #
        # Comparamos solamente las fechas porque
        # fecha_planificada es DateField.

        if (
            self.fecha_envio_cliente
            and self.fecha_planificada
            and self.fecha_envio_cliente.date()
            < self.fecha_planificada
        ):
            errores["fecha_envio_cliente"] = _(
                "La fecha de envío al cliente no puede ser "
                "anterior a la fecha planificada."
            )

        # ==================================================
        # RESPUESTA DEL CLIENTE
        # ==================================================

        hay_respuesta_cliente = (
            self.respuesta_cliente
            != RespuestaClienteProyectoChoices.PENDIENTE
        )

        # --------------------------------------------------
        # Respuesta definitiva sin envío
        # --------------------------------------------------

        # Si el cliente ya aceptó o rechazó,
        # necesariamente debe existir fecha de envío.

        if (
            hay_respuesta_cliente
            and not self.fecha_envio_cliente
        ):
            errores["fecha_envio_cliente"] = _(
                "Debe registrar el envío al cliente "
                "antes de registrar su respuesta."
            )

        # --------------------------------------------------
        # Respuesta definitiva sin fecha
        # --------------------------------------------------

        # Una aceptación o rechazo definitivo debe
        # disponer de fecha de respuesta.

        if (
            hay_respuesta_cliente
            and not self.fecha_respuesta_cliente
        ):
            errores["fecha_respuesta_cliente"] = _(
                "Debe indicar la fecha en que "
                "el cliente respondió el proyecto."
            )

        # --------------------------------------------------
        # Fecha de respuesta precargada sin envío
        # --------------------------------------------------

        # Se permite precargar fecha de respuesta mientras
        # la respuesta continúe PENDIENTE.
        #
        # Pero, si existe fecha de respuesta, debe existir
        # al menos una fecha de envío previa.

        if (
            self.fecha_respuesta_cliente
            and not self.fecha_envio_cliente
        ):
            errores["fecha_respuesta_cliente"] = _(
                "No puede registrar una fecha de respuesta "
                "sin haber registrado previamente "
                "el envío al cliente."
            )

        # --------------------------------------------------
        # Cronología envío → respuesta
        # --------------------------------------------------

        if (
            self.fecha_envio_cliente
            and self.fecha_respuesta_cliente
            and self.fecha_respuesta_cliente
            < self.fecha_envio_cliente
        ):
            errores["fecha_respuesta_cliente"] = _(
                "La fecha de respuesta del cliente "
                "no puede ser anterior a la fecha de envío."
            )

        # IMPORTANTE:
        #
        # No validamos:
        #
        # respuesta_cliente == PENDIENTE
        # + fecha_respuesta_cliente existente
        #
        # como error.
        #
        # Esto es intencional porque la fecha puede
        # precargarse antes de presionar Aceptar/Rechazar.

        # ==================================================
        # INICIO DE EJECUCIÓN
        # ==================================================

        if (
            self.fecha_inicio
            and self.fecha_inicio < self.fecha_creacion
        ):
            errores["fecha_inicio"] = _(
                "La fecha de inicio no puede ser anterior "
                "a la fecha de creación."
            )

        if (
            self.fecha_inicio
            and self.fecha_planificada
            and self.fecha_inicio < self.fecha_planificada
        ):
            errores["fecha_inicio"] = _(
                "La fecha de inicio no puede ser anterior "
                "a la fecha planificada."
            )

        # Si el proyecto tiene una respuesta aceptada,
        # la ejecución no debería comenzar antes
        # de la respuesta del cliente.

        if (
            self.fecha_inicio
            and self.fecha_respuesta_cliente
            and self.fecha_inicio
            < self.fecha_respuesta_cliente.date()
        ):
            errores["fecha_inicio"] = _(
                "La fecha de inicio no puede ser anterior "
                "a la fecha de respuesta del cliente."
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
        # ERRORES
        # ==================================================

        if errores:
            raise ValidationError(
                errores
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
    # PROPIEDADES GENERALES
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

    # ======================================================
    # PROPIEDADES DE TRAZABILIDAD
    # ======================================================

    @property
    def solicitud_recepcionada(self):
        """
        Indica si el hito de recepción de la solicitud
        fue formalmente registrado.
        """

        return bool(
            self.fecha_recepcion_solicitud
            and self.usuario_recepcion_solicitud_id
        )

    @property
    def fue_enviado_cliente(self):
        """
        Indica si el proyecto ya fue enviado al cliente.
        """

        return (
            self.fecha_envio_cliente
            is not None
        )

    @property
    def respuesta_pendiente(self):
        return (
            self.respuesta_cliente
            == RespuestaClienteProyectoChoices.PENDIENTE
        )

    @property
    def aceptado_cliente(self):
        """
        Indica si el cliente aceptó el proyecto.
        """

        return (
            self.respuesta_cliente
            == RespuestaClienteProyectoChoices.ACEPTADO
        )

    @property
    def rechazado_cliente(self):
        """
        Indica si el cliente rechazó el proyecto.
        """

        return (
            self.respuesta_cliente
            == RespuestaClienteProyectoChoices.RECHAZADO
        )

    # ======================================================
    # PROPIEDADES DE ESTADO
    # ======================================================

    @property
    def borrador(self):
        return (
            self.estado
            == EstadoProyectoChoices.BORRADOR
        )

    @property
    def pendiente_aprobacion(self):
        return (
            self.estado
            == EstadoProyectoChoices.PENDIENTE_APROBACION
        )

    @property
    def aprobado(self):
        return (
            self.estado
            == EstadoProyectoChoices.APROBADO
        )

    @property
    def planificado(self):
        return (
            self.estado
            == EstadoProyectoChoices.PLANIFICADO
        )

    @property
    def en_ejecucion(self):
        return (
            self.estado
            == EstadoProyectoChoices.EN_EJECUCION
        )

    @property
    def finalizado(self):
        return (
            self.estado
            == EstadoProyectoChoices.FINALIZADO
        )

    @property
    def cancelado(self):
        return (
            self.estado
            == EstadoProyectoChoices.CANCELADO
        )