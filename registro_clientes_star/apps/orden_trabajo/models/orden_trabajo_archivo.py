from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel
from apps.usuarios.models import Usuario

from .orden_trabajo import OrdenTrabajo


class OrdenTrabajoArchivo(BaseModel):
    """
    Representa un archivo asociado a una Orden de Trabajo.

    Puede corresponder a:

    - documentos;
    - fotografías;
    - evidencias;
    - informes;
    - actas;
    - archivos técnicos;
    - cualquier otra documentación relacionada
      con la ejecución de la OT.

    Los archivos forman parte del historial documental.

    Una vez registrados no deben modificarse ni eliminarse
    físicamente desde el flujo funcional normal.

    Si un archivo deja de ser válido, debe retirarse
    lógicamente conservando su trazabilidad.
    """

    # ======================================================
    # RELACIONES
    # ======================================================

    orden_trabajo = models.ForeignKey(
        OrdenTrabajo,
        on_delete=models.CASCADE,
        related_name="archivos",
        verbose_name=_("Orden de trabajo"),
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="archivos_ordenes_trabajo",
        editable=False,
        verbose_name=_("Cargado por"),
        help_text=_(
            "Usuario que registró formalmente "
            "el archivo en la orden de trabajo."
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
        upload_to="ordenes_trabajo/%Y/%m/",
        verbose_name=_("Archivo"),
        help_text=_(
            "Documento, fotografía o archivo técnico "
            "relacionado con la orden de trabajo."
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
    # RETIRO / ANULACIÓN LÓGICA
    # ======================================================

    fecha_retiro = models.DateTimeField(
        blank=True,
        null=True,
        editable=False,
        verbose_name=_("Fecha de retiro"),
        help_text=_(
            "Fecha y hora en que el archivo "
            "fue retirado del flujo operativo."
        ),
    )

    usuario_retiro = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="archivos_ot_retirados",
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
            "Motivo por el cual el archivo "
            "dejó de considerarse activo."
        ),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:
        verbose_name = _(
            "Archivo de orden de trabajo"
        )

        verbose_name_plural = _(
            "Archivos de órdenes de trabajo"
        )

        ordering = (
            "-is_active",
            "-fecha_documento",
            "-created_at",
        )

        indexes = [
            models.Index(
                fields=[
                    "orden_trabajo",
                    "is_active",
                ],
                name="idx_ot_arch_activo",
            ),
            models.Index(
                fields=[
                    "orden_trabajo",
                    "fecha_documento",
                ],
                name="idx_ot_arch_fecha",
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

        # --------------------------------------------------
        # DESCRIPCIÓN
        # --------------------------------------------------

        self.descripcion = (
            self.descripcion
            or ""
        ).strip()

        # --------------------------------------------------
        # ARCHIVO RETIRADO
        # --------------------------------------------------

        if not self.is_active:

            if not self.fecha_retiro:
                raise ValidationError(
                    {
                        "fecha_retiro": _(
                            "Un archivo retirado debe "
                            "tener fecha de retiro."
                        )
                    }
                )

            if not self.usuario_retiro_id:
                raise ValidationError(
                    {
                        "usuario_retiro": _(
                            "Un archivo retirado debe "
                            "indicar quién realizó "
                            "el retiro."
                        )
                    }
                )

            if not (
                self.motivo_retiro
                or ""
            ).strip():
                raise ValidationError(
                    {
                        "motivo_retiro": _(
                            "Debe indicar el motivo "
                            "del retiro del archivo."
                        )
                    }
                )

        # --------------------------------------------------
        # ARCHIVO ACTIVO
        # --------------------------------------------------

        else:

            if (
                self.fecha_retiro
                or self.usuario_retiro_id
                or self.motivo_retiro
            ):
                raise ValidationError(
                    _(
                        "Un archivo activo no puede tener "
                        "información de retiro."
                    )
                )

        # --------------------------------------------------
        # COHERENCIA TEMPORAL
        # --------------------------------------------------

        if (
            self.fecha_documento
            and self.fecha_retiro
            and self.fecha_retiro
            < self.fecha_documento
        ):
            raise ValidationError(
                {
                    "fecha_retiro": _(
                        "La fecha de retiro no puede ser "
                        "anterior a la fecha del documento."
                    )
                }
            )

        self.motivo_retiro = (
            self.motivo_retiro
            or ""
        ).strip()

    # ======================================================
    # PROPIEDADES
    # ======================================================

    @property
    def nombre_archivo(self):
        """
        Devuelve únicamente el nombre almacenado,
        sin incluir la ruta completa.
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
        Indica si el archivo continúa activo
        dentro del historial operativo.
        """

        return bool(
            self.is_active
        )

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return (
            f"{self.orden_trabajo.codigo} - "
            f"{self.nombre_archivo}"
        )