from django.db import models


class BaseModel(models.Model):
    """
    Modelo abstracto base del sistema.

    Contiene campos comunes utilizados
    por todas las entidades.
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
        ordering = ("-created_at",) #Esto hace que, por defecto, los registros más recientes aparezcan primero en las consultas