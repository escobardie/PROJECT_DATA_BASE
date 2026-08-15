from django.contrib import admin, messages
from django.core.exceptions import (
    ObjectDoesNotExist,
    ValidationError,
)
from django.utils.html import format_html
from django.http import (
    HttpResponseNotAllowed,
    HttpResponseRedirect,
)
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _

from apps.orden_trabajo.models import OrdenTrabajo

from apps.orden_trabajo.services import (
    crear_instalacion_desde_ot,
    finalizar_orden_trabajo,
    iniciar_orden_trabajo,
    pausar_orden_trabajo,
    programar_orden_trabajo,
    reanudar_orden_trabajo,
    registrar_aceptacion_cliente,
    registrar_cobro_ot,
    registrar_envio_cliente,
    registrar_facturacion_ot,
    registrar_recepcion_solicitud,
    registrar_rechazo_cliente,
)

from apps.usuarios.permissions import (
    puede_cobrar_ot,
    puede_crear_instalacion_desde_ot,
    puede_facturar_ot,
    puede_finalizar_ot,
    puede_iniciar_ot,
    puede_pausar_ot,
    puede_programar_ot,
    puede_reanudar_ot,
    puede_registrar_aceptacion_ot,
    puede_registrar_envio_ot,
    puede_registrar_recepcion_ot,
    puede_registrar_rechazo_ot,
)

from .orden_trabajo_archivo import (
    OrdenTrabajoArchivoInline,
)
from .orden_trabajo_seguimiento import (
    OrdenTrabajoSeguimientoInline,
)
from .orden_trabajo_tecnico import (
    OrdenTrabajoTecnicoInline,
)


@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    """
    Administración de órdenes de trabajo.

    El ciclo funcional de la OT se gestiona mediante:

        Admin
            ↓
        Permissions
            ↓
        Services
            ↓
        Models

    Las fechas permanecen editables para permitir
    registrar la trazabilidad real.

    Los estados y usuarios de auditoría son gestionados
    automáticamente mediante services.
    """

    # ======================================================
    # TEMPLATE
    # ======================================================

    change_form_template = (
        "admin/orden_trabajo/"
        "ordentrabajo/change_form.html"
    )

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "codigo",
        "titulo",
        "estado",
        "estado_aceptacion",
        "prioridad",
        "tipo",
        "responsable",
        "proyecto",
        "servicio_contratado",
        "presupuesto_telecom",
        "fecha_programada",
        "mostrar_instalacion",
        "mostrar_facturada",
        "mostrar_cobrada",
    )

    list_display_links = (
        "codigo",
        "titulo",
    )

    list_filter = (
        "estado",
        "estado_aceptacion",
        "prioridad",
        "tipo",
        "responsable",
        "proyecto",
        "servicio_contratado",
        "presupuesto_telecom",
    )

    search_fields = (
        # OT
        "codigo",
        "titulo",
        "descripcion",

        # Sucursal
        "sucursal__codigo",
        "sucursal__nombre",

        # Proyecto
        "proyecto__codigo",
        "proyecto__nombre",

        # Servicio contratado
        "servicio_contratado__codigo",

        # Presupuesto Telecom
        "presupuesto_telecom__codigo",

        # Instalación generada
        "instalacion__codigo",

        # Instalación preexistente
        "instalacion_relacionada__codigo",

        # Responsable
        "responsable__email",
        "responsable__first_name",
        "responsable__last_name",
    )

    ordering = (
        "-created_at",
    )

    empty_value_display = "-"

    save_on_top = True

    save_as = True

    list_per_page = 25

    show_full_result_count = False

    # ======================================================
    # COLUMNAS PERSONALIZADAS
    # ======================================================

    @admin.display(
        boolean=True,
        description=_("Inst."),
    )
    def mostrar_instalacion(self, obj):
        """
        Indica si la OT generó una instalación.
        """

        return obj.tiene_instalacion

    @admin.display(
        boolean=True,
        description=_("Fact."),
    )
    def mostrar_facturada(self, obj):
        """
        Indica si la OT fue facturada.
        """

        return obj.esta_facturada

    @admin.display(
        boolean=True,
        description=_("Cob."),
    )
    def mostrar_cobrada(self, obj):
        """
        Indica si la OT fue cobrada.
        """

        return obj.esta_cobrada

    # ======================================================
    # INFORMACIÓN DERIVADA
    # ======================================================

    @admin.display(
        description=_("Instalación generada"),
    )
    def instalacion_generada(self, obj):
        """
        Muestra la instalación generada por la OT
        como enlace directo a su formulario Admin.
        """

        if not obj or not obj.pk:
            return "-"

        try:
            instalacion = obj.instalacion

        except ObjectDoesNotExist:
            return "-"

        url = reverse(
            "admin:instalacion_instalacion_change",
            args=(instalacion.pk,),
            current_app=self.admin_site.name,
        )

        return format_html(
            '<a href="{}">{}</a>',
            url,
            instalacion,
        )

    # ======================================================
    # QUERYSET
    # ======================================================

    def get_queryset(self, request):
        """
        Optimiza las relaciones utilizadas por el Admin.
        """

        return (
            super()
            .get_queryset(request)
            .select_related(
                # Origen
                "sucursal",
                "proyecto",
                "servicio_contratado",
                "presupuesto_telecom",

                # Instalaciones
                "instalacion",
                "instalacion_relacionada",

                # Responsable
                "responsable",

                # Auditoría
                "usuario_recepcion_solicitud",
                "usuario_inicio",
                "usuario_finalizacion",
                "usuario_envio_cliente",
                "usuario_aceptacion",
                "usuario_facturacion",
                "usuario_cobro",
            )
        )

    # ======================================================
    # AUTOCOMPLETE
    # ======================================================

    autocomplete_fields = (
        "sucursal",
        "proyecto",
        "servicio_contratado",
        "presupuesto_telecom",
        "instalacion_relacionada",
        "responsable",
    )

    # ======================================================
    # SOLO LECTURA
    # ======================================================

    readonly_fields = (
        "codigo",
        "instalacion_generada",
        "created_at",
        "updated_at",
    )

    def get_readonly_fields(
        self,
        request,
        obj=None,
    ):
        """
        Protege campos gestionados mediante services.

        Las fechas permanecen editables para permitir
        registrar o corregir la fecha real de cada hito.
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
                    # Estados
                    "estado",
                    "estado_aceptacion",

                    # Usuarios de auditoría
                    "usuario_recepcion_solicitud",
                    "usuario_inicio",
                    "usuario_finalizacion",
                    "usuario_envio_cliente",
                    "usuario_aceptacion",
                    "usuario_facturacion",
                    "usuario_cobro",
                )
            )

        return tuple(
            dict.fromkeys(
                campos
            )
        )

    # ======================================================
    # FORMULARIO
    # ======================================================

    fieldsets = (
        (
            _("Información general"),
            {
                "fields": (
                    "codigo",
                    "titulo",
                    "descripcion",
                ),
            },
        ),
        (
            _("Origen de la orden"),
            {
                "fields": (
                    (
                        "sucursal",
                        "proyecto",
                    ),
                    (
                        "servicio_contratado",
                        "presupuesto_telecom",
                    ),
                ),
            },
        ),
        (
            _("Clasificación"),
            {
                "fields": (
                    (
                        "tipo",
                        "estado",
                        "prioridad",
                    ),
                ),
            },
        ),
        (
            _("Recepción de la solicitud"),
            {
                "fields": (
                    (
                        "fecha_recepcion_solicitud",
                        "usuario_recepcion_solicitud",
                    ),
                ),
            },
        ),
        (
            _("Planificación"),
            {
                "fields": (
                    "responsable",
                    "fecha_programada",
                ),
            },
        ),
        (
            _("Envío al cliente"),
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    (
                        "fecha_envio_cliente",
                        "usuario_envio_cliente",
                    ),
                ),
                "description": _(
                    "Aplicable a órdenes provenientes de "
                    "Proyecto o Presupuesto Telecom."
                ),
            },
        ),
        (
            _("Respuesta del cliente"),
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "estado_aceptacion",
                    (
                        "fecha_aceptacion",
                        "usuario_aceptacion",
                    ),
                ),
                "description": _(
                    "Indica si el cliente aceptó o rechazó "
                    "la propuesta enviada."
                ),
            },
        ),
        (
            _("Ejecución"),
            {
                "fields": (
                    (
                        "fecha_inicio",
                        "usuario_inicio",
                    ),
                    (
                        "fecha_finalizacion",
                        "usuario_finalizacion",
                    ),
                ),
            },
        ),
        (
            _("Instalaciones"),
            {
                "fields": (
                    "instalacion_generada",
                    "instalacion_relacionada",
                ),
                "description": _(
                    "La instalación generada es el resultado "
                    "técnico de esta orden. La instalación "
                    "relacionada corresponde a una instalación "
                    "preexistente sobre la cual se ejecuta "
                    "el trabajo."
                ),
            },
        ),
        (
            _("Facturación"),
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    (
                        "fecha_facturacion",
                        "usuario_facturacion",
                    ),
                ),
            },
        ),
        (
            _("Cobro"),
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    (
                        "fecha_cobro",
                        "usuario_cobro",
                    ),
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
        OrdenTrabajoTecnicoInline,
        OrdenTrabajoSeguimientoInline,
        OrdenTrabajoArchivoInline,
    )

    # ======================================================
    # URLS PERSONALIZADAS
    # ======================================================

    def get_urls(self):
        """
        Endpoints administrativos para ejecutar
        el ciclo funcional mediante services.
        """

        urls = super().get_urls()

        custom_urls = [
            path(
                "<path:object_id>/registrar-recepcion/",
                self.admin_site.admin_view(
                    self.registrar_recepcion_view
                ),
                name=(
                    "orden_trabajo_ordentrabajo_"
                    "registrar_recepcion"
                ),
            ),
            path(
                "<path:object_id>/programar/",
                self.admin_site.admin_view(
                    self.programar_view
                ),
                name=(
                    "orden_trabajo_ordentrabajo_"
                    "programar"
                ),
            ),
            path(
                "<path:object_id>/registrar-envio/",
                self.admin_site.admin_view(
                    self.registrar_envio_view
                ),
                name=(
                    "orden_trabajo_ordentrabajo_"
                    "registrar_envio"
                ),
            ),
            path(
                "<path:object_id>/aceptar/",
                self.admin_site.admin_view(
                    self.registrar_aceptacion_view
                ),
                name=(
                    "orden_trabajo_ordentrabajo_"
                    "aceptar"
                ),
            ),
            path(
                "<path:object_id>/rechazar/",
                self.admin_site.admin_view(
                    self.registrar_rechazo_view
                ),
                name=(
                    "orden_trabajo_ordentrabajo_"
                    "rechazar"
                ),
            ),
            path(
                "<path:object_id>/iniciar/",
                self.admin_site.admin_view(
                    self.iniciar_view
                ),
                name=(
                    "orden_trabajo_ordentrabajo_"
                    "iniciar"
                ),
            ),
            path(
                "<path:object_id>/pausar/",
                self.admin_site.admin_view(
                    self.pausar_view
                ),
                name=(
                    "orden_trabajo_ordentrabajo_"
                    "pausar"
                ),
            ),
            path(
                "<path:object_id>/reanudar/",
                self.admin_site.admin_view(
                    self.reanudar_view
                ),
                name=(
                    "orden_trabajo_ordentrabajo_"
                    "reanudar"
                ),
            ),
            path(
                "<path:object_id>/generar-instalacion/",
                self.admin_site.admin_view(
                    self.generar_instalacion_view
                ),
                name=(
                    "orden_trabajo_ordentrabajo_"
                    "generar_instalacion"
                ),
            ),
            path(
                "<path:object_id>/finalizar/",
                self.admin_site.admin_view(
                    self.finalizar_view
                ),
                name=(
                    "orden_trabajo_ordentrabajo_"
                    "finalizar"
                ),
            ),
            path(
                "<path:object_id>/facturar/",
                self.admin_site.admin_view(
                    self.registrar_facturacion_view
                ),
                name=(
                    "orden_trabajo_ordentrabajo_"
                    "facturar"
                ),
            ),
            path(
                "<path:object_id>/cobrar/",
                self.admin_site.admin_view(
                    self.registrar_cobro_view
                ),
                name=(
                    "orden_trabajo_ordentrabajo_"
                    "cobrar"
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
        Redirige al formulario de la OT.
        """

        url = reverse(
            "admin:"
            "orden_trabajo_ordentrabajo_change",
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
        Redirige al listado de OT.
        """

        url = reverse(
            "admin:"
            "orden_trabajo_ordentrabajo_changelist",
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
        Obtiene una OT según el alcance del Admin.
        """

        return self.get_object(
            request,
            object_id,
        )

    def _validar_post(self, request):
        """
        Las operaciones de escritura solo pueden
        ejecutarse mediante HTTP POST.
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
        Muestra un ValidationError como mensaje
        del Django Admin.
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
    # RECEPCIÓN
    # ======================================================

    def registrar_recepcion_view(
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

        if not puede_registrar_recepcion_ot(
            request.user,
            obj,
        ):
            self.message_user(
                request,
                _(
                    "No puede registrar la recepción "
                    "de esta orden."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(obj)

        try:
            registrar_recepcion_solicitud(
                orden_trabajo=obj,
                usuario=request.user,
            )

        except ValidationError as exc:
            self._mostrar_error(
                request,
                exc,
            )

        else:
            self.message_user(
                request,
                _("Recepción registrada correctamente."),
                level=messages.SUCCESS,
            )

        return self._redirect_change(obj)

    # ======================================================
    # PROGRAMACIÓN
    # ======================================================

    def programar_view(
        self,
        request,
        object_id,
    ):
        respuesta = self._validar_post(request)

        if respuesta:
            return respuesta

        obj = self._obtener_objeto(
            request,
            object_id,
        )

        if obj is None:
            return self._redirect_changelist()

        if not puede_programar_ot(
            request.user,
            obj,
        ):
            self.message_user(
                request,
                _(
                    "La orden no puede programarse "
                    "en su estado actual."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(obj)

        try:
            programar_orden_trabajo(
                orden_trabajo=obj,
                fecha_programada=(
                    obj.fecha_programada
                ),
            )

        except ValidationError as exc:
            self._mostrar_error(request, exc)

        else:
            self.message_user(
                request,
                _("Orden programada correctamente."),
                level=messages.SUCCESS,
            )

        return self._redirect_change(obj)

    # ======================================================
    # ENVÍO AL CLIENTE
    # ======================================================

    def registrar_envio_view(
        self,
        request,
        object_id,
    ):
        respuesta = self._validar_post(request)

        if respuesta:
            return respuesta

        obj = self._obtener_objeto(
            request,
            object_id,
        )

        if obj is None:
            return self._redirect_changelist()

        if not puede_registrar_envio_ot(
            request.user,
            obj,
        ):
            self.message_user(
                request,
                _(
                    "No puede registrar el envío "
                    "de esta orden."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(obj)

        try:
            registrar_envio_cliente(
                orden_trabajo=obj,
                usuario=request.user,
            )

        except ValidationError as exc:
            self._mostrar_error(request, exc)

        else:
            self.message_user(
                request,
                _("Envío al cliente registrado."),
                level=messages.SUCCESS,
            )

        return self._redirect_change(obj)

    # ======================================================
    # ACEPTACIÓN
    # ======================================================

    def registrar_aceptacion_view(
        self,
        request,
        object_id,
    ):
        respuesta = self._validar_post(request)

        if respuesta:
            return respuesta

        obj = self._obtener_objeto(
            request,
            object_id,
        )

        if obj is None:
            return self._redirect_changelist()

        if not puede_registrar_aceptacion_ot(
            request.user,
            obj,
        ):
            self.message_user(
                request,
                _(
                    "No puede registrar la aceptación "
                    "de esta orden."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(obj)

        try:
            registrar_aceptacion_cliente(
                orden_trabajo=obj,
                usuario=request.user,
            )

        except ValidationError as exc:
            self._mostrar_error(request, exc)

        else:
            self.message_user(
                request,
                _("Aceptación del cliente registrada."),
                level=messages.SUCCESS,
            )

        return self._redirect_change(obj)

    # ======================================================
    # RECHAZO
    # ======================================================

    def registrar_rechazo_view(
        self,
        request,
        object_id,
    ):
        respuesta = self._validar_post(request)

        if respuesta:
            return respuesta

        obj = self._obtener_objeto(
            request,
            object_id,
        )

        if obj is None:
            return self._redirect_changelist()

        if not puede_registrar_rechazo_ot(
            request.user,
            obj,
        ):
            self.message_user(
                request,
                _(
                    "No puede registrar el rechazo "
                    "de esta orden."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(obj)

        try:
            registrar_rechazo_cliente(
                orden_trabajo=obj,
                usuario=request.user,
            )

        except ValidationError as exc:
            self._mostrar_error(request, exc)

        else:
            self.message_user(
                request,
                _("Rechazo del cliente registrado."),
                level=messages.SUCCESS,
            )

        return self._redirect_change(obj)

    # ======================================================
    # INICIO
    # ======================================================

    def iniciar_view(
        self,
        request,
        object_id,
    ):
        respuesta = self._validar_post(request)

        if respuesta:
            return respuesta

        obj = self._obtener_objeto(
            request,
            object_id,
        )

        if obj is None:
            return self._redirect_changelist()

        if not puede_iniciar_ot(
            request.user,
            obj,
        ):
            self.message_user(
                request,
                _(
                    "La orden no puede iniciarse "
                    "en su estado actual."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(obj)

        try:
            iniciar_orden_trabajo(
                orden_trabajo=obj,
                usuario=request.user,
            )

        except ValidationError as exc:
            self._mostrar_error(request, exc)

        else:
            self.message_user(
                request,
                _("Orden iniciada correctamente."),
                level=messages.SUCCESS,
            )

        return self._redirect_change(obj)

    # ======================================================
    # PAUSA
    # ======================================================

    def pausar_view(
        self,
        request,
        object_id,
    ):
        respuesta = self._validar_post(request)

        if respuesta:
            return respuesta

        obj = self._obtener_objeto(
            request,
            object_id,
        )

        if obj is None:
            return self._redirect_changelist()

        if not puede_pausar_ot(
            request.user,
            obj,
        ):
            self.message_user(
                request,
                _("La orden no puede pausarse."),
                level=messages.ERROR,
            )

            return self._redirect_change(obj)

        try:
            pausar_orden_trabajo(
                orden_trabajo=obj,
            )

        except ValidationError as exc:
            self._mostrar_error(request, exc)

        else:
            self.message_user(
                request,
                _("Orden pausada correctamente."),
                level=messages.SUCCESS,
            )

        return self._redirect_change(obj)

    # ======================================================
    # REANUDACIÓN
    # ======================================================

    def reanudar_view(
        self,
        request,
        object_id,
    ):
        respuesta = self._validar_post(request)

        if respuesta:
            return respuesta

        obj = self._obtener_objeto(
            request,
            object_id,
        )

        if obj is None:
            return self._redirect_changelist()

        if not puede_reanudar_ot(
            request.user,
            obj,
        ):
            self.message_user(
                request,
                _("La orden no puede reanudarse."),
                level=messages.ERROR,
            )

            return self._redirect_change(obj)

        try:
            reanudar_orden_trabajo(
                orden_trabajo=obj,
            )

        except ValidationError as exc:
            self._mostrar_error(request, exc)

        else:
            self.message_user(
                request,
                _("Orden reanudada correctamente."),
                level=messages.SUCCESS,
            )

        return self._redirect_change(obj)

    # ======================================================
    # GENERAR INSTALACIÓN
    # ======================================================

    def generar_instalacion_view(
        self,
        request,
        object_id,
    ):
        respuesta = self._validar_post(request)

        if respuesta:
            return respuesta

        obj = self._obtener_objeto(
            request,
            object_id,
        )

        if obj is None:
            return self._redirect_changelist()

        if not puede_crear_instalacion_desde_ot(
            request.user,
            obj,
        ):
            self.message_user(
                request,
                _(
                    "No puede generar una instalación "
                    "desde esta orden."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(obj)

        try:
            instalacion = crear_instalacion_desde_ot(
                orden_trabajo=obj,
            )

        except ValidationError as exc:
            self._mostrar_error(request, exc)

        else:
            self.message_user(
                request,
                _(
                    "Instalación %(codigo)s "
                    "generada correctamente."
                )
                % {
                    "codigo": instalacion.codigo,
                },
                level=messages.SUCCESS,
            )

        return self._redirect_change(obj)

    # ======================================================
    # FINALIZACIÓN
    # ======================================================

    def finalizar_view(
        self,
        request,
        object_id,
    ):
        respuesta = self._validar_post(request)

        if respuesta:
            return respuesta

        obj = self._obtener_objeto(
            request,
            object_id,
        )

        if obj is None:
            return self._redirect_changelist()

        if not puede_finalizar_ot(
            request.user,
            obj,
        ):
            self.message_user(
                request,
                _(
                    "La orden todavía no cumple "
                    "las condiciones para finalizarse."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(obj)

        try:
            finalizar_orden_trabajo(
                orden_trabajo=obj,
                usuario=request.user,
            )

        except ValidationError as exc:
            self._mostrar_error(request, exc)

        else:
            self.message_user(
                request,
                _("Orden finalizada correctamente."),
                level=messages.SUCCESS,
            )

        return self._redirect_change(obj)

    # ======================================================
    # FACTURACIÓN
    # ======================================================

    def registrar_facturacion_view(
        self,
        request,
        object_id,
    ):
        respuesta = self._validar_post(request)

        if respuesta:
            return respuesta

        obj = self._obtener_objeto(
            request,
            object_id,
        )

        if obj is None:
            return self._redirect_changelist()

        if not puede_facturar_ot(
            request.user,
            obj,
        ):
            self.message_user(
                request,
                _(
                    "No puede registrar la facturación "
                    "de esta orden."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(obj)

        try:
            registrar_facturacion_ot(
                orden_trabajo=obj,
                usuario=request.user,
            )

        except ValidationError as exc:
            self._mostrar_error(request, exc)

        else:
            self.message_user(
                request,
                _("Facturación registrada correctamente."),
                level=messages.SUCCESS,
            )

        return self._redirect_change(obj)

    # ======================================================
    # COBRO
    # ======================================================

    def registrar_cobro_view(
        self,
        request,
        object_id,
    ):
        respuesta = self._validar_post(request)

        if respuesta:
            return respuesta

        obj = self._obtener_objeto(
            request,
            object_id,
        )

        if obj is None:
            return self._redirect_changelist()

        if not puede_cobrar_ot(
            request.user,
            obj,
        ):
            self.message_user(
                request,
                _(
                    "No puede registrar el cobro "
                    "de esta orden."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(obj)

        try:
            registrar_cobro_ot(
                orden_trabajo=obj,
                usuario=request.user,
            )

        except ValidationError as exc:
            self._mostrar_error(request, exc)

        else:
            self.message_user(
                request,
                _("Cobro registrado correctamente."),
                level=messages.SUCCESS,
            )

        return self._redirect_change(obj)

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
        permitidas para la OT actual.
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
                    "puede_registrar_recepcion_ot": (
                        puede_registrar_recepcion_ot(
                            request.user,
                            obj,
                        )
                    ),

                    "puede_programar_ot": (
                        puede_programar_ot(
                            request.user,
                            obj,
                        )
                    ),

                    "puede_registrar_envio_ot": (
                        puede_registrar_envio_ot(
                            request.user,
                            obj,
                        )
                    ),

                    "puede_registrar_aceptacion_ot": (
                        puede_registrar_aceptacion_ot(
                            request.user,
                            obj,
                        )
                    ),

                    "puede_registrar_rechazo_ot": (
                        puede_registrar_rechazo_ot(
                            request.user,
                            obj,
                        )
                    ),

                    "puede_iniciar_ot": (
                        puede_iniciar_ot(
                            request.user,
                            obj,
                        )
                    ),

                    "puede_pausar_ot": (
                        puede_pausar_ot(
                            request.user,
                            obj,
                        )
                    ),

                    "puede_reanudar_ot": (
                        puede_reanudar_ot(
                            request.user,
                            obj,
                        )
                    ),

                    "puede_generar_instalacion_ot": (
                        puede_crear_instalacion_desde_ot(
                            request.user,
                            obj,
                        )
                    ),

                    "puede_finalizar_ot": (
                        puede_finalizar_ot(
                            request.user,
                            obj,
                        )
                    ),

                    "puede_facturar_ot": (
                        puede_facturar_ot(
                            request.user,
                            obj,
                        )
                    ),

                    "puede_cobrar_ot": (
                        puede_cobrar_ot(
                            request.user,
                            obj,
                        )
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
    # ACCIONES MASIVAS
    # ======================================================

    actions = ()