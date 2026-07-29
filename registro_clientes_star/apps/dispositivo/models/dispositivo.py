from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    DEVICE_CODE_PREFIX,
    MAX_NAME_LENGTH,
)

from apps.common.choices import (
    EstadoDispositivoChoices,
    EstadoAprobacionChoices,
)

from apps.servicio.models.servicio_contratado import ServicioContratado

from .modelo_dispositivo import ModeloDispositivo


class Dispositivo(CodeModel):
    """
    Representa un equipo físico instalado dentro
    de un servicio contratado.
    """

    CODE_PREFIX = DEVICE_CODE_PREFIX


    # ======================================================
    # RELACIONES
    # ======================================================

    servicio_contratado = models.ForeignKey(
        ServicioContratado,
        on_delete=models.PROTECT,
        related_name="dispositivos",
        verbose_name=_("Servicio contratado"),
    )

    modelo = models.ForeignKey(
        ModeloDispositivo,
        on_delete=models.PROTECT,
        related_name="dispositivos",
        verbose_name=_("Modelo"),
    )


    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    numero_serie = models.CharField(
        max_length=MAX_NAME_LENGTH,
        unique=True,
        verbose_name=_("Número de serie"),
    )

    codigo_interno = models.CharField(
        max_length=MAX_NAME_LENGTH,
        blank=True,
        verbose_name=_("Código interno"),
    )


    # ======================================================
    # INSTALACIÓN
    # ======================================================

    fecha_instalacion = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de instalación"),
    )

    fecha_retiro = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de retiro"),
    )

    ubicacion = models.CharField(
        max_length=MAX_NAME_LENGTH,
        blank=True,
        verbose_name=_("Ubicación"),
    )


    # ======================================================
    # ESTADO
    # ======================================================

    estado = models.CharField(
        max_length=20,
        choices=EstadoDispositivoChoices.choices,
        default=EstadoDispositivoChoices.ACTIVO,
        verbose_name=_("Estado"),
    )


    # ======================================================
    # OBSERVACIONES
    # ======================================================

    observaciones = models.TextField(
        blank=True,
        verbose_name=_("Observaciones"),
    )


    # ======================================================
    # APROBACIÓN
    # ======================================================

    estado_aprobacion = models.CharField(
        max_length=20,
        choices=EstadoAprobacionChoices.choices,
        default=EstadoAprobacionChoices.PENDIENTE,
        editable=False,
        verbose_name=_("Estado de aprobación"),
        help_text=_(
            "Todo alta o modificación queda pendiente "
            "de aprobación hasta ser revisada."
        ),
    )

    aprobado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="dispositivos_aprobados",
        blank=True,
        null=True,
        editable=False,
        verbose_name=_("Aprobado/rechazado por"),
    )

    fecha_aprobacion = models.DateTimeField(
        blank=True,
        null=True,
        editable=False,
        verbose_name=_("Fecha de aprobación/rechazo"),
    )

    motivo_rechazo = models.TextField(
        blank=True,
        editable=False,
        verbose_name=_("Motivo de rechazo"),
    )


    class Meta:
        verbose_name = _("Dispositivo")
        verbose_name_plural = _("Dispositivos")

        ordering = (
            "modelo",
            "numero_serie",
        )


    def __str__(self):
        return f"{self.modelo} - {self.numero_serie}"


    # ======================================================
    # PERSISTENCIA
    # ======================================================

    _aprobando = False

    def save(self, *args, **kwargs):
        """
        Cualquier alta o modificación queda pendiente de
        aprobación, salvo que el guardado provenga de
        aprobar() o rechazar().
        """

        if not self._aprobando:
            self.estado_aprobacion = (
                EstadoAprobacionChoices.PENDIENTE
            )
            self.aprobado_por = None
            self.fecha_aprobacion = None
            self.motivo_rechazo = ""

        super().save(*args, **kwargs)


    # ======================================================
    # MÉTODOS DE NEGOCIO
    # ======================================================

    def aprobar(self, usuario, commit: bool = True):
        """
        Aprueba el dispositivo. Solo debe invocarse si
        `usuario` es staff.
        """

        self.estado_aprobacion = EstadoAprobacionChoices.APROBADO
        self.aprobado_por = usuario
        self.fecha_aprobacion = timezone.now()
        self.motivo_rechazo = ""

        if commit:
            self._aprobando = True
            self.save(
                update_fields=[
                    "estado_aprobacion",
                    "aprobado_por",
                    "fecha_aprobacion",
                    "motivo_rechazo",
                ]
            )
            self._aprobando = False

    def rechazar(self, usuario, motivo: str = "", commit: bool = True):
        """
        Rechaza el dispositivo. Solo debe invocarse si
        `usuario` es staff.
        """

        self.estado_aprobacion = EstadoAprobacionChoices.RECHAZADO
        self.aprobado_por = usuario
        self.fecha_aprobacion = timezone.now()
        self.motivo_rechazo = motivo

        if commit:
            self._aprobando = True
            self.save(
                update_fields=[
                    "estado_aprobacion",
                    "aprobado_por",
                    "fecha_aprobacion",
                    "motivo_rechazo",
                ]
            )
            self._aprobando = False

    @property
    def esta_aprobado(self) -> bool:
        return self.estado_aprobacion == EstadoAprobacionChoices.APROBADO