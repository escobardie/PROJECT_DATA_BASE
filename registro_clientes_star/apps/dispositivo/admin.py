from django.contrib import admin

from .models import TipoDispositivo, Marca, ModeloDispositivo, Dispositivo


@admin.register(TipoDispositivo)
class TipoDispositivoAdmin(admin.ModelAdmin):
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

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nombre",
        "sitio_web",
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

@admin.register(ModeloDispositivo)
class ModeloDispositivoAdmin(admin.ModelAdmin):

    list_display = (
        "codigo",
        "marca",
        "nombre",
        "tipo_dispositivo",
        "url_datas_heet",
        "fabricado",
        "is_active",
    )

    search_fields = (
        "codigo",
        "nombre",
        "marca__nombre",
        "fabricante_codigo",
        "ean",
    )

    list_filter = (
        "marca",
        "tipo_dispositivo",
        "fabricado",
        "is_active",
    )

    ordering = (
        "marca",
        "nombre",
    )

@admin.register(Dispositivo)
class DispositivoAdmin(admin.ModelAdmin):

    list_display = (
        "codigo",
        "modelo",
        "numero_serie",
        "servicio_contratado",
        "estado",
    )

    search_fields = (
        "codigo",
        "numero_serie",
        "codigo_interno",
        "modelo__nombre",
    )

    list_filter = (
        "estado",
        "modelo__marca",
        "modelo__tipo_dispositivo",
    )

    ordering = (
        "modelo",
        "numero_serie",
    )
