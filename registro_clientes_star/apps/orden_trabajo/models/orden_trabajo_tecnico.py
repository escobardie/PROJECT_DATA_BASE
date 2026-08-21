from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel
from apps.usuarios.models import Usuario

from .orden_trabajo import OrdenTrabajo


class OrdenTrabajoTecnico(BaseModel):
    """
    Representa la asignación de un técnico
    a una orden de trabajo.

    Una orden puede tener varios técnicos activos,
    pero solamente uno puede ser el principal.

    La asignación y desasignación se gestionan
    mediante services.
    """

    # ======================================================
    # RELACIONES
    # ======================================================

    orden_trabajo = models.ForeignKey(
        OrdenTrabajo,
        on_delete=models.CASCADE,
        related_name="tecnicos",
        verbose_name=_("Orden de trabajo"),
    )

    tecnico = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo_asignadas",
        verbose_name=_("Técnico"),
    )

    # ======================================================
    # ASIGNACIÓN
    # ======================================================

    es_principal = models.BooleanField(
        default=False,
        verbose_name=_("Técnico principal"),
        help_text=_(
            "Indica si el técnico es el responsable "
            "principal de ejecutar la orden."
        ),
    )

    fecha_asignacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de asignación"),
        help_text=_(
            "Fecha y hora en que el técnico fue "
            "asignado a la orden."
        ),
    )

    usuario_asignacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="asignaciones_tecnicos_ot_registradas",
        blank=True,
        null=True,
        editable=False,
        verbose_name=_("Asignado por"),
        help_text=_(
            "Usuario que registró formalmente "
            "la asignación del técnico."
        ),
    )

    # ======================================================
    # DESASIGNACIÓN
    # ======================================================

    fecha_desasignacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fecha de desasignación"),
        help_text=_(
            "Fecha y hora en que el técnico fue "
            "desasignado de la orden."
        ),
    )

    usuario_desasignacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="desasignaciones_tecnicos_ot_registradas",
        blank=True,
        null=True,
        editable=False,
        verbose_name=_("Desasignado por"),
        help_text=_(
            "Usuario que registró formalmente "
            "la desasignación del técnico."
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
            "Observaciones relacionadas con la participación "
            "del técnico en la orden de trabajo."
        ),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:
        verbose_name = _("Técnico asignado")
        verbose_name_plural = _("Técnicos asignados")

        ordering = (
            "-is_active",
            "-es_principal",
            "tecnico",
        )

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "orden_trabajo",
                    "tecnico",
                ],
                name="unique_ot_tecnico",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "orden_trabajo",
                    "is_active",
                ],
                name="idx_ot_tec_activo",
            ),
        ]

    # ======================================================
    # VALIDACIONES
    # ======================================================

    def clean(self):
        """
        Valida la coherencia de la asignación.

        Reglas:

        - solamente puede existir un técnico principal activo;
        - un técnico inactivo no puede ser principal;
        - fecha y usuario de desasignación deben ser coherentes.
        """

        super().clean()

        errores = {}

        # ==================================================
        # TÉCNICO PRINCIPAL
        # ==================================================

        if (
            self.es_principal
            and not self.is_active
        ):
            errores["es_principal"] = _(
                "Un técnico desasignado no puede permanecer "
                "como técnico principal."
            )

        if (
            self.orden_trabajo_id
            and self.es_principal
            and self.is_active
        ):
            existe_principal = (
                OrdenTrabajoTecnico.objects
                .filter(
                    orden_trabajo_id=(
                        self.orden_trabajo_id
                    ),
                    es_principal=True,
                    is_active=True,
                )
                .exclude(
                    pk=self.pk,
                )
                .exists()
            )

            if existe_principal:
                errores["es_principal"] = _(
                    "La orden de trabajo ya tiene "
                    "un técnico principal activo."
                )

        # ==================================================
        # ASIGNACIÓN
        # ==================================================

        if (
            self.usuario_asignacion_id
            and not self.fecha_asignacion
        ):
            errores["fecha_asignacion"] = _(
                "Debe existir una fecha de asignación "
                "cuando existe un usuario de asignación."
            )

        # ==================================================
        # DESASIGNACIÓN
        # ==================================================

        if (
            self.fecha_desasignacion
            and not self.usuario_desasignacion_id
        ):
            errores["usuario_desasignacion"] = _(
                "Debe registrarse quién realizó "
                "la desasignación."
            )

        if (
            self.usuario_desasignacion_id
            and not self.fecha_desasignacion
        ):
            errores["fecha_desasignacion"] = _(
                "Debe existir una fecha de desasignación."
            )

        if (
            self.fecha_asignacion
            and self.fecha_desasignacion
            and self.fecha_desasignacion
            < self.fecha_asignacion
        ):
            errores["fecha_desasignacion"] = _(
                "La fecha de desasignación no puede ser "
                "anterior a la fecha de asignación."
            )

        if errores:
            raise ValidationError(
                errores
            )

    # ======================================================
    # PROPIEDADES
    # ======================================================

    @property
    def esta_asignado(self) -> bool:
        """
        Indica si el técnico se encuentra
        actualmente asignado.
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
            f"{self.tecnico}"
        )