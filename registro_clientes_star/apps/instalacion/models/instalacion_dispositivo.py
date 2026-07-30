from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import CodeModel
from apps.common.constants import (
    INSTALLATION_DEVICE_CODE_PREFIX,
    MAX_SERIAL_LENGTH,
    MAX_MAC_LENGTH,
    MAX_LOCATION_LENGTH,
    MAX_ACCESS_USERNAME_LENGTH,
    MAX_ACCESS_PASSWORD_LENGTH,
)

from apps.common.choices import (
    EstadoDispositivoInstaladoChoices,
)

from apps.dispositivo.models import Dispositivo

from .instalacion import Instalacion


class InstalacionDispositivo(CodeModel):
    """
    Representa un dispositivo físico instalado
    dentro de una instalación.

    Relaciona un producto del catálogo con una instalación real.

    Ejemplo:

    Dispositivo:
        Cámara Hikvision DS-2CD2043G2-I

    Instalación:
        Cliente Juan Pérez - Sucursal Centro

    Datos propios:
        Serie
        IP
        MAC
        Ubicación
        Estado
    """

    CODE_PREFIX = INSTALLATION_DEVICE_CODE_PREFIX

    # ======================================================
    # RELACIONES
    # ======================================================

    instalacion = models.ForeignKey(
        Instalacion,
        on_delete=models.CASCADE,
        related_name="dispositivos",
        verbose_name=_("Instalación"),
    )

    dispositivo = models.ForeignKey(
        Dispositivo,
        on_delete=models.PROTECT,
        related_name="instalaciones",
        verbose_name=_("Dispositivo"),
    )

    # ======================================================
    # INFORMACIÓN DEL EQUIPO
    # ======================================================

    cantidad = models.PositiveIntegerField(
        default=1,
        validators=[
            MinValueValidator(1),
        ],
        verbose_name=_("Cantidad"),
        help_text=_(
            "Cantidad instalada del dispositivo."
        ),
    )

    numero_serie = models.CharField(
        max_length=MAX_SERIAL_LENGTH,
        blank=True,
        default="",
        verbose_name=_("Número de serie"),
        help_text=_(
            "Identificador único del equipo físico."
        ),
    )

    # ======================================================
    # CONFIGURACIÓN DE RED
    # ======================================================

    direccion_mac = models.CharField(
        max_length=MAX_MAC_LENGTH,
        blank=True,
        default="",
        verbose_name=_("Dirección MAC"),
    )

    direccion_ip = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name=_("Dirección IP"),
    )

    # ======================================================
    # CREDENCIALES
    # ======================================================

    usuario_acceso = models.CharField(
        max_length=MAX_ACCESS_USERNAME_LENGTH,
        blank=True,
        default="",
        verbose_name=_("Usuario de acceso"),
    )

    contrasena_acceso = models.CharField(
        max_length=MAX_ACCESS_PASSWORD_LENGTH,
        blank=True,
        default="",
        verbose_name=_("Contraseña de acceso"),
    )

    # ======================================================
    # UBICACIÓN
    # ======================================================

    ubicacion = models.CharField(
        max_length=MAX_LOCATION_LENGTH,
        blank=True,
        default="",
        verbose_name=_("Ubicación"),
    )

    # ======================================================
    # ESTADO
    # ======================================================

    estado = models.CharField(
        max_length=20,
        choices=EstadoDispositivoInstaladoChoices.choices,
        default=EstadoDispositivoInstaladoChoices.INSTALADO,
        db_index=True,
        verbose_name=_("Estado"),
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
    # META
    # ======================================================

    class Meta:
        verbose_name = _("Dispositivo instalado")
        verbose_name_plural = _("Dispositivos instalados")

        ordering = (
            "ubicacion",
            "codigo",
        )

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "numero_serie",
                ],
                condition=~models.Q(
                    numero_serie=""
                ),
                name=(
                    "unique_instalacion_dispositivo_serie"
                ),
            ),

        ]

        indexes = [

            models.Index(
                fields=[
                    "instalacion",
                    "estado",
                ],
                name=(
                    "idx_inst_disp_inst_estado"
                ),
            ),

            models.Index(
                fields=[
                    "estado",
                ],
                name=(
                    "idx_inst_disp_estado"
                ),
            ),

            models.Index(
                fields=[
                    "ubicacion",
                ],
                name=(
                    "idx_inst_disp_ubicacion"
                ),
            ),

            models.Index(
                fields=[
                    "numero_serie",
                ],
                name=(
                    "idx_inst_disp_serie"
                ),
            ),

        ]

    # ======================================================
    # VALIDACIONES
    # ======================================================

    def clean(self):
        """
        Validaciones de reglas de negocio.
        """

        super().clean()

        # ----------------------------------------------
        # Serie única cuando existe
        # ----------------------------------------------

        if self.numero_serie:

            existe = (
                InstalacionDispositivo.objects
                .filter(
                    numero_serie=self.numero_serie,
                )
                .exclude(
                    pk=self.pk,
                )
                .exists()
            )

            if existe:
                raise ValidationError(
                    {
                        "numero_serie": _(
                            "Ya existe un dispositivo "
                            "con este número de serie."
                        )
                    }
                )

        # ----------------------------------------------
        # Una serie por equipo físico
        # ----------------------------------------------

        if (
            self.cantidad > 1
            and self.numero_serie
        ):
            raise ValidationError(
                {
                    "numero_serie": _(
                        "No se puede asignar un único "
                        "número de serie cuando la cantidad "
                        "instalada es mayor a 1."
                    )
                }
            )

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):

        if self.numero_serie:
            return (
                f"{self.dispositivo} "
                f"({self.numero_serie})"
            )

        return str(self.dispositivo)

    # ======================================================
    # PROPIEDADES
    # ======================================================

    @property
    def tiene_ip(self):
        return bool(self.direccion_ip)

    @property
    def tiene_mac(self):
        return bool(self.direccion_mac)

    @property
    def activo(self):
        return (
            self.estado
            == EstadoDispositivoInstaladoChoices.INSTALADO
        )