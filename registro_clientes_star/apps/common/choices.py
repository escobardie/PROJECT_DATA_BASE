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