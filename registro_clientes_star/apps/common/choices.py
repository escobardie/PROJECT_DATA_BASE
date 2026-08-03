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

    PENDIENTE = "PENDIENTE", _("Pendiente")
    PARCIAL = "PARCIAL", _("Parcial")
    PAGADA = "PAGADA", _("Pagada")
    VENCIDA = "VENCIDA", _("Vencida")
    ANULADA = "ANULADA", _("Anulada")

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


# ==========================================================
# TELECOM
# ==========================================================

class TipoConceptoTelecomChoices(models.TextChoices):
    """
    Tipo de concepto del catálogo de telecom.
    """

    MANO_DE_OBRA = "MANO_DE_OBRA", _("Mano de obra")
    MATERIAL = "MATERIAL", _("Material")


class MonedaChoices(models.TextChoices):
    """
    Moneda en la que está expresado un importe.
    """

    PESOS = "PESOS", _("Pesos")
    DOLAR = "DOLAR", _("Dólares")


class TipoTrabajoTelecomChoices(models.TextChoices):
    """
    Tipo de trabajo realizado en un presupuesto de telecom.
    """

    INSTALACION = "INSTALACION", _("Instalación")
    DESINSTALACION = "DESINSTALACION", _("Desinstalación")
    REINSTALACION = "REINSTALACION", _("Reinstalación")


class TipoRecargoTelecomChoices(models.TextChoices):
    """
    Recargos porcentuales aplicables a la mano de obra
    de telecom según turno, distancia y día.

    Los combos no listados (por ejemplo, instalación
    diurna, o desinstalación diurna a menos de 50 km)
    no llevan recargo: se facturan al valor base del
    catálogo.
    """

    INSTALACION_NOCTURNO_0_50 = (
        "INSTALACION_NOCTURNO_0_50",
        _("Instalación nocturna (0 a 50 km)"),
    )
    INSTALACION_NOCTURNO_50_MAS = (
        "INSTALACION_NOCTURNO_50_MAS",
        _("Instalación nocturna (+50 km)"),
    )
    DESINSTALACION_DIURNO_50_MAS = (
        "DESINSTALACION_DIURNO_50_MAS",
        _("Desinstalación diurna (+50 km)"),
    )
    DESINSTALACION_NOCTURNO_0_50 = (
        "DESINSTALACION_NOCTURNO_0_50",
        _("Desinstalación nocturna (0 a 50 km)"),
    )
    REINSTALACION_NOCTURNO_0_50 = (
        "REINSTALACION_NOCTURNO_0_50",
        _("Reinstalación nocturna (0 a 50 km)"),
    )
    REINSTALACION_NOCTURNO_50_MAS = (
        "REINSTALACION_NOCTURNO_50_MAS",
        _("Reinstalación nocturna (+50 km)"),
    )
    SABADO = "SABADO", _("Sábado")
    DOMINGO = "DOMINGO", _("Domingo")
    FERIADO = "FERIADO", _("Feriado")


# ==========================================================
# INSTALACION
# ==========================================================

class EstadoInstalacionChoices(models.TextChoices):
    PENDIENTE = "pendiente", _("Pendiente")
    PROGRAMADA = "programada", _("Programada")
    EN_PROCESO = "en_proceso", _("En proceso")
    FINALIZADA = "finalizada", _("Finalizada")
    CANCELADA = "cancelada", _("Cancelada")

class PrioridadInstalacionChoices(models.TextChoices):
    NORMAL = "normal", _("Normal")
    ALTA = "alta", _("Alta")
    URGENTE = "urgente", _("Urgente")
    CRITICA = "critica", _("Crítica")

class RolTecnicoInstalacionChoices(models.TextChoices):
    RESPONSABLE = "responsable", _("Responsable")
    AYUDANTE = "ayudante", _("Ayudante")
    SUPERVISOR = "supervisor", _("Supervisor")

class EstadoDispositivoInstaladoChoices(models.TextChoices):
    """
    Estados posibles de un dispositivo instalado.
    """

    INSTALADO = "instalado", _("Instalado")
    RETIRADO = "retirado", _("Retirado")
    REEMPLAZADO = "reemplazado", _("Reemplazado")
    FUERA_SERVICIO = "fuera_servicio", _("Fuera de servicio")

# ======================================================
# TIPO DE ORDEN DE TRABAJO
# ======================================================


class TipoOrdenTrabajoChoices(models.TextChoices):
    """
    Tipos de trabajos que puede gestionar una OT.
    """

    INSTALACION = (
        "INSTALACION",
        _("Instalación"),
    )

    MANTENIMIENTO = (
        "MANTENIMIENTO",
        _("Mantenimiento"),
    )

    REPARACION = (
        "REPARACION",
        _("Reparación"),
    )

    REINSTALACION = (
        "REINSTALACION",
        _("Reinstalación"),
    )

    DESINSTALACION = (
        "DESINSTALACION",
        _("Desinstalación"),
    )

    VISITA_TECNICA = (
        "VISITA_TECNICA",
        _("Visita técnica"),
    )

    INSPECCION = (
        "INSPECCION",
        _("Inspección"),
    )

    GARANTIA = (
        "GARANTIA",
        _("Garantía"),
    )


# ======================================================
# ESTADO DE ORDEN DE TRABAJO
# ======================================================


class EstadoOrdenTrabajoChoices(models.TextChoices):
    """
    Estados del ciclo de vida de una OT.
    """

    BORRADOR = (
        "BORRADOR",
        _("Borrador"),
    )

    PENDIENTE = (
        "PENDIENTE",
        _("Pendiente"),
    )

    PROGRAMADA = (
        "PROGRAMADA",
        _("Programada"),
    )

    EN_PROCESO = (
        "EN_PROCESO",
        _("En proceso"),
    )

    PAUSADA = (
        "PAUSADA",
        _("Pausada"),
    )

    FINALIZADA = (
        "FINALIZADA",
        _("Finalizada"),
    )

    CANCELADA = (
        "CANCELADA",
        _("Cancelada"),
    )


# ======================================================
# PRIORIDAD ORDEN DE TRABAJO
# ======================================================


class PrioridadOrdenTrabajoChoices(models.TextChoices):
    """
    Nivel de prioridad de la orden.
    """

    BAJA = (
        "BAJA",
        _("Baja"),
    )

    MEDIA = (
        "MEDIA",
        _("Media"),
    )

    ALTA = (
        "ALTA",
        _("Alta"),
    )

    URGENTE = (
        "URGENTE",
        _("Urgente"),
    )

# ======================================================
# PROPIEDADES DE PROYECTO
# ======================================================

class EstadoProyectoRequerimientoChoices(models.TextChoices):

    PENDIENTE = (
        "PENDIENTE",
        _("Pendiente"),
    )

    PARCIAL = (
        "PARCIAL",
        _("Parcial"),
    )

    COMPLETADO = (
        "COMPLETADO",
        _("Completado"),
    )

    CANCELADO = (
        "CANCELADO",
        _("Cancelado"),
    )


# ======================================================
# PROPIEDADES DE PRESUPUESTO
# ======================================================

class EstadoPresupuestoChoices(models.TextChoices):

    BORRADOR = (
        "BORRADOR",
        _("Borrador"),
    )

    ENVIADO = (
        "ENVIADO",
        _("Enviado"),
    )

    APROBADO = (
        "APROBADO",
        _("Aprobado"),
    )

    RECHAZADO = (
        "RECHAZADO",
        _("Rechazado"),
    )

    VENCIDO = (
        "VENCIDO",
        _("Vencido"),
    )

    CANCELADO = (
        "CANCELADO",
        _("Cancelado"),
    )

class TipoConceptoPresupuestoChoices(models.TextChoices):
    """
    Tipo de concepto del catálogo de presupuesto.
    """

    MANO_DE_OBRA = "MANO_DE_OBRA", _("Mano de obra")
    MATERIAL = "MATERIAL", _("Material")
    SERVICIO = "SERVICIO", _("Servicio")
    VIATICO = "VIATICO", _("Viático")

class TipoPresupuestoChoices(models.TextChoices):
    """
    Tipo de concepto del catálogo de presupuesto.
    """

    VENTA = "VENTA", _("Venta")
    AMPLIACIÓN = "AMPLIACIÓN", _("Ampliación")
    MANTENIMIENTO = "MANTENIMIENTO", _("Mantenimiento")
    REPARACIÓN = "REPARACIÓN", _("Reparación")
    ACTUALIZACIÓN = "ACTUALIZACIÓN", _("Actualización")

class TipoTrabajoPresupuestoChoices(models.TextChoices):
    """
    Tipo de trabajo realizado en un presupuesto de presupuesto.
    """

    INSTALACION = "INSTALACION", _("Instalación")
    DESINSTALACION = "DESINSTALACION", _("Desinstalación")
    REINSTALACION = "REINSTALACION", _("Reinstalación")

class UnidadMedidaChoices(models.TextChoices):
    """
    Unidades de medida disponibles para los conceptos comerciales.
    """

    UNIDAD = (
        "UN",
        _("Unidad"),
    )

    METRO = (
        "M",
        _("Metro"),
    )

    METRO_CUADRADO = (
        "M2",
        _("Metro cuadrado"),
    )

    METRO_CUBICO = (
        "M3",
        _("Metro cúbico"),
    )

    HORA = (
        "H",
        _("Hora"),
    )

    DIA = (
        "D",
        _("Día"),
    )

    MES = (
        "MES",
        _("Mes"),
    )

    SERVICIO = (
        "SER",
        _("Servicio"),
    )

    LICENCIA = (
        "LIC",
        _("Licencia"),
    )

    CAJA = (
        "CAJ",
        _("Caja"),
    )

    ROLLO = (
        "ROL",
        _("Rollo"),
    )

    KIT = (
        "KIT",
        _("Kit"),
    )

    LOTE = (
        "LOT",
        _("Lote"),
    )

class MonedaPresupuestoChoices(models.TextChoices):
    """
    Monedas soportadas por el sistema.
    """

    ARS = "ARS", _("Peso argentino")
    USD = "USD", _("Dólar estadounidense")
    EUR = "EUR", _("Euro")