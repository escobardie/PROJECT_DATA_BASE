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

from apps.servicio.models import ServicioContratado
#from apps.orden_trabajo.models import OrdenTrabajo


class Instalacion(CodeModel):
    """
    Representa un trabajo técnico realizado sobre un servicio contratado.

    Una instalación agrupa los dispositivos instalados, los técnicos
    participantes y toda la información relacionada con el trabajo.

    No almacena información del cliente ni de la sucursal, ya que estos
    datos se obtienen a través del ServicioContratado.
    """

    CODE_PREFIX = INSTALLATION_CODE_PREFIX

    # ======================================================
    # RELACIONES
    # ======================================================

    servicio_contratado = models.ForeignKey(
        ServicioContratado,
        on_delete=models.PROTECT,
        related_name="instalaciones",
        blank=True,
        null=True,
        verbose_name=_("Servicio contratado"),
        help_text=_(
            "Servicio contratado al que pertenece la instalación."
        ),
    )
    # orden_trabajo = models.OneToOneField(
    #     OrdenTrabajo,
    #     on_delete=models.PROTECT,
    #     related_name="instalacion",
    #     blank=True,
    #     null=True,
    #     verbose_name=_("Orden de trabajo"),
    #     help_text=_("Orden de trabajo asociada a la instalación, si corresponde."),
    # )
    # ======================================================
    # PLANIFICACIÓN
    # ======================================================

    prioridad = models.CharField(
        max_length=20,
        choices=PrioridadInstalacionChoices.choices,
        default=PrioridadInstalacionChoices.NORMAL,
        db_index=True,
        verbose_name=_("Prioridad"),
        help_text=_("Prioridad de la instalación."),
    )

    fecha_programada = models.DateField(
        verbose_name=_("Fecha programada"),
        db_index=True,
        help_text=_("Fecha en la que se programó la instalación."),
    )

    duracion_estimada = models.DurationField(
        blank=True,
        null=True,
        verbose_name=_("Duración estimada"),
        help_text=_("Tiempo estimado para completar la instalación."),
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
        help_text=_("Estado actual de la instalación."),
    )

    fecha_inicio = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de inicio"),
        help_text=_("Fecha y hora en que se inició la instalación."),
    )

    fecha_finalizacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de finalización"),
        help_text=_("Fecha y hora en que se completó la instalación."),
    )

    # ======================================================
    # CONFORMIDAD
    # ======================================================

    recibido_por = models.CharField(
        max_length=MAX_NAME_LENGTH,
        blank=True,
        verbose_name=_("Recibido por"),
        help_text=_("Nombre de la persona que recibió la instalación."),
    )

    fecha_conformidad = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de conformidad"),
        help_text=_("Fecha y hora en que se confirmó la conformidad de la instalación."),
    )

    observaciones_conformidad = models.TextField(
        blank=True,
        verbose_name=_("Observaciones de conformidad"),
        help_text=_("Observaciones generales sobre la conformidad de la instalación."),
    )

    # ======================================================
    # OBSERVACIONES
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        verbose_name=_("Observaciones"),
        help_text=_("Observaciones generales sobre la instalación."),
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
                ]
            ),
        ]

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        if self.servicio_contratado:
            return (
                f"{self.codigo} - "
                f"{self.servicio_contratado}"
            )

        return self.codigo

    # ======================================================
    # PROPIEDADES
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
        Determina si una instalación programada se encuentra vencida.
        """

        return (
            self.fecha_programada < timezone.localdate()
            and not self.finalizada
            and not self.cancelada
        )

    @property
    def tiene_orden_trabajo(self):
        """
        Indica si la instalación fue creada desde una orden de trabajo.
        """

        return hasattr(
            self,
            "orden_trabajo",
        )


    @property
    def tiene_ordenes_relacionadas(self):
        """
        Indica si existen órdenes de trabajo relacionadas con esta instalación.
        """

        return (
            self.ordenes_trabajo_relacionadas.exists()
        )


    @property
    def cantidad_ordenes_relacionadas(self):
        """
        Devuelve la cantidad de órdenes relacionadas con esta instalación.
        """

        return (
            self.ordenes_trabajo_relacionadas.count()
        )