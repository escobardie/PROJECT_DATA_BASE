from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from apps.usuarios.models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """
    Administración de usuarios del sistema.

    El correo electrónico se utiliza como identificador
    para el inicio de sesión.
    """

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "email",
        "first_name",
        "last_name",
        "cargo",
        "mostrar_grupos",
        "cuenta_cliente",
        "sucursal",
        "is_staff",
        "is_active",
    )

    list_display_links = (
        "email",
        "first_name",
        "last_name",
    )

    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "groups",
        "cuenta_cliente",
        "sucursal",
    )

    search_fields = (
        "email",
        "first_name",
        "last_name",
        "telefono",
        "cargo",

        # Cuenta cliente
        "cuenta_cliente__codigo",
        "cuenta_cliente__razon_social",
        "cuenta_cliente__nombre",

        # Sucursal
        "sucursal__codigo",
        "sucursal__nombre",

        # Grupos
        "groups__name",
    )

    ordering = (
        "first_name",
        "last_name",
        "email",
    )

    empty_value_display = "-"

    save_on_top = True

    list_per_page = 25

    show_full_result_count = False

    # ======================================================
    # COLUMNAS PERSONALIZADAS
    # ======================================================

    @admin.display(
        description=_("Grupos"),
    )
    def mostrar_grupos(self, obj):
        """
        Muestra los grupos asignados al usuario.
        """

        grupos = getattr(
            obj,
            "_grupos_precargados",
            None,
        )

        if grupos is None:
            grupos = obj.groups.all()

        nombres = [
            grupo.name
            for grupo in grupos
        ]

        if not nombres:
            return "-"

        return ", ".join(nombres)

    # ======================================================
    # QUERYSET
    # ======================================================

    def get_queryset(self, request):
        """
        Optimiza las relaciones utilizadas
        en el listado del administrador.
        """

        return (
            super()
            .get_queryset(request)
            .select_related(
                "cuenta_cliente",
                "sucursal",
            )
            .prefetch_related(
                "groups",
            )
            .distinct()
        )

    # ======================================================
    # AUTOCOMPLETE
    # ======================================================

    autocomplete_fields = (
        "cuenta_cliente",
        "sucursal",
    )

    # ======================================================
    # CAMPOS DE SELECCIÓN MÚLTIPLE
    # ======================================================

    filter_horizontal = (
        "groups",
        "user_permissions",
    )

    # ======================================================
    # SOLO LECTURA
    # ======================================================

    readonly_fields = (
        "last_login",
        "date_joined",
    )

    # ======================================================
    # FORMULARIO DE EDICIÓN
    # ======================================================

    fieldsets = (
        (
            _("Autenticación"),
            {
                "fields": (
                    "email",
                    "password",
                ),
            },
        ),
        (
            _("Información personal"),
            {
                "fields": (
                    (
                        "first_name",
                        "last_name",
                    ),
                    (
                        "telefono",
                        "cargo",
                    ),
                    "observaciones",
                ),
            },
        ),
        (
            _("Alcance del usuario cliente"),
            {
                "fields": (
                    (
                        "cuenta_cliente",
                        "sucursal",
                    ),
                ),
                "description": _(
                    "Estos campos delimitan los datos visibles "
                    "para usuarios asociados a clientes. "
                    "Deben permanecer vacíos para usuarios internos."
                ),
            },
        ),
        (
            _("Roles y permisos"),
            {
                "fields": (
                    "groups",
                    "user_permissions",
                ),
                "description": _(
                    "Los roles funcionales se asignan mediante grupos. "
                    "Los permisos individuales deben utilizarse "
                    "solamente para excepciones concretas."
                ),
            },
        ),
        (
            _("Estado y acceso"),
            {
                "fields": (
                    (
                        "is_active",
                        "is_staff",
                        "is_superuser",
                    ),
                ),
            },
        ),
        (
            _("Fechas importantes"),
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "last_login",
                    "date_joined",
                ),
            },
        ),
    )

    # ======================================================
    # FORMULARIO DE CREACIÓN
    # ======================================================

    add_fieldsets = (
        (
            _("Autenticación"),
            {
                "classes": (
                    "wide",
                ),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                ),
            },
        ),
        (
            _("Información personal"),
            {
                "classes": (
                    "wide",
                ),
                "fields": (
                    (
                        "first_name",
                        "last_name",
                    ),
                    (
                        "telefono",
                        "cargo",
                    ),
                    "observaciones",
                ),
            },
        ),
        (
            _("Alcance del usuario cliente"),
            {
                "classes": (
                    "wide",
                ),
                "fields": (
                    (
                        "cuenta_cliente",
                        "sucursal",
                    ),
                ),
            },
        ),
        (
            _("Roles"),
            {
                "classes": (
                    "wide",
                ),
                "fields": (
                    "groups",
                ),
            },
        ),
        (
            _("Estado y acceso"),
            {
                "classes": (
                    "wide",
                ),
                "fields": (
                    (
                        "is_active",
                        "is_staff",
                    ),
                ),
            },
        ),
    )

    # ======================================================
    # ACCIONES
    # ======================================================

    actions = (
        "activar_usuarios",
        "desactivar_usuarios",
    )

    @admin.action(
        description=_("Activar usuarios seleccionados"),
    )
    def activar_usuarios(self, request, queryset):
        """
        Activa los usuarios seleccionados.
        """

        actualizados = queryset.update(
            is_active=True,
        )

        self.message_user(
            request,
            _(
                "%(cantidad)s usuario(s) activado(s)."
            )
            % {
                "cantidad": actualizados,
            },
        )

    @admin.action(
        description=_("Desactivar usuarios seleccionados"),
    )
    def desactivar_usuarios(self, request, queryset):
        """
        Desactiva los usuarios seleccionados.

        El usuario actual no puede desactivarse
        mediante esta acción.
        """

        queryset = queryset.exclude(
            pk=request.user.pk,
        )

        actualizados = queryset.update(
            is_active=False,
        )

        self.message_user(
            request,
            _(
                "%(cantidad)s usuario(s) desactivado(s)."
            )
            % {
                "cantidad": actualizados,
            },
        )