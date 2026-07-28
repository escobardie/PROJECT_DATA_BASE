from django.contrib import admin

from .models import (
    Factura,
    DetalleFactura,
    Pago,
    NumeradorFactura,
)


# ======================================================
# INLINE DETALLES
# ======================================================

class DetalleFacturaInline(admin.TabularInline):
    model = DetalleFactura

    extra = 1

    fields = (
        "servicio_contratado",
        "concepto",
        "descripcion",
        "cantidad",
        "precio_unitario",
        "descuento",
        "subtotal",
    )

    readonly_fields = (
        "subtotal",
    )


# ======================================================
# INLINE PAGOS
# ======================================================

class PagoInline(admin.TabularInline):
    model = Pago

    extra = 0

    fields = (
        "fecha",
        "importe",
        "medio_pago",
        "numero_comprobante",
        "observaciones",
    )


# ======================================================
# NUMERADOR FACTURA
# ======================================================

@admin.register(NumeradorFactura)
class NumeradorFacturaAdmin(admin.ModelAdmin):

    list_display = (
        "punto_venta",
        "ultimo_numero",
        "activo",
    )

    search_fields = (
        "punto_venta",
    )

    list_filter = (
        "activo",
    )

    ordering = (
        "punto_venta",
    )


# ======================================================
# FACTURA
# ======================================================

@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):

    # --------------------------------------------------
    # LISTADO
    # --------------------------------------------------

    list_display = (
        "codigo",
        "numero_formateado",
        "cuenta_cliente",
        "sucursal",
        "fecha_emision",
        "total",
        "mostrar_estado",
        "mostrar_saldo",
        "is_active",
    )


    # --------------------------------------------------
    # BÚSQUEDA
    # --------------------------------------------------

    search_fields = (
        "codigo",
        "numero",
        "cuenta_cliente__nombre",
        "cuenta_cliente__apellido",
        "cuenta_cliente__razon_social",
        "cuenta_cliente__cuit",
        "sucursal__nombre",
    )


    # --------------------------------------------------
    # FILTROS
    # --------------------------------------------------

    list_filter = (
        "fecha_emision",
        "fecha_anulacion",
        "punto_venta",
        "is_active",
    )


    # --------------------------------------------------
    # CAMPOS SOLO LECTURA
    # --------------------------------------------------

    readonly_fields = (
        "codigo",
        "numero",
        "total",
        "numero_formateado",
        "estado",
        "total_pagado",
        "saldo_pendiente",
        "fecha_emision",
        "fecha_anulacion",
    )


    # --------------------------------------------------
    # RELACIONES
    # --------------------------------------------------

    autocomplete_fields = (
        "cuenta_cliente",
        "sucursal",
    )


    # --------------------------------------------------
    # INLINE
    # --------------------------------------------------

    inlines = (
        DetalleFacturaInline,
        PagoInline,
    )


    # --------------------------------------------------
    # ORDENAMIENTO
    # --------------------------------------------------

    ordering = (
        "-created_at",
    )


    # --------------------------------------------------
    # MÉTODOS VISUALES
    # --------------------------------------------------

    @admin.display(
        description="Estado"
    )
    def mostrar_estado(self, obj):
        return obj.estado


    @admin.display(
        description="Saldo pendiente"
    )
    def mostrar_saldo(self, obj):
        return obj.saldo_pendiente

# ======================================================
# DETALLE FACTURA
# ======================================================

@admin.register(DetalleFactura)
class DetalleFacturaAdmin(admin.ModelAdmin):

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "factura",
        "concepto",
        "codigo_servicio",
        "cantidad",
        "precio_unitario",
        "descuento",
        "subtotal",
    )


    # ======================================================
    # BÚSQUEDA
    # ======================================================

    search_fields = (
        "concepto",
        "codigo_servicio",
        "descripcion",
        "factura__codigo",
        "factura__numero",
        "servicio_contratado__codigo",
    )


    # ======================================================
    # FILTROS
    # ======================================================

    list_filter = (
        "factura__fecha_emision",
    )


    # ======================================================
    # CAMPOS SOLO LECTURA
    # ======================================================

    readonly_fields = (
        "codigo_servicio",
        "subtotal",
    )


    # ======================================================
    # RELACIONES
    # ======================================================

    autocomplete_fields = (
        "factura",
        "servicio_contratado",
    )


    # ======================================================
    # ORDENAMIENTO
    # ======================================================

    ordering = (
        "factura",
        "id",
    )

# ======================================================
# PAGO
# ======================================================

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):

    list_display = (
        "codigo",
        "factura",
        "fecha",
        "importe",
        "medio_pago",
        "numero_comprobante",
    )

    search_fields = (
        "codigo",
        "factura__codigo",
        "numero_comprobante",
    )

    list_filter = (
        "medio_pago",
        "fecha",
    )

    autocomplete_fields = (
        "factura",
    )

    readonly_fields = (
        "codigo",
    )

    date_hierarchy = "fecha"

    ordering = (
        "-fecha",
    )