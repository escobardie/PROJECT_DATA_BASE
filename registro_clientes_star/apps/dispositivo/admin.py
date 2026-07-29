from django.contrib import admin, messages

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
        "mostrar_estado_aprobacion",
    )

    search_fields = (
        "codigo",
        "numero_serie",
        "codigo_interno",
        "modelo__nombre",
    )

    list_filter = (
        "estado",
        "estado_aprobacion",
        "modelo__marca",
        "modelo__tipo_dispositivo",
    )

    readonly_fields = (
        "codigo",
        "estado_aprobacion",
        "aprobado_por",
        "fecha_aprobacion",
        "motivo_rechazo",
    )

    ordering = (
        "modelo",
        "numero_serie",
    )

    # --------------------------------------------------
    # ACCIONES
    # --------------------------------------------------

    actions = (
        "accion_aprobar",
        "accion_rechazar",
    )

    def get_actions(self, request):
        """
        Oculta las acciones de aprobación/rechazo del
        desplegable si el usuario no es staff.
        """

        actions = super().get_actions(request)

        if not request.user.is_staff:
            actions.pop("accion_aprobar", None)
            actions.pop("accion_rechazar", None)

        return actions

    @admin.action(description="Aprobar dispositivos seleccionados")
    def accion_aprobar(self, request, queryset):
        if not request.user.is_staff:
            self.message_user(
                request,
                "No tenés permiso para aprobar dispositivos.",
                level=messages.ERROR,
            )
            return

        aprobados = 0

        for dispositivo in queryset:
            dispositivo.aprobar(usuario=request.user)
            aprobados += 1

        self.message_user(
            request,
            f"{aprobados} dispositivo(s) aprobado(s).",
            level=messages.SUCCESS,
        )

    @admin.action(description="Rechazar dispositivos seleccionados")
    def accion_rechazar(self, request, queryset):
        if not request.user.is_staff:
            self.message_user(
                request,
                "No tenés permiso para rechazar dispositivos.",
                level=messages.ERROR,
            )
            return

        rechazados = 0

        for dispositivo in queryset:
            dispositivo.rechazar(
                usuario=request.user,
                motivo="Rechazado desde el admin.",
            )
            rechazados += 1

        self.message_user(
            request,
            f"{rechazados} dispositivo(s) rechazado(s).",
            level=messages.WARNING,
        )

    # --------------------------------------------------
    # MÉTODOS VISUALES
    # --------------------------------------------------

    @admin.display(description="Aprobación")
    def mostrar_estado_aprobacion(self, obj):
        return obj.get_estado_aprobacion_display()
