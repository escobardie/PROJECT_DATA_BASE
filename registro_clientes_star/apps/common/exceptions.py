from django.utils.translation import gettext_lazy as _


class BusinessLogicError(Exception):
    """
    Excepción base para todos los errores de lógica de negocio
    del sistema.

    Todas las excepciones de dominio deben heredar de esta clase.
    """

    default_message = _("Se produjo un error de lógica de negocio.")

    def __init__(self, message=None):
        super().__init__(message or self.default_message)


# ======================================================
# FACTURACIÓN
# ======================================================

class PuntoVentaNoDisponibleError(BusinessLogicError):
    """
    El punto de venta no se encuentra disponible para emitir
    facturas.
    """

    default_message = _(
        "El punto de venta no se encuentra disponible."
    )


class FacturaAnuladaError(BusinessLogicError):
    """
    La factura se encuentra anulada.
    """

    default_message = _(
        "La factura se encuentra anulada."
    )


class FacturaPagadaError(BusinessLogicError):
    """
    La factura ya fue cancelada completamente.
    """

    default_message = _(
        "La factura ya se encuentra pagada."
    )


# ======================================================
# CLIENTES
# ======================================================

class ClienteInactivoError(BusinessLogicError):
    """
    El cliente no se encuentra activo.
    """

    default_message = _(
        "El cliente no se encuentra activo."
    )


# ======================================================
# SERVICIOS
# ======================================================

class ServicioInactivoError(BusinessLogicError):
    """
    El servicio no se encuentra activo.
    """

    default_message = _(
        "El servicio no se encuentra activo."
    )


# ======================================================
# DISPOSITIVOS
# ======================================================

class DispositivoNoDisponibleError(BusinessLogicError):
    """
    El dispositivo no se encuentra disponible.
    """

    default_message = _(
        "El dispositivo no se encuentra disponible."
    )


# ======================================================
# PROYECTOS
# ======================================================

class ProyectoFinalizadoError(BusinessLogicError):
    """
    El proyecto ya se encuentra finalizado.
    """

    default_message = _(
        "El proyecto ya fue finalizado."
    )