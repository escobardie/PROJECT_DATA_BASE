from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel

from apps.common.constants import (
    INSTALLATION_CODE_PREFIX,
    MAX_NAME_LENGTH,
)

from apps.common.choices import (
    EstadoInstalacionChoices,
    PrioridadInstalacionChoices,
)


class Instalacion(CodeModel):
    """
    Representa el resultado técnico de una orden de trabajo.

    Una instalación documenta los equipos físicos instalados,
    los técnicos participantes, la ejecución del trabajo
    y la conformidad del cliente.

    El proyecto, la sucursal, el servicio contratado y otros
    datos de origen se obtienen mediante la orden de trabajo.
    """

    CODE_PREFIX = INSTALLATION_CODE_PREFIX

    # ======================================================
    # RELACIONES
    # ======================================================

    orden_trabajo = models.OneToOneField(
        "orden_trabajo.OrdenTrabajo",
        on_delete=models.PROTECT,
        related_name="instalacion",
        verbose_name=_("Orden de trabajo"),
        help_text=_(
            "Orden de trabajo que dio origen a esta instalación."
        ),
    )

    # ======================================================
    # PLANIFICACIÓN
    # ======================================================

    prioridad = models.CharField(
        max_length=20,
        choices=PrioridadInstalacionChoices.choices,
        default=PrioridadInstalacionChoices.NORMAL,
        db_index=True,
        verbose_name=_("Prioridad"),
        help_text=_(
            "Prioridad operativa de la instalación."
        ),
    )

    fecha_programada = models.DateField(
        db_index=True,
        verbose_name=_("Fecha programada"),
        help_text=_(
            "Fecha prevista para ejecutar la instalación."
        ),
    )

    duracion_estimada = models.DurationField(
        blank=True,
        null=True,
        verbose_name=_("Duración estimada"),
        help_text=_(
            "Tiempo estimado para completar la instalación."
        ),
    )

    # ======================================================
    # EJECUCIÓN
    # ======================================================

    estado = models.CharField(
        max_length=20,
        choices=EstadoInstalacionChoices.choices,
        default=EstadoInstalacionChoices.PENDIENTE,
        db_index=True,
        verbose_name=_("Estado"),
        help_text=_(
            "Estado actual de la instalación."
        ),
    )

    fecha_inicio = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de inicio"),
        help_text=_(
            "Fecha y hora reales de inicio de la instalación."
        ),
    )

    fecha_finalizacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de finalización"),
        help_text=_(
            "Fecha y hora reales de finalización de la instalación."
        ),
    )

    # ======================================================
    # CONFORMIDAD
    # ======================================================

    recibido_por = models.CharField(
        max_length=MAX_NAME_LENGTH,
        blank=True,
        default="",
        verbose_name=_("Recibido por"),
        help_text=_(
            "Nombre de la persona que recibió la instalación."
        ),
    )

    fecha_conformidad = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de conformidad"),
        help_text=_(
            "Fecha y hora en que se registró la conformidad."
        ),
    )

    observaciones_conformidad = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Observaciones de conformidad"),
        help_text=_(
            "Observaciones relacionadas con la recepción "
            "y conformidad de la instalación."
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
            "Observaciones generales sobre la instalación."
        ),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:
        verbose_name = _("Instalación")
        verbose_name_plural = _("Instalaciones")

        ordering = (
            "prioridad",
            "fecha_programada",
            "-created_at",
        )

        indexes = [
            models.Index(
                fields=[
                    "estado",
                    "fecha_programada",
                ],
                name="idx_inst_estado_fecha",
            ),
        ]

    # ======================================================
    # VALIDACIONES
    # ======================================================

    def clean(self):
        """
        Valida la coherencia temporal de la instalación.
        """

        super().clean()

        errores = {}

        if (
            self.fecha_inicio
            and self.fecha_inicio.date() < self.fecha_programada
        ):
            errores["fecha_inicio"] = _(
                "La fecha de inicio no puede ser anterior "
                "a la fecha programada."
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

        if (
            self.fecha_conformidad
            and not self.fecha_finalizacion
        ):
            errores["fecha_conformidad"] = _(
                "Debe finalizar la instalación antes "
                "de registrar la conformidad."
            )

        if (
            self.fecha_finalizacion
            and self.fecha_conformidad
            and self.fecha_conformidad < self.fecha_finalizacion
        ):
            errores["fecha_conformidad"] = _(
                "La fecha de conformidad no puede ser anterior "
                "a la finalización de la instalación."
            )

        if errores:
            raise ValidationError(errores)

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return (
            f"{self.codigo} - "
            f"{self.orden_trabajo.codigo}"
        )

    # ======================================================
    # PROPIEDADES DE ORIGEN
    # ======================================================

    @property
    def proyecto(self):
        """
        Devuelve el proyecto asociado a la orden,
        si corresponde.
        """

        return self.orden_trabajo.proyecto

    @property
    def sucursal(self):
        """
        Devuelve la sucursal asociada a la orden,
        si corresponde.
        """

        return self.orden_trabajo.sucursal

    @property
    def servicio_contratado(self):
        """
        Devuelve el servicio contratado asociado a la orden,
        si corresponde.
        """

        return self.orden_trabajo.servicio_contratado

    @property
    def presupuesto_telecom(self):
        """
        Devuelve el presupuesto Telecom asociado a la orden,
        si corresponde.
        """

        return self.orden_trabajo.presupuesto_telecom

    # ======================================================
    # PROPIEDADES DE ESTADO
    # ======================================================

    @property
    def esta_pendiente(self):
        return (
            self.estado
            == EstadoInstalacionChoices.PENDIENTE
        )

    @property
    def esta_programada(self):
        return (
            self.estado
            == EstadoInstalacionChoices.PROGRAMADA
        )

    @property
    def en_proceso(self):
        return (
            self.estado
            == EstadoInstalacionChoices.EN_PROCESO
        )

    @property
    def finalizada(self):
        return (
            self.estado
            == EstadoInstalacionChoices.FINALIZADA
        )

    @property
    def cancelada(self):
        return (
            self.estado
            == EstadoInstalacionChoices.CANCELADA
        )

    @property
    def esta_vencida(self):
        """
        Indica si la fecha programada ya pasó y la instalación
        aún no fue finalizada ni cancelada.
        """

        return (
            self.fecha_programada < timezone.localdate()
            and not self.finalizada
            and not self.cancelada
        )

    # ======================================================
    # PROPIEDADES RELACIONADAS
    # ======================================================

    @property
    def tiene_ordenes_relacionadas(self):
        """
        Indica si existen otras órdenes ejecutadas
        sobre esta instalación.
        """

        return self.ordenes_trabajo_relacionadas.exists()

    @property
    def cantidad_ordenes_relacionadas(self):
        """
        Devuelve la cantidad de órdenes ejecutadas
        sobre esta instalación.
        """

        return self.ordenes_trabajo_relacionadas.count()