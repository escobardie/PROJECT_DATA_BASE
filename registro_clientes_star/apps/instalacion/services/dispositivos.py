"""
Servicios relacionados con dispositivos físicos
de una instalación.

Este módulo centraliza la transferencia de dispositivos
previstos en un Proyecto hacia una Instalacion.

Reglas principales:

- solamente se importan ProyectoDetalle cuyo origen
  sea un Dispositivo;
- cada unidad comercial genera un InstalacionDispositivo
  físico independiente;
- la cantidad del detalle debe ser un entero positivo;
- la instalación debe estar vinculada a una OT con Proyecto;
- la instalación no debe contener dispositivos previamente.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.instalacion.models import (
    Instalacion,
    InstalacionDispositivo,
)

from apps.proyecto.models import ProyectoDetalle


# ======================================================
# FUNCIONES PRIVADAS
# ======================================================

def _validar_instalacion_guardada(
    instalacion: Instalacion | None,
) -> None:
    """
    Valida que exista una instalación persistida.
    """

    if instalacion is None:
        raise ValueError(
            "Debe proporcionar una instalación válida."
        )

    if not instalacion.pk:
        raise ValueError(
            "La instalación debe estar guardada antes "
            "de importar dispositivos."
        )


def _bloquear_instalacion(
    instalacion: Instalacion,
) -> Instalacion:
    """
    Recupera y bloquea la instalación durante
    la operación de importación.
    """

    _validar_instalacion_guardada(
        instalacion
    )

    return (
        Instalacion.objects
        .select_for_update()
        .select_related(
            "orden_trabajo",
            "orden_trabajo__proyecto",
        )
        .get(
            pk=instalacion.pk,
        )
    )


def _validar_proyecto(
    instalacion: Instalacion,
) -> None:
    """
    Verifica que la instalación provenga
    de una OT asociada a Proyecto.
    """

    if not instalacion.orden_trabajo.proyecto_id:
        raise ValidationError(
            {
                "orden_trabajo": _(
                    "La instalación no está asociada "
                    "a una orden de trabajo proveniente "
                    "de un proyecto."
                )
            }
        )


def _validar_instalacion_sin_dispositivos(
    instalacion: Instalacion,
) -> None:
    """
    Evita una segunda importación automática.

    Si ya existen dispositivos, la importación
    debe realizarse de forma manual o mediante
    una estrategia explícita futura.
    """

    if instalacion.dispositivos.exists():
        raise ValidationError(
            {
                "dispositivos": _(
                    "La instalación ya tiene dispositivos "
                    "registrados. No puede realizarse "
                    "la importación automática."
                )
            }
        )


def _convertir_cantidad_unidades(
    detalle: ProyectoDetalle,
) -> int:
    """
    Convierte la cantidad comercial en una cantidad
    de unidades físicas.

    Para dispositivos solo se admiten enteros positivos.
    """

    cantidad = (
        detalle.cantidad
        or Decimal("0")
    )

    if cantidad <= 0:
        raise ValidationError(
            {
                "cantidad": _(
                    "La cantidad del dispositivo %(detalle)s "
                    "debe ser mayor que cero."
                )
                % {
                    "detalle": detalle.codigo,
                }
            }
        )

    cantidad_entera = cantidad.to_integral_value()

    if cantidad != cantidad_entera:
        raise ValidationError(
            {
                "cantidad": _(
                    "La cantidad del dispositivo %(detalle)s "
                    "debe ser un número entero. "
                    "Cantidad actual: %(cantidad)s."
                )
                % {
                    "detalle": detalle.codigo,
                    "cantidad": cantidad,
                }
            }
        )

    return int(
        cantidad_entera
    )


def _obtener_detalles_dispositivo(
    instalacion: Instalacion,
):
    """
    Obtiene únicamente los detalles del proyecto
    cuyo origen es un dispositivo.
    """

    proyecto = (
        instalacion
        .orden_trabajo
        .proyecto
    )

    return (
        proyecto.detalles
        .filter(
            dispositivo__isnull=False,
        )
        .select_related(
            "dispositivo",
        )
        .order_by(
            "orden",
            "codigo",
        )
    )


# ======================================================
# IMPORTAR DISPOSITIVOS DESDE PROYECTO
# ======================================================

@transaction.atomic
def cargar_dispositivos_desde_proyecto(
    *,
    instalacion: Instalacion,
) -> list[InstalacionDispositivo]:
    """
    Precarga en una instalación los dispositivos
    previstos en el proyecto asociado a su OT.

    Cada unidad física genera un registro independiente
    de InstalacionDispositivo.

    Ejemplo:

        ProyectoDetalle:
            dispositivo = Cámara IP
            cantidad = 3.00

        Resultado:
            InstalacionDispositivo #1
            InstalacionDispositivo #2
            InstalacionDispositivo #3

    Los campos físicos individuales quedan inicialmente
    vacíos:

    - número de serie;
    - MAC;
    - IP;
    - ubicación;
    - credenciales.

    Returns:
        list[InstalacionDispositivo]:
            Registros creados.

    Raises:
        ValidationError:
            Si la instalación no proviene de Proyecto,
            ya contiene dispositivos, no existen
            dispositivos en el proyecto o alguna cantidad
            no representa unidades físicas enteras.
    """

    objeto = _bloquear_instalacion(
        instalacion
    )

    _validar_proyecto(
        objeto
    )

    _validar_instalacion_sin_dispositivos(
        objeto
    )

    detalles = list(
        _obtener_detalles_dispositivo(
            objeto
        )
    )

    if not detalles:
        raise ValidationError(
            {
                "dispositivos": _(
                    "El proyecto asociado no contiene "
                    "dispositivos para importar."
                )
            }
        )

    # --------------------------------------------------
    # VALIDAR TODAS LAS CANTIDADES ANTES DE CREAR
    # --------------------------------------------------

    cantidades = []

    for detalle in detalles:
        cantidades.append(
            (
                detalle,
                _convertir_cantidad_unidades(
                    detalle
                ),
            )
        )

    # --------------------------------------------------
    # CREACIÓN DE UNIDADES FÍSICAS
    # --------------------------------------------------

    creados = []

    for detalle, cantidad in cantidades:
        for _ in range(cantidad):
            dispositivo_instalado = (
                InstalacionDispositivo(
                    instalacion=objeto,
                    dispositivo=detalle.dispositivo,
                )
            )

            dispositivo_instalado.full_clean()

            dispositivo_instalado.save()

            creados.append(
                dispositivo_instalado
            )

    return creados


__all__ = (
    "cargar_dispositivos_desde_proyecto",
)