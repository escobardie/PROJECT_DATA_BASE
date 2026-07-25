from django.contrib import admin

from .models import CategoriaSistema, Sistema


@admin.register(CategoriaSistema)
class CategoriaSistemaAdmin(admin.ModelAdmin):

    list_display = (
        "codigo",
        "nombre",
        "is_active",
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

@admin.register(Sistema)
class SistemaAdmin(admin.ModelAdmin):

    list_display = (
        "codigo",
        "categoria",
        "nombre",
        "disponible",
        "is_active",
    )

    search_fields = (
        "codigo",
        "nombre",
        "categoria__nombre",
    )

    list_filter = (
        "categoria",
        "disponible",
        "is_active",
    )

    ordering = (
        "categoria",
        "nombre",
    )