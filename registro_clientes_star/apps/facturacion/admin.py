from django.contrib import admin

from .models import (
    Factura,
    DetalleFactura,
    Pago,
    NumeradorFactura,
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

    search_fields = (
        "codigo",
        "numero",
        "cuenta_cliente__nombre",
        "cuenta_cliente__apellido",
        "cuenta_cliente__razon_social",
        "cuenta_cliente__cuit",
    )

    list_filter = (
        "fecha_emision",
        "fecha_anulacion",
        "is_active",
    )

    readonly_fields = (
        "codigo",
        "numero",
        "numero_formateado",
        "total_pagado",
        "saldo_pendiente",
        "estado",
    )

    autocomplete_fields = (
        "cuenta_cliente",
        "sucursal",
    )

    date_hierarchy = "fecha_emision"

    ordering = (
        "-fecha_emision",
        "-numero",
    )


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

    list_display = (
        "codigo",
        "factura",
        "descripcion",
        "cantidad",
        "precio_unitario",
        "descuento",
        "subtotal",
    )

    search_fields = (
        "codigo",
        "descripcion",
        "factura__codigo",
    )

    readonly_fields = (
        "codigo",
        "subtotal",
    )

    autocomplete_fields = (
        "factura",
        "servicio_contratado",
    )

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