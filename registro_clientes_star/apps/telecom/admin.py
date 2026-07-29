from django.contrib import admin

from .models import (
    ZonaTelecom,
    ConceptoTelecom,
    RecargoTelecom,
    PresupuestoTelecom,
    DetallePresupuestoTelecom,
)


# ======================================================
# ZONA
# ======================================================

@admin.register(ZonaTelecom)
class ZonaTelecomAdmin(admin.ModelAdmin):

    list_display = (
        "codigo",
        "provincia",
        "region",
        "ciudad_cabecera",
        "factor_multiplicador",
        "is_active",
    )

    search_fields = (
        "codigo",
        "provincia",
        "region",
        "ciudad_cabecera",
    )

    list_filter = (
        "region",
        "is_active",
    )

    readonly_fields = (
        "codigo",
    )

    ordering = (
        "provincia",
    )


# ======================================================
# CONCEPTO
# ======================================================

@admin.register(ConceptoTelecom)
class ConceptoTelecomAdmin(admin.ModelAdmin):

    list_display = (
        "codigo",
        "nombre",
        "tipo",
        "moneda",
        "precio_unitario",
        "is_active",
    )

    search_fields = (
        "codigo",
        "nombre",
        "descripcion",
    )

    list_filter = (
        "tipo",
        "moneda",
        "is_active",
    )

    readonly_fields = (
        "codigo",
    )

    ordering = (
        "tipo",
        "nombre",
    )


# ======================================================
# RECARGO
# ======================================================

@admin.register(RecargoTelecom)
class RecargoTelecomAdmin(admin.ModelAdmin):

    list_display = (
        "codigo",
        "tipo",
        "factor",
        "is_active",
    )

    search_fields = (
        "codigo",
    )

    list_filter = (
        "is_active",
    )

    readonly_fields = (
        "codigo",
    )

    ordering = (
        "tipo",
    )


# ======================================================
# INLINE DETALLE
# ======================================================

class DetallePresupuestoTelecomInline(admin.TabularInline):
    model = DetallePresupuestoTelecom

    extra = 1

    fields = (
        "concepto",
        "cantidad",
        "precio_unitario",
        "subtotal",
    )

    readonly_fields = (
        "precio_unitario",
        "subtotal",
    )

    autocomplete_fields = (
        "concepto",
    )


# ======================================================
# PRESUPUESTO
# ======================================================

@admin.register(PresupuestoTelecom)
class PresupuestoTelecomAdmin(admin.ModelAdmin):

    list_display = (
        "codigo",
        "sitio_obra",
        "zona",
        "tipo_trabajo",
        "fecha_solicitud",
        "subtotal_mano_obra",
        "mostrar_total_mano_obra_ajustado",
        "subtotal_materiales",
        "is_active",
    )

    search_fields = (
        "codigo",
        "sitio_obra",
        "zona__provincia",
    )

    list_filter = (
        "tipo_trabajo",
        "zona",
        "fecha_solicitud",
        "is_active",
    )

    readonly_fields = (
        "codigo",
        "factor_multiplicador_zona",
        "factor_recargo",
        "subtotal_mano_obra",
        "subtotal_materiales",
        "mostrar_total_mano_obra_ajustado",
    )

    autocomplete_fields = (
        "zona",
        "recargo",
    )

    inlines = (
        DetallePresupuestoTelecomInline,
    )

    ordering = (
        "-fecha_solicitud",
    )

    @admin.display(
        description="Mano de obra ajustada (ARS)"
    )
    def mostrar_total_mano_obra_ajustado(self, obj):
        return obj.total_mano_obra_ajustado


# ======================================================
# DETALLE (registro independiente, además del inline)
# ======================================================

@admin.register(DetallePresupuestoTelecom)
class DetallePresupuestoTelecomAdmin(admin.ModelAdmin):

    list_display = (
        "presupuesto",
        "nombre_concepto",
        "tipo",
        "moneda",
        "cantidad",
        "precio_unitario",
        "subtotal",
    )

    search_fields = (
        "nombre_concepto",
        "presupuesto__codigo",
        "concepto__codigo",
    )

    list_filter = (
        "tipo",
        "moneda",
    )

    readonly_fields = (
        "nombre_concepto",
        "tipo",
        "moneda",
        "precio_unitario",
        "subtotal",
    )

    autocomplete_fields = (
        "presupuesto",
        "concepto",
    )

    ordering = (
        "presupuesto",
        "id",
    )
