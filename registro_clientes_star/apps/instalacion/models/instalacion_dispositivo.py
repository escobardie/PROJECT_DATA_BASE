from django.core.validators import RegexValidator
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


# ======================================================
# VALIDADORES
# ======================================================

mac_address_validator = RegexValidator(
    regex=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",
    message=_(
        "Ingrese una dirección MAC válida. "
        "Ejemplo: AA:BB:CC:DD:EE:FF."
    ),
)


class InstalacionDispositivo(CodeModel):
    """
    Representa un dispositivo físico individual instalado.

    Cada registro corresponde a una única unidad física y puede
    almacenar información propia como número de serie, dirección
    MAC, dirección IP, ubicación, credenciales y estado.

    El producto comercial asociado se obtiene desde el catálogo
    mediante la relación con Dispositivo.
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
        help_text=_(
            "Instalación a la que pertenece el equipo físico."
        ),
    )

    dispositivo = models.ForeignKey(
        Dispositivo,
        on_delete=models.PROTECT,
        related_name="dispositivos_instalados",
        verbose_name=_("Dispositivo"),
        help_text=_(
            "Producto del catálogo correspondiente al equipo físico."
        ),
    )

    # ======================================================
    # IDENTIFICACIÓN DEL EQUIPO
    # ======================================================

    numero_serie = models.CharField(
        max_length=MAX_SERIAL_LENGTH,
        blank=True,
        null=True,
        unique=True,
        verbose_name=_("Número de serie"),
        help_text=_(
            "Número de serie único del equipo físico."
        ),
    )

    # ======================================================
    # CONFIGURACIÓN DE RED
    # ======================================================

    direccion_mac = models.CharField(
        max_length=MAX_MAC_LENGTH,
        blank=True,
        null=True,
        unique=True,
        validators=[
            mac_address_validator,
        ],
        verbose_name=_("Dirección MAC"),
        help_text=_(
            "Dirección MAC única del equipo. "
            "Ejemplo: AA:BB:CC:DD:EE:FF."
        ),
    )

    direccion_ip = models.GenericIPAddressField(
        blank=True,
        null=True,
        protocol="both",
        unpack_ipv4=True,
        verbose_name=_("Dirección IP"),
        help_text=_(
            "Dirección IPv4 o IPv6 asignada al dispositivo."
        ),
    )

    # ======================================================
    # CREDENCIALES
    # ======================================================

    usuario_acceso = models.CharField(
        max_length=MAX_ACCESS_USERNAME_LENGTH,
        blank=True,
        default="",
        verbose_name=_("Usuario de acceso"),
        help_text=_(
            "Nombre de usuario utilizado para acceder al dispositivo."
        ),
    )

    contrasena_acceso = models.CharField(
        max_length=MAX_ACCESS_PASSWORD_LENGTH,
        blank=True,
        default="",
        verbose_name=_("Contraseña de acceso"),
        help_text=_(
            "Contraseña utilizada para acceder al dispositivo."
        ),
    )

    # ======================================================
    # UBICACIÓN
    # ======================================================

    ubicacion = models.CharField(
        max_length=MAX_LOCATION_LENGTH,
        blank=True,
        default="",
        verbose_name=_("Ubicación"),
        help_text=_(
            "Ubicación física del dispositivo dentro de la instalación."
        ),
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
        help_text=_(
            "Estado actual del equipo físico instalado."
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
            "Observaciones técnicas sobre el dispositivo instalado."
        ),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:
        verbose_name = _("Dispositivo instalado")
        verbose_name_plural = _("Dispositivos instalados")

        ordering = (
            "ubicacion",
            "codigo",
        )

        indexes = [
            models.Index(
                fields=[
                    "instalacion",
                    "estado",
                ],
                name="idx_inst_disp_inst_estado",
            ),
            models.Index(
                fields=[
                    "instalacion",
                    "ubicacion",
                ],
                name="idx_inst_disp_inst_ubic",
            ),
        ]

    # ======================================================
    # NORMALIZACIÓN
    # ======================================================

    def normalizar_identificadores(self):
        """
        Normaliza el número de serie y la dirección MAC
        antes de validar y guardar el registro.
        """

        if self.numero_serie:
            self.numero_serie = (
                self.numero_serie
                .strip()
                .upper()
            )

        if self.direccion_mac:
            self.direccion_mac = (
                self.direccion_mac
                .strip()
                .upper()
                .replace("-", ":")
            )

    # ======================================================
    # VALIDACIONES
    # ======================================================

    def clean(self):
        """
        Ejecuta las validaciones del dispositivo instalado.
        """

        super().clean()

        self.normalizar_identificadores()

    # ======================================================
    # SAVE
    # ======================================================

    def save(self, *args, **kwargs):
        """
        Guarda el dispositivo normalizando previamente
        sus identificadores.
        """

        self.normalizar_identificadores()

        super().save(*args, **kwargs)

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        if self.numero_serie:
            return (
                f"{self.dispositivo} "
                f"({self.numero_serie})"
            )

        return (
            f"{self.codigo} - "
            f"{self.dispositivo}"
        )

    # ======================================================
    # PROPIEDADES
    # ======================================================

    @property
    def tiene_numero_serie(self):
        """
        Indica si el equipo tiene número de serie registrado.
        """

        return bool(self.numero_serie)

    @property
    def tiene_ip(self):
        """
        Indica si el equipo tiene una dirección IP registrada.
        """

        return self.direccion_ip is not None

    @property
    def tiene_mac(self):
        """
        Indica si el equipo tiene una dirección MAC registrada.
        """

        return bool(self.direccion_mac)

    @property
    def tiene_credenciales(self):
        """
        Indica si se registraron usuario y contraseña de acceso.
        """

        return bool(
            self.usuario_acceso
            and self.contrasena_acceso
        )

    @property
    def activo(self):
        """
        Indica si el dispositivo permanece instalado y activo.
        """

        return (
            self.estado
            == EstadoDispositivoInstaladoChoices.INSTALADO
        )