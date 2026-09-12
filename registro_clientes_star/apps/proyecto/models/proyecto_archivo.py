from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel
from apps.usuarios.models import Usuario

from .proyecto import Proyecto


class ProyectoArchivo(BaseModel):
    """
    Representa un archivo asociado a un Proyecto.

    El documento puede almacenarse en:

    - almacenamiento local administrado por Django;
    - Google Drive.

    Los archivos forman parte del historial documental
    del Proyecto.

    Una vez registrados no deben modificarse ni eliminarse
    directamente desde el flujo funcional.

    Si un documento deja de ser válido debe retirarse
    lógicamente conservando toda su trazabilidad.
    """

    # ======================================================
    # ORIGEN DEL ARCHIVO
    # ======================================================

    class Origen(models.TextChoices):
        LOCAL = (
            "LOCAL",
            _("Archivo local"),
        )

        GOOGLE_DRIVE = (
            "GOOGLE_DRIVE",
            _("Google Drive"),
        )

    # ======================================================
    # RELACIONES
    # ======================================================

    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name="archivos",
        verbose_name=_("Proyecto"),
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="archivos_proyectos",
        editable=False,
        verbose_name=_("Cargado por"),
        help_text=_(
            "Usuario que registró formalmente "
            "el archivo en el proyecto."
        ),
    )

    # ======================================================
    # ORIGEN
    # ======================================================

    origen = models.CharField(
        max_length=20,
        choices=Origen.choices,
        default=Origen.LOCAL,
        db_index=True,
        verbose_name=_("Origen"),
        help_text=_(
            "Indica dónde se encuentra almacenado "
            "el documento."
        ),
    )

    # ======================================================
    # FECHA FUNCIONAL
    # ======================================================

    fecha_documento = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha del documento"),
        help_text=_(
            "Fecha y hora asociada al documento, "
            "fotografía o evidencia."
        ),
    )

    # ======================================================
    # ARCHIVO LOCAL
    # ======================================================

    archivo = models.FileField(
        upload_to="proyectos/%Y/%m/",
        blank=True,
        default="",
        verbose_name=_("Archivo local"),
        help_text=_(
            "Documento almacenado localmente "
            "por la aplicación."
        ),
    )

    # ======================================================
    # GOOGLE DRIVE
    # ======================================================

    drive_file_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
        editable=False,
        verbose_name=_("ID de Google Drive"),
        help_text=_(
            "Identificador único asignado por Google Drive."
        ),
    )

    drive_nombre = models.CharField(
        max_length=255,
        blank=True,
        default="",
        editable=False,
        verbose_name=_("Nombre en Google Drive"),
    )

    drive_mime_type = models.CharField(
        max_length=255,
        blank=True,
        default="",
        editable=False,
        verbose_name=_("Tipo MIME de Google Drive"),
    )

    drive_web_view_link = models.URLField(
        max_length=1000,
        blank=True,
        default="",
        editable=False,
        verbose_name=_("Enlace de Google Drive"),
        help_text=_(
            "Enlace para abrir el documento en Google Drive."
        ),
    )

    # ======================================================
    # DESCRIPCIÓN
    # ======================================================

    descripcion = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name=_("Descripción"),
        help_text=_(
            "Descripción breve del contenido "
            "del archivo."
        ),
    )

    # ======================================================
    # RETIRO LÓGICO
    # ======================================================

    fecha_retiro = models.DateTimeField(
        blank=True,
        null=True,
        editable=False,
        verbose_name=_("Fecha de retiro"),
    )

    usuario_retiro = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="archivos_proyecto_retirados",
        blank=True,
        null=True,
        editable=False,
        verbose_name=_("Retirado por"),
    )

    motivo_retiro = models.CharField(
        max_length=250,
        blank=True,
        default="",
        editable=False,
        verbose_name=_("Motivo del retiro"),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:
        verbose_name = _(
            "Archivo de proyecto"
        )

        verbose_name_plural = _(
            "Archivos de proyectos"
        )

        ordering = (
            "-is_active",
            "-fecha_documento",
            "-created_at",
        )

        indexes = [
            models.Index(
                fields=[
                    "proyecto",
                    "is_active",
                ],
                name="idx_proy_arch_act",
            ),
            models.Index(
                fields=[
                    "proyecto",
                    "fecha_documento",
                ],
                name="idx_proy_arch_fec",
            ),
            models.Index(
                fields=[
                    "proyecto",
                    "origen",
                ],
                name="idx_proy_arch_ori",
            ),
        ]

    # ======================================================
    # VALIDACIONES
    # ======================================================

    def clean(self):
        """
        Mantiene consistencia entre:

        - archivo local;
        - archivo en Google Drive;
        - estado documental;
        - información de retiro.
        """

        super().clean()

        errores = {}

        # ==================================================
        # NORMALIZAR TEXTOS
        # ==================================================

        self.descripcion = (
            self.descripcion
            or ""
        ).strip()

        self.drive_file_id = (
            self.drive_file_id
            or ""
        ).strip()

        self.drive_nombre = (
            self.drive_nombre
            or ""
        ).strip()

        self.drive_mime_type = (
            self.drive_mime_type
            or ""
        ).strip()

        self.drive_web_view_link = (
            self.drive_web_view_link
            or ""
        ).strip()

        self.motivo_retiro = (
            self.motivo_retiro
            or ""
        ).strip()

        # ==================================================
        # ARCHIVO LOCAL
        # ==================================================

        if self.origen == self.Origen.LOCAL:

            if not self.archivo:
                errores["archivo"] = _(
                    "Debe seleccionar un archivo local."
                )

            if (
                self.drive_file_id
                or self.drive_nombre
                or self.drive_mime_type
                or self.drive_web_view_link
            ):
                errores["origen"] = _(
                    "Un archivo local no puede contener "
                    "información de Google Drive."
                )

        # ==================================================
        # GOOGLE DRIVE
        # ==================================================

        elif self.origen == self.Origen.GOOGLE_DRIVE:

            if self.archivo:
                errores["archivo"] = _(
                    "Un archivo de Google Drive no debe "
                    "almacenarse también como archivo local."
                )

            if not self.drive_file_id:
                errores["drive_file_id"] = _(
                    "Debe existir un identificador "
                    "de Google Drive."
                )

            if not self.drive_nombre:
                errores["drive_nombre"] = _(
                    "Debe existir un nombre "
                    "para el archivo de Google Drive."
                )

            if not self.drive_web_view_link:
                errores["drive_web_view_link"] = _(
                    "Debe existir un enlace para abrir "
                    "el archivo en Google Drive."
                )

        else:

            errores["origen"] = _(
                "El origen del archivo no es válido."
            )

        # ==================================================
        # ARCHIVO RETIRADO
        # ==================================================

        if not self.is_active:

            if not self.fecha_retiro:
                errores["fecha_retiro"] = _(
                    "Un archivo retirado debe tener "
                    "fecha de retiro."
                )

            if not self.usuario_retiro_id:
                errores["usuario_retiro"] = _(
                    "Un archivo retirado debe indicar "
                    "quién realizó el retiro."
                )

            if not self.motivo_retiro:
                errores["motivo_retiro"] = _(
                    "Debe indicar el motivo del retiro."
                )

        # ==================================================
        # ARCHIVO ACTIVO
        # ==================================================

        else:

            if (
                self.fecha_retiro
                or self.usuario_retiro_id
                or self.motivo_retiro
            ):
                errores["is_active"] = _(
                    "Un archivo activo no puede contener "
                    "información de retiro."
                )

        # ==================================================
        # COHERENCIA TEMPORAL
        # ==================================================

        if (
            self.fecha_documento
            and self.fecha_retiro
            and self.fecha_retiro
            < self.fecha_documento
        ):
            errores["fecha_retiro"] = _(
                "La fecha de retiro no puede ser anterior "
                "a la fecha del documento."
            )

        # ==================================================
        # ERRORES
        # ==================================================

        if errores:
            raise ValidationError(
                errores
            )

    # ======================================================
    # PROPIEDADES
    # ======================================================

    @property
    def nombre_archivo(self):
        """
        Devuelve el nombre visible del documento
        independientemente de su origen.
        """

        if (
            self.origen
            == self.Origen.GOOGLE_DRIVE
        ):
            return (
                self.drive_nombre
                or _("Archivo de Google Drive")
            )

        if not self.archivo:
            return _("Archivo sin cargar")

        return (
            self.archivo.name
            .rsplit("/", 1)[-1]
        )

    @property
    def es_local(self):
        """
        Indica si el documento utiliza
        almacenamiento local.
        """

        return (
            self.origen
            == self.Origen.LOCAL
        )

    @property
    def es_google_drive(self):
        """
        Indica si el documento está almacenado
        en Google Drive.
        """

        return (
            self.origen
            == self.Origen.GOOGLE_DRIVE
        )

    @property
    def esta_disponible(self):
        """
        Indica si el documento continúa activo
        dentro del historial del Proyecto.
        """

        return bool(
            self.is_active
        )

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return (
            f"{self.proyecto.codigo} - "
            f"{self.nombre_archivo}"
        )