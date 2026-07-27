from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """
    Administración de usuarios del sistema.
    """

    list_display = (
        "email",
        "first_name",
        "last_name",
        "cuenta_cliente",
        "sucursal",
        "is_staff",
        "is_active",
    )

    search_fields = (
        "email",
        "first_name",
        "last_name",
        "telefono",
        "cargo",
        "cuenta_cliente__codigo",
        "cuenta_cliente__razon_social",
        "cuenta_cliente__nombre",
        "sucursal__nombre",
    )

    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "groups",
        "cuenta_cliente",
    )

    ordering = (
        "first_name",
        "last_name",
    )

    autocomplete_fields = (
        "cuenta_cliente",
        "sucursal",
    )

    list_select_related = (
        "cuenta_cliente",
        "sucursal",
    )

    fieldsets = (
        (
            "Autenticación",
            {
                "fields": (
                    "email",
                    "password",
                )
            },
        ),
        (
            "Información personal",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "telefono",
                    "cargo",
                )
            },
        ),
        (
            "Cliente",
            {
                "fields": (
                    "cuenta_cliente",
                    "sucursal",
                )
            },
        ),
        (
            "Permisos",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Fechas importantes",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                )
            },
        ),
        (
            "Información adicional",
            {
                "fields": (
                    "observaciones",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "telefono",
                    "cargo",
                    "cuenta_cliente",
                    "sucursal",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )