from django.db import models
from django.utils.translation import gettext_lazy as _

class EstadoServicio(models.TextChoices):
    ACTIVO = "ACTIVO", "Activo"
    SUSPENDIDO = "SUSPENDIDO", "Suspendido"



class TipoClienteChoices(models.TextChoices):
    PERSONA = "PERSONA", "Persona Física"
    EMPRESA = "EMPRESA", "Empresa"


class EstadoServicioChoices(models.TextChoices):
    ACTIVO = "ACTIVO", "Activo"
    INACTIVO = "INACTIVO", "Inactivo"


# class EstadoServicioContratadoChoices(models.TextChoices):
#     """
#     Estados posibles de un servicio contratado.
#     """

#     ACTIVO = "ACTIVO", "Activo"
#     SUSPENDIDO = "SUSPENDIDO", "Suspendido"
#     FINALIZADO = "FINALIZADO", "Finalizado"
#     CANCELADO = "CANCELADO", "Cancelado"
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

    MANTENIMIENTO = ("MANTENIMIENTO", _("En mantenimiento"),)

    RETIRADO = "RETIRADO", _("Retirado")

    REEMPLAZADO = "REEMPLAZADO", _("Reemplazado")

    DANADO = "DANADO", _("Dañado")

class EstadoProyectoChoices(models.TextChoices):
    """
    Estados posibles de un proyecto.
    """

    PLANIFICADO = (
        "PLANIFICADO",
        _("Planificado"),
    )

    PRESUPUESTADO = (
        "PRESUPUESTADO",
        _("Presupuestado"),
    )

    APROBADO = (
        "APROBADO",
        _("Aprobado"),
    )

    EN_EJECUCION = (
        "EN_EJECUCION",
        _("En ejecución"),
    )

    FINALIZADO = (
        "FINALIZADO",
        _("Finalizado"),
    )

    CANCELADO = (
        "CANCELADO",
        _("Cancelado"),
    )