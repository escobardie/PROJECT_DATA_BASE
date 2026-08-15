from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Prefetch
from django.http import (
    HttpResponseNotAllowed,
    HttpResponseRedirect,
)
from django.utils.html import format_html
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _

from apps.instalacion.models import (
    Instalacion,
    InstalacionTecnico,
)

from apps.instalacion.services import (
    cargar_dispositivos_desde_proyecto,
    cancelar_instalacion,
    finalizar_instalacion,
    iniciar_instalacion,
    programar_instalacion,
    registrar_conformidad_instalacion,
)

from apps.usuarios.permissions import (
    puede_cancelar_instalacion_concreta,
    puede_finalizar_instalacion_concreta,
    puede_iniciar_instalacion_concreta,
    puede_programar_instalacion_concreta,
    puede_registrar_conformidad_instalacion,
)

from .instalacion_dispositivo import (
    InstalacionDispositivoInline,
)
from .instalacion_tecnico import (
    InstalacionTecnicoInline,
)


@admin.register(Instalacion)
class InstalacionAdmin(admin.ModelAdmin):
    """
    Administración de instalaciones.

    Una instalación representa el resultado técnico
    de una orden de trabajo.

    Su ciclo de vida se gestiona mediante:

        Admin
            ↓
        Permissions
            ↓
        Services
            ↓
        Models

    El estado se modifica exclusivamente mediante
    services.

    Las fechas permanecen editables para permitir
    registrar la trazabilidad real.
    """

    # ======================================================
    # TEMPLATE
    # ======================================================

    change_form_template = (
        "admin/instalacion/"
        "instalacion/change_form.html"
    )

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "codigo",
        "orden_trabajo",
        "mostrar_origen",
        "estado",
        "prioridad",
        "fecha_programada",
        "responsable",
        "cantidad_dispositivos",
        "mostrar_conformidad",
        "mostrar_vencida",
        "created_at",
        "is_active",
    )

    list_display_links = (
        "codigo",
        "orden_trabajo",
    )

    list_filter = (
        "estado",
        "prioridad",
        "fecha_programada",
        "orden_trabajo__tipo",
        "orden_trabajo__estado",
        "is_active",
    )

    search_fields = (
        "codigo",

        # Orden de trabajo
        "orden_trabajo__codigo",
        "orden_trabajo__titulo",
        "orden_trabajo__descripcion",

        # Sucursal
        "orden_trabajo__sucursal__nombre",
        "orden_trabajo__sucursal__cuenta_cliente__nombre",

        # Proyecto
        "orden_trabajo__proyecto__codigo",
        "orden_trabajo__proyecto__nombre",

        # Servicio contratado
        "orden_trabajo__servicio_contratado__codigo",

        # Presupuesto Telecom
        "orden_trabajo__presupuesto_telecom__codigo",

        # Técnicos
        "tecnicos__usuario__email",
        "tecnicos__usuario__first_name",
        "tecnicos__usuario__last_name",

        # Dispositivos físicos instalados
        "dispositivos__codigo",
        "dispositivos__numero_serie",
        "dispositivos__direccion_mac",
        "dispositivos__direccion_ip",
        "dispositivos__ubicacion",

        # Producto del catálogo
        "dispositivos__dispositivo__codigo",
        "dispositivos__dispositivo__nombre_comercial",
        "dispositivos__dispositivo__modelo__nombre",
        "dispositivos__dispositivo__modelo__marca__nombre",
    )

    ordering = (
        "-fecha_programada",
        "-created_at",
    )

    empty_value_display = "-"

    save_on_top = True

    save_as = False

    list_per_page = 25

    show_full_result_count = False

    # ======================================================
    # COLUMNAS PERSONALIZADAS
    # ======================================================

    @admin.display(
        description=_("Origen"),
    )
    def mostrar_origen(self, obj):
        """
        Muestra el origen principal de la OT.
        """

        orden = obj.orden_trabajo

        if orden.proyecto_id:
            return orden.proyecto

        if orden.servicio_contratado_id:
            return orden.servicio_contratado

        if orden.presupuesto_telecom_id:
            return orden.presupuesto_telecom

        if orden.sucursal_id:
            return orden.sucursal

        return "-"

    @admin.display(
        description=_("Responsable"),
    )
    def responsable(self, obj):
        """
        Devuelve el técnico responsable principal
        de la instalación.
        """

        responsables = getattr(
            obj,
            "_responsables_prefetched",
            (),
        )

        if responsables:
            return responsables[0].usuario

        return "-"

    @admin.display(
        description=_("Dispositivos"),
        ordering="_cantidad_dispositivos",
    )
    def cantidad_dispositivos(self, obj):
        """
        Devuelve la cantidad de dispositivos
        registrados en la instalación.
        """

        return obj._cantidad_dispositivos

    @admin.display(
        boolean=True,
        description=_("Conf."),
    )
    def mostrar_conformidad(self, obj):
        """
        Indica si existe conformidad registrada.
        """

        return obj.fecha_conformidad is not None

    @admin.display(
        boolean=True,
        description=_("Vencida"),
    )
    def mostrar_vencida(self, obj):
        """
        Indica si la instalación está vencida.
        """

        return obj.esta_vencida

    # ======================================================
    # INFORMACIÓN DERIVADA
    # ======================================================

    @admin.display(
        description=_("Orden de trabajo"),
    )
    def mostrar_orden_trabajo(self, obj):
        """
        Muestra la OT asociada como enlace directo
        a su formulario en el Admin.
        """

        if not obj or not obj.pk:
            return "-"

        orden = obj.orden_trabajo

        if not orden:
            return "-"

        url = reverse(
            "admin:orden_trabajo_ordentrabajo_change",
            args=(orden.pk,),
            current_app=self.admin_site.name,
        )

        return format_html(
            '<a href="{}">{}</a>',
            url,
            orden,
        )


    # ======================================================
    # QUERYSET
    # ======================================================

    def get_queryset(self, request):
        """
        Optimiza las relaciones y valores utilizados
        por el administrador.
        """

        responsables = (
            InstalacionTecnico.objects
            .filter(
                es_responsable=True,
            )
            .select_related(
                "usuario",
            )
        )

        return (
            super()
            .get_queryset(request)
            .select_related(
                "orden_trabajo",
                "orden_trabajo__sucursal",
                "orden_trabajo__sucursal__cuenta_cliente",
                "orden_trabajo__proyecto",
                "orden_trabajo__servicio_contratado",
                "orden_trabajo__presupuesto_telecom",
                "orden_trabajo__responsable",
            )
            .prefetch_related(
                Prefetch(
                    "tecnicos",
                    queryset=responsables,
                    to_attr="_responsables_prefetched",
                ),
            )
            .annotate(
                _cantidad_dispositivos=Count(
                    "dispositivos",
                    distinct=True,
                ),
            )
            .distinct()
        )

    # ======================================================
    # AUTOCOMPLETE
    # ======================================================

    autocomplete_fields = (
        "orden_trabajo",
    )

    # ======================================================
    # SOLO LECTURA
    # ======================================================

    readonly_fields = (
        "codigo",
        "mostrar_orden_trabajo",
        "mostrar_proyecto",
        "mostrar_sucursal",
        "mostrar_servicio_contratado",
        "mostrar_presupuesto_telecom",
        "created_at",
        "updated_at",

    )

    def get_readonly_fields(
        self,
        request,
        obj=None,
    ):
        """
        El estado se modifica exclusivamente
        mediante services.

        Las fechas permanecen editables para permitir
        registrar la fecha real de cada operación.
        """

        campos = list(
            super().get_readonly_fields(
                request,
                obj,
            )
        )

        if obj and obj.pk:
            campos.extend(
                (
                    "estado",
                    "orden_trabajo",
                )
            )

        return tuple(
            dict.fromkeys(
                campos
            )
        )

    # ======================================================
    # INFORMACIÓN DERIVADA
    # ======================================================

    @admin.display(
        description=_("Proyecto"),
    )
    def mostrar_proyecto(self, obj):
        if not obj or not obj.pk:
            return "-"

        return obj.proyecto or "-"

    @admin.display(
        description=_("Sucursal"),
    )
    def mostrar_sucursal(self, obj):
        if not obj or not obj.pk:
            return "-"

        return obj.sucursal or "-"

    @admin.display(
        description=_("Servicio contratado"),
    )
    def mostrar_servicio_contratado(self, obj):
        if not obj or not obj.pk:
            return "-"

        return obj.servicio_contratado or "-"

    @admin.display(
        description=_("Presupuesto Telecom"),
    )
    def mostrar_presupuesto_telecom(self, obj):
        if not obj or not obj.pk:
            return "-"

        return obj.presupuesto_telecom or "-"

    # ======================================================
    # FORMULARIO
    # ======================================================

    fieldsets = (
        (
            _("Información general"),
            {
                "fields": (
                    "codigo",
                    "mostrar_orden_trabajo",
                    (
                        "estado",
                        "prioridad",
                    ),
                    "is_active",
                ),
            },
        ),
        (
            _("Origen de la orden"),
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "mostrar_proyecto",
                    "mostrar_sucursal",
                    "mostrar_servicio_contratado",
                    "mostrar_presupuesto_telecom",
                ),
            },
        ),
        (
            _("Planificación"),
            {
                "fields": (
                    (
                        "fecha_programada",
                        "duracion_estimada",
                    ),
                ),
            },
        ),
        (
            _("Ejecución"),
            {
                "fields": (
                    (
                        "fecha_inicio",
                        "fecha_finalizacion",
                    ),
                ),
            },
        ),
        (
            _("Conformidad"),
            {
                "fields": (
                    "recibido_por",
                    "fecha_conformidad",
                    "observaciones_conformidad",
                ),
                "description": _(
                    "La conformidad se registra una vez "
                    "finalizada la instalación."
                ),
            },
        ),
        (
            _("Observaciones"),
            {
                "fields": (
                    "observaciones",
                ),
            },
        ),
        (
            _("Auditoría"),
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    # ======================================================
    # INLINES
    # ======================================================

    inlines = (
        InstalacionTecnicoInline,
        InstalacionDispositivoInline,
    )

    # ======================================================
    # URLS PERSONALIZADAS
    # ======================================================

    def get_urls(self):
        """
        Agrega endpoints para gestionar el ciclo
        de vida de la instalación.
        """

        urls = super().get_urls()

        custom_urls = [
            path(
                "<path:object_id>/programar/",
                self.admin_site.admin_view(
                    self.programar_view
                ),
                name=(
                    "instalacion_instalacion_"
                    "programar"
                ),
            ),
            path(
                "<path:object_id>/iniciar/",
                self.admin_site.admin_view(
                    self.iniciar_view
                ),
                name=(
                    "instalacion_instalacion_"
                    "iniciar"
                ),
            ),
            path(
                "<path:object_id>/finalizar/",
                self.admin_site.admin_view(
                    self.finalizar_view
                ),
                name=(
                    "instalacion_instalacion_"
                    "finalizar"
                ),
            ),
            path(
                "<path:object_id>/cancelar/",
                self.admin_site.admin_view(
                    self.cancelar_view
                ),
                name=(
                    "instalacion_instalacion_"
                    "cancelar"
                ),
            ),
            path(
                "<path:object_id>/registrar-conformidad/",
                self.admin_site.admin_view(
                    self.registrar_conformidad_view
                ),
                name=(
                    "instalacion_instalacion_"
                    "registrar_conformidad"
                ),
            ),
            path(
                "<path:object_id>/importar-dispositivos-proyecto/",
                self.admin_site.admin_view(
                    self.importar_dispositivos_proyecto_view
                ),
                name=(
                    "instalacion_instalacion_"
                    "importar_dispositivos_proyecto"
                ),
            ),
        ]

        return custom_urls + urls

    # ======================================================
    # AUXILIARES
    # ======================================================

    def _redirect_change(
        self,
        obj,
    ):
        """
        Redirige nuevamente al formulario
        de la instalación.
        """

        url = reverse(
            "admin:instalacion_instalacion_change",
            args=(
                obj.pk,
            ),
            current_app=self.admin_site.name,
        )

        return HttpResponseRedirect(
            url
        )

    def _redirect_changelist(self):
        """
        Redirige al listado de instalaciones.
        """

        url = reverse(
            "admin:instalacion_instalacion_changelist",
            current_app=self.admin_site.name,
        )

        return HttpResponseRedirect(
            url
        )

    def _obtener_objeto(
        self,
        request,
        object_id,
    ):
        """
        Obtiene la instalación según el alcance
        del administrador.
        """

        return self.get_object(
            request,
            object_id,
        )

    def _validar_post(self, request):
        """
        Las operaciones de escritura solamente
        pueden ejecutarse mediante POST.
        """

        if request.method != "POST":
            return HttpResponseNotAllowed(
                [
                    "POST",
                ]
            )

        return None

    def _mostrar_error(
        self,
        request,
        exc,
    ):
        """
        Convierte ValidationError en un mensaje
        visible del Admin.
        """

        if hasattr(exc, "messages"):
            mensaje = " ".join(
                str(item)
                for item in exc.messages
            )
        else:
            mensaje = str(exc)

        self.message_user(
            request,
            mensaje,
            level=messages.ERROR,
        )

    # ======================================================
    # PROGRAMACIÓN
    # ======================================================

    def programar_view(
        self,
        request,
        object_id,
    ):
        respuesta = self._validar_post(
            request
        )

        if respuesta:
            return respuesta

        obj = self._obtener_objeto(
            request,
            object_id,
        )

        if obj is None:
            return self._redirect_changelist()

        if not puede_programar_instalacion_concreta(
            request.user,
            obj,
        ):
            self.message_user(
                request,
                _(
                    "La instalación no puede programarse "
                    "en su estado actual."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(
                obj
            )

        try:
            programar_instalacion(
                instalacion=obj,
                fecha_programada=(
                    obj.fecha_programada
                ),
                duracion_estimada=(
                    obj.duracion_estimada
                ),
            )

        except ValidationError as exc:
            self._mostrar_error(
                request,
                exc,
            )

        else:
            self.message_user(
                request,
                _(
                    "Instalación programada correctamente."
                ),
                level=messages.SUCCESS,
            )

        return self._redirect_change(
            obj
        )

    # ======================================================
    # INICIO
    # ======================================================

    def iniciar_view(
        self,
        request,
        object_id,
    ):
        respuesta = self._validar_post(
            request
        )

        if respuesta:
            return respuesta

        obj = self._obtener_objeto(
            request,
            object_id,
        )

        if obj is None:
            return self._redirect_changelist()

        if not puede_iniciar_instalacion_concreta(
            request.user,
            obj,
        ):
            self.message_user(
                request,
                _(
                    "La instalación no puede iniciarse "
                    "en su estado actual."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(
                obj
            )

        try:
            iniciar_instalacion(
                instalacion=obj,
            )

        except ValidationError as exc:
            self._mostrar_error(
                request,
                exc,
            )

        else:
            self.message_user(
                request,
                _(
                    "Instalación iniciada correctamente."
                ),
                level=messages.SUCCESS,
            )

        return self._redirect_change(
            obj
        )

    # ======================================================
    # FINALIZACIÓN
    # ======================================================

    def finalizar_view(
        self,
        request,
        object_id,
    ):
        respuesta = self._validar_post(
            request
        )

        if respuesta:
            return respuesta

        obj = self._obtener_objeto(
            request,
            object_id,
        )

        if obj is None:
            return self._redirect_changelist()

        if not puede_finalizar_instalacion_concreta(
            request.user,
            obj,
        ):
            self.message_user(
                request,
                _(
                    "La instalación todavía no cumple "
                    "las condiciones para finalizarse."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(
                obj
            )

        try:
            finalizar_instalacion(
                instalacion=obj,
            )

        except ValidationError as exc:
            self._mostrar_error(
                request,
                exc,
            )

        else:
            self.message_user(
                request,
                _(
                    "Instalación finalizada correctamente."
                ),
                level=messages.SUCCESS,
            )

        return self._redirect_change(
            obj
        )

    # ======================================================
    # CANCELACIÓN
    # ======================================================

    def cancelar_view(
        self,
        request,
        object_id,
    ):
        respuesta = self._validar_post(
            request
        )

        if respuesta:
            return respuesta

        obj = self._obtener_objeto(
            request,
            object_id,
        )

        if obj is None:
            return self._redirect_changelist()

        if not puede_cancelar_instalacion_concreta(
            request.user,
            obj,
        ):
            self.message_user(
                request,
                _(
                    "La instalación no puede cancelarse "
                    "en su estado actual."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(
                obj
            )

        try:
            cancelar_instalacion(
                instalacion=obj,
            )

        except ValidationError as exc:
            self._mostrar_error(
                request,
                exc,
            )

        else:
            self.message_user(
                request,
                _(
                    "Instalación cancelada correctamente."
                ),
                level=messages.SUCCESS,
            )

        return self._redirect_change(
            obj
        )

    # ======================================================
    # CONFORMIDAD
    # ======================================================

    def registrar_conformidad_view(
        self,
        request,
        object_id,
    ):
        respuesta = self._validar_post(
            request
        )

        if respuesta:
            return respuesta

        obj = self._obtener_objeto(
            request,
            object_id,
        )

        if obj is None:
            return self._redirect_changelist()

        if not puede_registrar_conformidad_instalacion(
            request.user,
            obj,
        ):
            self.message_user(
                request,
                _(
                    "No puede registrar la conformidad "
                    "de esta instalación."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(
                obj
            )

        try:
            registrar_conformidad_instalacion(
                instalacion=obj,
                recibido_por=obj.recibido_por,
                fecha=obj.fecha_conformidad,
                observaciones=(
                    obj.observaciones_conformidad
                ),
            )

        except ValidationError as exc:
            self._mostrar_error(
                request,
                exc,
            )

        else:
            self.message_user(
                request,
                _(
                    "Conformidad registrada correctamente."
                ),
                level=messages.SUCCESS,
            )

        return self._redirect_change(
            obj
        )
    # ======================================================
    # IMPORTAR DISPOSITIVOS DEL PROYECTO
    # ======================================================

    def importar_dispositivos_proyecto_view(
        self,
        request,
        object_id,
    ):
        """
        Importa los dispositivos definidos en el proyecto
        asociado a la OT de esta instalación.

        Cada unidad del ProyectoDetalle genera un
        InstalacionDispositivo individual.
        """

        respuesta = self._validar_post(
            request
        )

        if respuesta:
            return respuesta

        obj = self._obtener_objeto(
            request,
            object_id,
        )

        if obj is None:
            return self._redirect_changelist()

        if not obj.orden_trabajo.proyecto_id:
            self.message_user(
                request,
                _(
                    "Esta instalación no proviene "
                    "de un proyecto."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(
                obj
            )

        if obj.dispositivos.exists():
            self.message_user(
                request,
                _(
                    "La instalación ya tiene dispositivos "
                    "registrados."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(
                obj
            )

        try:
            dispositivos = (
                cargar_dispositivos_desde_proyecto(
                    instalacion=obj,
                )
            )

        except ValidationError as exc:
            self._mostrar_error(
                request,
                exc,
            )

        else:
            self.message_user(
                request,
                _(
                    "Se importaron %(cantidad)s "
                    "dispositivos correctamente."
                )
                % {
                    "cantidad": len(dispositivos),
                },
                level=messages.SUCCESS,
            )

        return self._redirect_change(
            obj
        )

    # ======================================================
    # CONTEXTO DEL TEMPLATE
    # ======================================================

    def changeform_view(
        self,
        request,
        object_id=None,
        form_url="",
        extra_context=None,
    ):
        """
        Expone al template únicamente las operaciones
        permitidas para la instalación actual.
        """

        extra_context = (
            extra_context
            or {}
        )

        obj = None

        if object_id:
            obj = self.get_object(
                request,
                object_id,
            )

        if obj:
            extra_context.update(
                {
                    "puede_programar_instalacion": (
                        puede_programar_instalacion_concreta(
                            request.user,
                            obj,
                        )
                    ),

                    "puede_iniciar_instalacion": (
                        puede_iniciar_instalacion_concreta(
                            request.user,
                            obj,
                        )
                    ),

                    "puede_finalizar_instalacion": (
                        puede_finalizar_instalacion_concreta(
                            request.user,
                            obj,
                        )
                    ),

                    "puede_cancelar_instalacion": (
                        puede_cancelar_instalacion_concreta(
                            request.user,
                            obj,
                        )
                    ),

                    "puede_registrar_conformidad": (
                        puede_registrar_conformidad_instalacion(
                            request.user,
                            obj,
                        )
                    ),
                    "puede_importar_dispositivos_proyecto": bool(
                        obj.orden_trabajo.proyecto_id
                        and not obj.dispositivos.exists()
                    ),
                }
            )

        return super().changeform_view(
            request,
            object_id,
            form_url,
            extra_context,
        )

    # ======================================================
    # ACCIONES
    # ======================================================

    actions = ()