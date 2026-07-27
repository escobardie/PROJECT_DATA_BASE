from django.db import models
from django.utils.translation import gettext_lazy as _


class TipoClienteChoices(models.TextChoices):
    PERSONA = "PERSONA", _("Persona Física")
    EMPRESA = "EMPRESA", _("Empresa")


class EstadoServicioChoices(models.TextChoices):
    ACTIVO = "ACTIVO", _("Activo")
    INACTIVO = "INACTIVO", _("Inactivo")


class EstadoServicioContratadoChoices(models.TextChoices):
    PENDIENTE = "PENDIENTE", _("Pendiente")
    ACTIVO = "ACTIVO", _("Activo")
    SUSPENDIDO = "SUSPENDIDO", _("Suspendido")
    FINALIZADO = "FINALIZADO", _("Finalizado")
    CANCELADO = "CANCELADO", _("Cancelado")


class EstadoDispositivoChoices(models.TextChoices):
    """
    Estados posibles de un dispositivo físico instalado.
    """

    ACTIVO = "ACTIVO", _("Activo")
    MANTENIMIENTO = "MANTENIMIENTO", _("En mantenimiento")
    RETIRADO = "RETIRADO", _("Retirado")
    REEMPLAZADO = "REEMPLAZADO", _("Reemplazado")
    DANADO = "DANADO", _("Dañado")


class EstadoProyectoChoices(models.TextChoices):
    """
    Estados posibles de un proyecto.
    """

    PLANIFICADO = "PLANIFICADO", _("Planificado")
    PRESUPUESTADO = "PRESUPUESTADO", _("Presupuestado")
    APROBADO = "APROBADO", _("Aprobado")
    EN_EJECUCION = "EN_EJECUCION", _("En ejecución")
    FINALIZADO = "FINALIZADO", _("Finalizado")
    CANCELADO = "CANCELADO", _("Cancelado")

class EstadoFacturaChoices(models.TextChoices):
    """
    Estados posibles de una factura.
    """

    PENDIENTE = "pendiente", _("Pendiente")
    PARCIAL = "parcial", _("Parcial")
    PAGADA = "pagada", _("Pagada")
    VENCIDA = "vencida", _("Vencida")
    ANULADA = "anulada", _("Anulada")

class MedioPagoChoices(models.TextChoices):
    """
    Medios de pago posibles para un pago.
    """

    EFECTIVO = "efectivo", _("Efectivo")
    TARJETA_CREDITO = "tarjeta_credito", _("Tarjeta de crédito")
    TARJETA_DEBITO = "tarjeta_debito", _("Tarjeta de débito")
    TRANSFERENCIA_BANCARIA = "transferencia_bancaria", _("Transferencia bancaria")
    #ADELANTO_MITAD_INICIO_RESTO_FINALIZAR = "adelanto_mitad_inicio_resto_finalizar", _("Adelanto, mitad (50%) al inicio y resto (50%) al finalizar")
    MITAD_MITAD = "mitad_mitad", _("Mitad (50%) al inicio y resto (50%) al finalizar")
    CHEQUE = "cheque", _("Cheque")
    OTRO = "otro", _("Otro")