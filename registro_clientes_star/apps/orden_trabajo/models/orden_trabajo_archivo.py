from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel
from apps.usuarios.models import Usuario

from .orden_trabajo import OrdenTrabajo


class OrdenTrabajoArchivo(BaseModel):
    """
    Representa un archivo asociado a una orden de trabajo.

    Permite almacenar documentos, evidencias, fotografías
    y archivos técnicos relacionados con la ejecución de la orden.
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
            "Descripción breve del contenido del archivo."
        ),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:
        verbose_name = _("Archivo de orden de trabajo")
        verbose_name_plural = _("Archivos de órdenes de trabajo")

        ordering = (
            "-created_at",
        )

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return (
            f"{self.orden_trabajo.codigo} - "
            f"{self.nombre_archivo}"
        )

    # ======================================================
    # PROPIEDADES
    # ======================================================

    @property
    def nombre_archivo(self):
        """
        Devuelve únicamente el nombre del archivo,
        sin incluir la ruta de almacenamiento.
        """

        if not self.archivo:
            return _("Archivo sin cargar")

        return self.archivo.name.rsplit("/", 1)[-1]