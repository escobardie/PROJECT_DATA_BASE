"""
Generador de códigos de negocio del sistema.
"""

from apps.common.constants import (
    CODE_SEPARATOR,
    CODE_PADDING,
)


def generate_code(prefix: str, number: int) -> str:
    """
    Genera un código de negocio.

    Ejemplo:
        prefix = "CLI"
        number = 25

        Resultado:
        CLI-000025

    Args:
        prefix:
            Prefijo del código.

        number:
            Número identificador.

    Returns:
        Código formateado.
    """

    if not prefix:
        raise ValueError(
            "El prefijo del código es obligatorio."
        )

    if number is None:
        raise ValueError(
            "El número del código es obligatorio."
        )

    if not isinstance(number, int):
        raise TypeError(
            "El número del código debe ser entero."
        )

    formatted_number = str(number).zfill(
        CODE_PADDING
    )

    return (
        f"{prefix}"
        f"{CODE_SEPARATOR}"
        f"{formatted_number}"
    )