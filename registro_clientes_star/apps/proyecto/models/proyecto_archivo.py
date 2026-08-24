from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel
from apps.usuarios.models import Usuario

from .proyecto import Proyecto


class ProyectoArchivo(BaseModel):
    """
    Representa un archivo asociado a un Proyecto.

    Puede corresponder a:

    - documentación comercial;
    - presupuestos;
    - propuestas;
    - fotografías;
    - planos;
    - memorias técnicas;
    - aprobaciones;
    - actas;
    - informes;
    - documentación administrativa;
    - cualquier otra evidencia relacionada
      con el proyecto.

    Los archivos forman parte del historial documental
    del proyecto.

    Una vez registrados no deben modificarse ni eliminarse
    físicamente desde el flujo funcional normal.

    Si un documento deja de ser válido debe retirarse
    lógicamente conservando toda su trazabilidad.
    """

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
    # ARCHIVO
    # ======================================================

    archivo = models.FileField(
        upload_to="proyectos/%Y/%m/",
        verbose_name=_("Archivo"),
        help_text=_(
            "Documento, fotografía, plano, informe "
            "o archivo relacionado con el proyecto."
        ),
    )

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
        help_text=_(
            "Fecha y hora en que el archivo "
            "fue retirado del flujo documental."
        ),
    )

    usuario_retiro = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="archivos_proyecto_retirados",
        blank=True,
        null=True,
        editable=False,
        verbose_name=_("Retirado por"),
        help_text=_(
            "Usuario que retiró formalmente "
            "el archivo."
        ),
    )

    motivo_retiro = models.CharField(
        max_length=250,
        blank=True,
        default="",
        editable=False,
        verbose_name=_("Motivo del retiro"),
        help_text=_(
            "Motivo por el cual el archivo dejó "
            "de considerarse activo."
        ),
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
        ]

    # ======================================================
    # VALIDACIONES
    # ======================================================

    def clean(self):
        """
        Mantiene la consistencia del historial documental.
        """

        super().clean()

        errores = {}

        # ==================================================
        # NORMALIZAR DESCRIPCIÓN
        # ==================================================

        self.descripcion = (
            self.descripcion
            or ""
        ).strip()

        self.motivo_retiro = (
            self.motivo_retiro
            or ""
        ).strip()

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
                    "Debe indicar el motivo del retiro "
                    "del archivo."
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
        Devuelve únicamente el nombre del archivo
        sin incluir la ruta de almacenamiento.
        """

        if not self.archivo:
            return _("Archivo sin cargar")

        return (
            self.archivo.name
            .rsplit("/", 1)[-1]
        )

    @property
    def esta_disponible(self):
        """
        Indica si el documento continúa activo
        dentro del historial del proyecto.
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