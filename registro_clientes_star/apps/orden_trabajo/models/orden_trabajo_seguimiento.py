from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel
from apps.usuarios.models import Usuario

from .orden_trabajo import OrdenTrabajo


class OrdenTrabajoSeguimiento(BaseModel):
    """
    Representa una actualización dentro del historial
    de una orden de trabajo.

    Cada seguimiento registra un comentario, novedad
    o avance informado por un usuario.
    """

    # ======================================================
    # RELACIONES
    # ======================================================

    orden_trabajo = models.ForeignKey(
        OrdenTrabajo,
        on_delete=models.CASCADE,
        related_name="seguimientos",
        verbose_name=_("Orden de trabajo"),
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="seguimientos_ordenes_trabajo",
        verbose_name=_("Usuario"),
        help_text=_(
            "Usuario que registró el seguimiento."
        ),
    )

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    comentario = models.TextField(
        verbose_name=_("Comentario"),
        help_text=_(
            "Descripción de la novedad, avance o actualización "
            "de la orden de trabajo."
        ),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:
        verbose_name = _("Seguimiento de orden de trabajo")
        verbose_name_plural = _("Seguimientos de órdenes de trabajo")

        ordering = (
            "-created_at",
        )

        indexes = [
            models.Index(
                fields=[
                    "orden_trabajo",
                    "created_at",
                ],
                name="idx_ot_seg_fecha",
            ),
        ]

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return (
            f"{self.orden_trabajo.codigo} - "
            f"{self.created_at:%d/%m/%Y %H:%M}"
        )