from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import Proyecto, DetalleProyecto


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nombre",
        "sucursal",
        "estado",
        "fecha_inicio",
        "fecha_finalizacion",
        "is_active",
        "created_at",
    )

    search_fields = (
        "codigo",
        "nombre",
        "descripcion",
        "sucursal__nombre",
        "sucursal__codigo",
        "sucursal__cuenta_cliente__codigo",
        "sucursal__cuenta_cliente__nombre",
        "sucursal__cuenta_cliente__apellido",
        "sucursal__cuenta_cliente__razon_social",
    )

    list_filter = (
        "estado",
        "is_active",
    )

    ordering = (
        "-created_at",
    )

    autocomplete_fields = (
        "sucursal",
    )

@admin.register(DetalleProyecto)
class DetalleProyectoAdmin(admin.ModelAdmin):

    list_display = (
        "codigo",
        "proyecto",
        "modelo_dispositivo",
        "cantidad",
    )

    search_fields = (
        "codigo",
        "proyecto__nombre",
        "modelo_dispositivo__nombre",
    )

    list_filter = (
        "modelo_dispositivo__marca",
        "modelo_dispositivo__tipo_dispositivo",
    )

    ordering = (
        "proyecto",
    )

