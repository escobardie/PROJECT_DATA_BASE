from django.db import models


class BaseModel(models.Model):
    """
    Modelo base para todas las entidades del sistema.
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
    )

    class Meta:
        abstract = True