from django.db import models

from apps.common.constants import MAX_CODE_LENGTH
from apps.common.code_generator import generate_code

from .base import BaseModel


class CodeModel(BaseModel):
    """
    Modelo abstracto para entidades
    que requieren un código de negocio.
    """

    codigo = models.CharField(
        max_length=MAX_CODE_LENGTH,
        unique=True,
        editable=False,
        verbose_name="Código",
    )

    CODE_PREFIX = None

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
        Genera automáticamente el código
        de negocio basado en el ID.
        """

        if not self.CODE_PREFIX:
            raise ValueError(
                "Debe definir CODE_PREFIX en el modelo."
            )

        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new:
            self.codigo = generate_code(
                self.CODE_PREFIX,
                self.pk
            )

            super().save(
                update_fields=["codigo"]
            )