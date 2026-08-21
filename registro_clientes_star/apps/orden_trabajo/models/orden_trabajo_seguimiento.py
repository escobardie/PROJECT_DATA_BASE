from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel
from apps.usuarios.models import Usuario

from .orden_trabajo import OrdenTrabajo


class OrdenTrabajoSeguimiento(BaseModel):
    """
    Representa una actualización dentro del historial
    de una orden de trabajo.

    Cada seguimiento es un registro histórico.

    Una vez registrado no debe modificarse ni eliminarse
    desde el flujo funcional normal.
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
        editable=False,
        verbose_name=_("Registrado por"),
        help_text=_(
            "Usuario que registró formalmente "
            "el seguimiento."
        ),
    )

    # ======================================================
    # FECHA FUNCIONAL
    # ======================================================

    fecha_seguimiento = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha del seguimiento"),
        help_text=_(
            "Fecha y hora real en que ocurrió "
            "la novedad o actualización."
        ),
    )

    # ======================================================
    # INFORMACIÓN
    # ======================================================

    comentario = models.TextField(
        verbose_name=_("Comentario"),
        help_text=_(
            "Descripción de la novedad, avance "
            "o actualización de la orden de trabajo."
        ),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:
        verbose_name = _(
            "Seguimiento de orden de trabajo"
        )

        verbose_name_plural = _(
            "Seguimientos de órdenes de trabajo"
        )

        ordering = (
            "-fecha_seguimiento",
            "-created_at",
        )

        indexes = [
            models.Index(
                fields=[
                    "orden_trabajo",
                    "fecha_seguimiento",
                ],
                name="idx_ot_seg_fecha",
            ),
        ]

    # ======================================================
    # VALIDACIONES
    # ======================================================

    def clean(self):
        """
        Valida la información mínima
        del seguimiento.
        """

        super().clean()

        comentario = (
            self.comentario
            or ""
        ).strip()

        if not comentario:
            raise ValidationError(
                {
                    "comentario": _(
                        "Debe indicar una novedad, avance "
                        "o comentario para el seguimiento."
                    )
                }
            )

        self.comentario = comentario

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        fecha = (
            self.fecha_seguimiento
            or self.created_at
        )

        if fecha:
            return (
                f"{self.orden_trabajo.codigo} - "
                f"{fecha:%d/%m/%Y %H:%M}"
            )

        return (
            f"{self.orden_trabajo.codigo} - "
            f"{_('Seguimiento sin guardar')}"
        )