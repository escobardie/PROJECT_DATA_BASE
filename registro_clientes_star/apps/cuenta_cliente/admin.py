from django.contrib import admin

from .models import CuentaCliente, Sucursal


@admin.register(CuentaCliente)
class CuentaClienteAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "tipo_cliente",
        "nombre_mostrar",
        "telefono",
        "celular",
        "email",
        "is_active",
        "created_at",
    )

    search_fields = (
        "codigo",
        "nombre",
        "apellido",
        "razon_social",
        "dni",
        "cuit",
        "telefono",
        "celular",
        "email",
    )

    list_filter = (
        "tipo_cliente",
        "is_active",
    )

    ordering = (
        "codigo",
    )

    @admin.display(description="Cliente")
    def nombre_mostrar(self, obj):
        if obj.razon_social:
            return obj.razon_social
        return f"{obj.apellido or ''}, {obj.nombre or ''}".strip(", ")
    

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nombre",
        "cuenta_cliente",
        "ciudad",
        "provincia",
        "telefono",
        "is_active",
        "created_at",
    )

    search_fields = (
        "codigo",
        "nombre",
        "cuenta_cliente__codigo",
        "cuenta_cliente__nombre",
        "cuenta_cliente__apellido",
        "cuenta_cliente__razon_social",
        "ciudad",
        "provincia",
        "telefono",
        "email",
    )

    list_filter = (
        "provincia",
        "ciudad",
        "is_active",
    )

    ordering = (
        "codigo",
    )
