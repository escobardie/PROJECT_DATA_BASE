from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from apps.common.exceptions import (
    PuntoVentaNoDisponibleError,
)


class NumeradorFactura(models.Model):
    """
    Administra la numeración secuencial de facturas
    por punto de venta.

    Es un modelo técnico encargado únicamente de generar
    números consecutivos seguros.
    """

    # ======================================================
    # IDENTIFICACIÓN
    # ======================================================

    punto_venta = models.PositiveSmallIntegerField(
        unique=True,
        verbose_name=_("Punto de venta"),
        help_text=_(
            "Número identificador del punto de venta."
        ),
    )

    # ======================================================
    # NUMERACIÓN
    # ======================================================

    ultimo_numero = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Último número utilizado"),
        help_text=_(
            "Último número de factura generado."
        ),
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    activo = models.BooleanField(
        default=True,
        verbose_name=_("Activo"),
    )

    # ======================================================
    # CONFIGURACIÓN DEL MODELO
    # ======================================================

    class Meta:
        verbose_name = _("Numerador de factura")
        verbose_name_plural = _("Numeradores de factura")
        ordering = ("punto_venta",)

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):
        return f"{self.punto_venta:04d}"

    # ======================================================
    # LÓGICA DE NEGOCIO
    # ======================================================

    @classmethod
    def obtener_siguiente_numero(cls, punto_venta):
        """
        Obtiene el siguiente número disponible
        para un punto de venta.

        La operación es segura para múltiples usuarios
        generando facturas simultáneamente.
        """

        with transaction.atomic():

            try:
                numerador = (
                    cls.objects
                    .select_for_update()
                    .get(
                        punto_venta=punto_venta,
                    )
                )

            except cls.DoesNotExist:

                numerador = cls.objects.create(
                    punto_venta=punto_venta,
                    ultimo_numero=0,
                )

                numerador = (
                    cls.objects
                    .select_for_update()
                    .get(
                        pk=numerador.pk,
                    )
                )

            if not numerador.activo:
                raise PuntoVentaNoDisponibleError()

            numerador.ultimo_numero += 1

            numerador.save(
                update_fields=[
                    "ultimo_numero",
                ],
            )

            return numerador.ultimo_numero