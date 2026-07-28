from django.contrib import admin

from .models import (
    CategoriaServicio,
    Servicio,
    ServicioContratado,
    CategoriaServicio,
    ServicioSistema,
)


@admin.register(CategoriaServicio)
class CategoriaServicioAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nombre",
        "is_active",
        "created_at",
    )

    search_fields = (
        "codigo",
        "nombre",
    )

    list_filter = (
        "is_active",
    )

    ordering = (
        "nombre",
    )

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nombre",
        "categoria",
        "precio_abono",
        "genera_abono",
        "is_active",
    )

    search_fields = (
        "codigo",
        "nombre",
        "categoria__nombre",
    )

    list_filter = (
        "categoria",
        "genera_abono",
        "requiere_dispositivos",
        "requiere_instalacion",
        "permite_facturacion",
        "is_active",
    )

    ordering = (
        "nombre",
    )

    list_select_related = (
        "categoria",
    )

@admin.register(ServicioContratado)
class ServicioContratadoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "servicio",
        "sucursal",
        "proyecto",
        "nombre_comercial",
        "fecha_alta",
        "precio_abono",
        "descuento_porcentaje",
        "mostrar_importe_final",
        "estado",
        "facturar",
        "is_active",
        "created_at",
    )

    search_fields = (
        "codigo",
        "nombre_comercial",
        "servicio__nombre",
        "sucursal__nombre",
        "sucursal__codigo",
        "sucursal__cuenta_cliente__codigo",
        "sucursal__cuenta_cliente__nombre",
        "sucursal__cuenta_cliente__apellido",
        "sucursal__cuenta_cliente__razon_social",
        "proyecto__codigo",
        "proyecto__nombre",
    )

    list_filter = (
        "estado",
        "facturar",
        "renovacion_automatica",
        "servicio",
        "is_active",
    )

    ordering = (
        "-fecha_alta",
        "nombre_comercial",
    )

    autocomplete_fields = (
        "sucursal",
        "servicio",
        "proyecto",
    )

    @admin.display(description="Importe final", ordering="precio_abono")
    def mostrar_importe_final(self, obj):
        return obj.importe_final

@admin.register(ServicioSistema)
class ServicioSistemaAdmin(admin.ModelAdmin):

    list_display = (
        "servicio",
        "sistema",
        "principal",
        "is_active",
    )

    search_fields = (
        "servicio__nombre",
        "sistema__nombre",
    )

    list_filter = (
        "principal",
        "sistema__categoria",
        "is_active",
    )

    ordering = (
        "servicio",
        "-principal",
    )

