from django.db import models
from django.utils.translation import gettext_lazy as _


from apps.common.models import BaseModel

from apps.usuarios.models import Usuario

from .orden_trabajo import OrdenTrabajo


class OrdenTrabajoArchivo(BaseModel):
    """
    Archivos asociados a una orden de trabajo.

    Permite almacenar evidencias, documentos,
    fotografías y archivos técnicos.
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
        verbose_name=_("Usuario"),
        help_text=_(
            "Usuario que cargó el archivo."
        ),
    )

    # ======================================================
    # ARCHIVO
    # ======================================================

    archivo = models.FileField(
        upload_to="ordenes_trabajo/%Y/%m/",
        verbose_name=_("Archivo"),
    )

    descripcion = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name=_("Descripción"),
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
            "-created_at",
        )

        indexes = [

            models.Index(
                fields=[
                    "orden_trabajo",
                ],
                name=(
                    "idx_ot_archivo_ot"
                ),
            ),

            models.Index(
                fields=[
                    "usuario",
                ],
                name=(
                    "idx_ot_archivo_usuario"
                ),
            ),

        ]

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):

        return (
            f"{self.orden_trabajo.codigo} - "
            f"{self.archivo.name}"
        )