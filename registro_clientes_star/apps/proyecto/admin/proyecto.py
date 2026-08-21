from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count
from django.http import (
    HttpResponseNotAllowed,
    HttpResponseRedirect,
)
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _

from apps.proyecto.models import (
    Proyecto,
    ProyectoDetalle,
)

from apps.proyecto.services import (
    actualizar_detalle_proyecto,
    crear_detalle_proyecto,
    crear_orden_trabajo_desde_proyecto,
    eliminar_detalle_proyecto,
    finalizar_proyecto,
    planificar_proyecto,
    registrar_aceptacion_proyecto,
    registrar_envio_proyecto,
    registrar_recepcion_proyecto,
    registrar_rechazo_proyecto,
)

from apps.usuarios.permissions import (
    puede_editar_proyecto,
    puede_eliminar_proyecto,
    puede_finalizar_proyecto,
    puede_generar_ot_desde_proyecto,
    puede_planificar_proyecto,
    puede_registrar_aceptacion_proyecto,
    puede_registrar_envio_proyecto,
    puede_registrar_recepcion_proyecto,
    puede_registrar_rechazo_proyecto,
    puede_ver_costos_del_proyecto,
    puede_ver_proyecto,
)

from apps.usuarios.services.permisos import (
    puede_crear_proyectos,
    puede_ver_costos_proyecto,
    puede_ver_proyectos,
)

from apps.usuarios.services.querysets import (
    filtrar_proyectos,
)

from .inlines import ProyectoDetalleInline


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    """
    Administración de proyectos.

    El flujo comercial y operativo del proyecto
    se gestiona mediante:

        Admin
            ↓
        Permissions
            ↓
        Services
            ↓
        Models

    Flujo principal:

        BORRADOR
            ↓
        Registrar recepción
            ↓
        Planificar
            ↓
        PLANIFICADO
            ↓
        Registrar envío
            ↓
        PENDIENTE_APROBACION
            ↓
        Aceptar / Rechazar
            ↓
        APROBADO
            ↓
        Generar OT

    Regla general para fechas de hitos:

        1. fecha escrita actualmente en el Admin;
        2. fecha previamente guardada;
        3. fecha actual resuelta por el service.

    Las fechas permanecen editables para permitir
    registrar fechas históricas o reales.

    Los estados y usuarios que registran cada hito
    son gestionados exclusivamente mediante services.
    """

    # ======================================================
    # TEMPLATE
    # ======================================================

    change_form_template = (
        "admin/proyecto/proyecto/change_form.html"
    )

    # ======================================================
    # LISTADO
    # ======================================================

    list_display = (
        "codigo",
        "nombre",
        "sucursal",
        "responsable",
        "prioridad",
        "estado",
        "respuesta_cliente",
        "cantidad_detalles",
        "cantidad_ordenes_trabajo",
        "fecha_creacion",
        "fecha_planificada",
        "total",
    )

    list_display_links = (
        "codigo",
        "nombre",
    )

    list_filter = (
        "estado",
        "prioridad",
        "respuesta_cliente",
        "moneda",
        "responsable",
        "sucursal",
    )

    search_fields = (
        # Proyecto
        "codigo",
        "nombre",
        "descripcion",

        # Sucursal
        "sucursal__codigo",
        "sucursal__nombre",

        # Cuenta cliente
        "sucursal__cuenta_cliente__codigo",
        "sucursal__cuenta_cliente__nombre",

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

    # Evita duplicar accidentalmente un proyecto
    # mediante "Guardar como nuevo".
    save_as = False

    list_per_page = 25

    show_full_result_count = False

    # ======================================================
    # AUTOCOMPLETE
    # ======================================================

    autocomplete_fields = (
        "sucursal",
        "responsable",
    )

    # ======================================================
    # SOLO LECTURA
    # ======================================================

    readonly_fields = (
        "codigo",

        # Importes calculados
        "subtotal",
        "descuento_total",
        "impuestos",
        "total",

        # Auditoría base
        "created_at",
        "updated_at",
    )

    def get_readonly_fields(
        self,
        request,
        obj=None,
    ):
        """
        Protege los campos administrados por el flujo
        automático del proyecto.

        Las fechas permanecen editables para permitir
        registrar fechas históricas o reales.
        """

        campos = list(
            super().get_readonly_fields(
                request,
                obj,
            )
        )

        campos.extend(
            (
                "estado",
                "respuesta_cliente",
                "usuario_recepcion_solicitud",
                "usuario_envio_cliente",
                "usuario_respuesta_cliente",
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
                    "sucursal",
                    "nombre",
                    "descripcion",
                ),
            },
        ),

        (
            _("Clasificación"),
            {
                "fields": (
                    (
                        "prioridad",
                        "estado",
                    ),
                ),
            },
        ),

        (
            _("Condiciones comerciales"),
            {
                "fields": (
                    "moneda",
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
                "description": _(
                    "Registra cuándo fue recibida la solicitud "
                    "que originó el proyecto."
                ),
            },
        ),

        (
            _("Planificación"),
            {
                "fields": (
                    "responsable",
                    (
                        "fecha_creacion",
                        "fecha_planificada",
                    ),
                ),
                "description": _(
                    "Responsable y fecha prevista para "
                    "la planificación del proyecto."
                ),
            },
        ),

        (
            _("Envío al cliente"),
            {
                "fields": (
                    (
                        "fecha_envio_cliente",
                        "usuario_envio_cliente",
                    ),
                ),
                "description": _(
                    "Registra el envío formal del proyecto "
                    "al cliente para su evaluación."
                ),
            },
        ),

        (
            _("Respuesta del cliente"),
            {
                "fields": (
                    "respuesta_cliente",
                    (
                        "fecha_respuesta_cliente",
                        "usuario_respuesta_cliente",
                    ),
                ),
                "description": _(
                    "Registra si el cliente aceptó o rechazó "
                    "el proyecto enviado."
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
            _("Observaciones"),
            {
                "fields": (
                    "observaciones",
                ),
            },
        ),

        (
            _("Resumen económico"),
            {
                "fields": (
                    (
                        "subtotal",
                        "descuento_total",
                    ),
                    (
                        "impuestos",
                        "total",
                    ),
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
        ProyectoDetalleInline,
    )

    # ======================================================
    # QUERYSET
    # ======================================================

    def get_queryset(
        self,
        request,
    ):
        """
        Optimiza la consulta y limita los proyectos visibles
        según el alcance del usuario.
        """

        queryset = (
            super()
            .get_queryset(request)
            .select_related(
                # Origen
                "sucursal",
                "sucursal__cuenta_cliente",

                # Responsable
                "responsable",

                # Trazabilidad
                "usuario_recepcion_solicitud",
                "usuario_envio_cliente",
                "usuario_respuesta_cliente",
            )
            .annotate(
                _cantidad_detalles=Count(
                    "detalles",
                    distinct=True,
                ),
                _cantidad_ordenes_trabajo=Count(
                    "ordenes_trabajo",
                    distinct=True,
                ),
            )
        )

        return filtrar_proyectos(
            request.user,
            queryset,
        )

    # ======================================================
    # COLUMNAS DINÁMICAS
    # ======================================================

    def get_list_display(
        self,
        request,
    ):
        """
        Oculta los importes económicos para usuarios
        que no tienen autorización para consultarlos.
        """

        columnas = list(
            super().get_list_display(
                request
            )
        )

        if not puede_ver_costos_proyecto(
            request.user
        ):
            columnas = [
                columna
                for columna in columnas
                if columna != "total"
            ]

        return tuple(
            columnas
        )

    # ======================================================
    # FIELDSETS DINÁMICOS
    # ======================================================

    def get_fieldsets(
        self,
        request,
        obj=None,
    ):
        """
        Retira el resumen económico cuando el usuario
        no está autorizado a consultar costos e importes.
        """

        fieldsets = list(
            super().get_fieldsets(
                request,
                obj,
            )
        )

        puede_ver_costos = (
            puede_ver_costos_del_proyecto(
                request.user,
                obj,
            )
            if obj
            else puede_ver_costos_proyecto(
                request.user,
            )
        )

        if not puede_ver_costos:
            fieldsets = [
                fieldset
                for fieldset in fieldsets
                if fieldset[0]
                != _("Resumen económico")
            ]

        return tuple(
            fieldsets
        )

    # ======================================================
    # PERMISOS DEL ADMIN
    # ======================================================

    def has_module_permission(
        self,
        request,
    ):
        """
        Controla si Proyecto aparece
        en el índice administrativo.
        """

        return puede_ver_proyectos(
            request.user
        )

    def has_view_permission(
        self,
        request,
        obj=None,
    ):
        """
        Controla la visualización general
        y por objeto.
        """

        permiso_django = (
            super().has_view_permission(
                request,
                obj,
            )
        )

        if not permiso_django:
            return False

        if obj is None:
            return puede_ver_proyectos(
                request.user
            )

        return puede_ver_proyecto(
            request.user,
            obj,
        )

    def has_add_permission(
        self,
        request,
    ):
        """
        Controla la creación de proyectos.
        """

        permiso_django = (
            super().has_add_permission(
                request
            )
        )

        return bool(
            permiso_django
            and puede_crear_proyectos(
                request.user
            )
        )

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        """
        Controla la modificación general
        y por objeto.
        """

        permiso_django = (
            super().has_change_permission(
                request,
                obj,
            )
        )

        if not permiso_django:
            return False

        if obj is None:
            return request.user.has_perm(
                "proyecto.change_proyecto"
            )

        return puede_editar_proyecto(
            request.user,
            obj,
        )

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        """
        Solamente permite eliminar proyectos completos
        cuando la regla específica lo autoriza.
        """

        permiso_django = (
            super().has_delete_permission(
                request,
                obj,
            )
        )

        if not permiso_django:
            return False

        if obj is None:
            return bool(
                request.user.is_superuser
                and request.user.has_perm(
                    "proyecto.delete_proyecto"
                )
            )

        return puede_eliminar_proyecto(
            request.user,
            obj,
        )

    # ======================================================
    # URLS PERSONALIZADAS
    # ======================================================

    def get_urls(
        self,
    ):
        """
        Agrega los endpoints administrativos
        correspondientes al flujo del proyecto.
        """

        urls = super().get_urls()

        custom_urls = [
            path(
                "<path:object_id>/registrar-recepcion/",
                self.admin_site.admin_view(
                    self.registrar_recepcion_view
                ),
                name=(
                    "proyecto_proyecto_"
                    "registrar_recepcion"
                ),
            ),

            path(
                "<path:object_id>/planificar/",
                self.admin_site.admin_view(
                    self.planificar_view
                ),
                name=(
                    "proyecto_proyecto_"
                    "planificar"
                ),
            ),

            path(
                "<path:object_id>/registrar-envio/",
                self.admin_site.admin_view(
                    self.registrar_envio_view
                ),
                name=(
                    "proyecto_proyecto_"
                    "registrar_envio"
                ),
            ),

            path(
                "<path:object_id>/registrar-aceptacion/",
                self.admin_site.admin_view(
                    self.registrar_aceptacion_view
                ),
                name=(
                    "proyecto_proyecto_"
                    "registrar_aceptacion"
                ),
            ),

            path(
                "<path:object_id>/registrar-rechazo/",
                self.admin_site.admin_view(
                    self.registrar_rechazo_view
                ),
                name=(
                    "proyecto_proyecto_"
                    "registrar_rechazo"
                ),
            ),

            path(
                "<path:object_id>/finalizar/",
                self.admin_site.admin_view(
                    self.finalizar_proyecto_view
                ),
                name=(
                    "proyecto_proyecto_finalizar"
                ),
            ),

            path(
                "<path:object_id>/generar-ot/",
                self.admin_site.admin_view(
                    self.generar_ot_view
                ),
                name=(
                    "proyecto_proyecto_generar_ot"
                ),
            ),
        ]

        return (
            custom_urls
            + urls
        )

    # ======================================================
    # HELPERS ADMIN
    # ======================================================

    def _redirect_change(
        self,
        proyecto,
    ):
        """
        Redirige al formulario de modificación
        del proyecto.
        """

        url = reverse(
            "admin:proyecto_proyecto_change",
            args=(
                proyecto.pk,
            ),
            current_app=self.admin_site.name,
        )

        return HttpResponseRedirect(
            url
        )

    def _redirect_changelist(
        self,
    ):
        """
        Redirige al listado de proyectos.
        """

        url = reverse(
            "admin:proyecto_proyecto_changelist",
            current_app=self.admin_site.name,
        )

        return HttpResponseRedirect(
            url
        )

    def _validar_post(
        self,
        request,
    ):
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
        legible dentro del Django Admin.
        """

        if hasattr(
            exc,
            "messages",
        ):
            mensaje = " ".join(
                str(item)
                for item in exc.messages
            )

        else:
            mensaje = str(
                exc
            )

        self.message_user(
            request,
            mensaje,
            level=messages.ERROR,
        )

    def _obtener_proyecto(
        self,
        request,
        object_id,
    ):
        """
        Obtiene el proyecto respetando
        el queryset autorizado del Admin.
        """

        return self.get_object(
            request,
            object_id,
        )

    # ======================================================
    # HELPERS DE FECHAS
    # ======================================================

    def _obtener_fecha_post(
        self,
        request,
        nombre_campo,
    ):
        """
        Obtiene un DateField enviado por un botón
        personalizado del Admin.

        Retorna None cuando el usuario no indicó
        ninguna fecha.

        El service será responsable de resolver:

            fecha enviada
                ↓
            fecha guardada
                ↓
            fecha actual
        """

        valor = (
            request.POST.get(
                nombre_campo
            )
            or ""
        ).strip()

        if not valor:
            return None

        try:
            return forms.DateField(
                required=False,
            ).clean(
                valor
            )

        except ValidationError as exc:
            raise ValidationError(
                {
                    nombre_campo: _(
                        "La fecha indicada no tiene "
                        "un formato válido."
                    )
                }
            ) from exc

    def _obtener_fecha_hora_post(
        self,
        request,
        nombre_campo,
    ):
        """
        Obtiene un DateTimeField enviado por un botón
        personalizado del Admin.

        Soporta dos formatos:

        1. campo DateTime simple;
        2. widget dividido de Django Admin:
               nombre_campo_0 = fecha
               nombre_campo_1 = hora

        Retorna None cuando no se indicó una fecha.

        El service resolverá posteriormente:

            fecha enviada
                ↓
            fecha guardada
                ↓
            fecha/hora actual
        """

        # ==================================================
        # CAMPO SIMPLE
        # ==================================================

        valor_simple = (
            request.POST.get(
                nombre_campo
            )
            or ""
        ).strip()

        if valor_simple:
            try:
                return forms.DateTimeField(
                    required=False,
                ).clean(
                    valor_simple
                )

            except ValidationError as exc:
                raise ValidationError(
                    {
                        nombre_campo: _(
                            "La fecha y hora indicadas "
                            "no tienen un formato válido."
                        )
                    }
                ) from exc

        # ==================================================
        # WIDGET DIVIDIDO DEL ADMIN
        # ==================================================

        valor_fecha = (
            request.POST.get(
                f"{nombre_campo}_0"
            )
            or ""
        ).strip()

        valor_hora = (
            request.POST.get(
                f"{nombre_campo}_1"
            )
            or ""
        ).strip()

        if (
            not valor_fecha
            and not valor_hora
        ):
            return None

        try:
            return forms.SplitDateTimeField(
                required=False,
            ).clean(
                [
                    valor_fecha,
                    valor_hora,
                ]
            )

        except ValidationError as exc:
            raise ValidationError(
                {
                    nombre_campo: _(
                        "La fecha y hora indicadas "
                        "no tienen un formato válido."
                    )
                }
            ) from exc

    # ======================================================
    # REGISTRAR RECEPCIÓN
    # ======================================================

    def registrar_recepcion_view(
        self,
        request,
        object_id,
    ):
        """
        Registra la recepción de la solicitud.

        Prioridad:

        1. fecha escrita actualmente en el Admin;
        2. fecha previamente guardada;
        3. fecha/hora actual resuelta por el service.
        """

        respuesta = self._validar_post(
            request
        )

        if respuesta:
            return respuesta

        proyecto = self._obtener_proyecto(
            request,
            object_id,
        )

        if proyecto is None:
            return self._redirect_changelist()

        # ==================================================
        # PERMISO
        # ==================================================

        if not puede_registrar_recepcion_proyecto(
            request.user,
            proyecto,
        ):
            self.message_user(
                request,
                _(
                    "No puede registrar la recepción "
                    "de este proyecto."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(
                proyecto
            )

        # ==================================================
        # FECHA ESCRITA EN ADMIN
        # ==================================================

        try:
            fecha = (
                self._obtener_fecha_hora_post(
                    request,
                    "fecha_recepcion_solicitud",
                )
            )

        except ValidationError as exc:
            self._mostrar_error(
                request,
                exc,
            )

            return self._redirect_change(
                proyecto
            )

        # ==================================================
        # SERVICE
        # ==================================================

        try:
            registrar_recepcion_proyecto(
                proyecto=proyecto,
                usuario=request.user,
                fecha=fecha,
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
                    "Recepción de la solicitud "
                    "registrada correctamente."
                ),
                level=messages.SUCCESS,
            )

        return self._redirect_change(
            proyecto
        )

    # ======================================================
    # PLANIFICACIÓN
    # ======================================================

    def planificar_view(
        self,
        request,
        object_id,
    ):
        """
        Confirma la planificación del proyecto.

        Prioridad:

        1. fecha escrita actualmente en el Admin;
        2. fecha previamente guardada;
        3. fecha actual resuelta por el service.
        """

        respuesta = self._validar_post(
            request
        )

        if respuesta:
            return respuesta

        proyecto = self._obtener_proyecto(
            request,
            object_id,
        )

        if proyecto is None:
            return self._redirect_changelist()

        # ==================================================
        # PERMISO
        # ==================================================

        if not puede_planificar_proyecto(
            request.user,
            proyecto,
        ):
            self.message_user(
                request,
                _(
                    "El proyecto no cumple las condiciones "
                    "para ser planificado."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(
                proyecto
            )

        # ==================================================
        # FECHA ESCRITA EN ADMIN
        # ==================================================

        try:
            fecha_planificada = (
                self._obtener_fecha_post(
                    request,
                    "fecha_planificada",
                )
            )

        except ValidationError as exc:
            self._mostrar_error(
                request,
                exc,
            )

            return self._redirect_change(
                proyecto
            )

        # ==================================================
        # SERVICE
        # ==================================================

        try:
            planificar_proyecto(
                proyecto=proyecto,
                fecha_planificada=fecha_planificada,
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
                    "Proyecto planificado correctamente."
                ),
                level=messages.SUCCESS,
            )

        return self._redirect_change(
            proyecto
        )

    # ======================================================
    # ENVÍO AL CLIENTE
    # ======================================================

    def registrar_envio_view(
        self,
        request,
        object_id,
    ):
        """
        Registra el envío del proyecto al cliente.

        Prioridad:

        1. fecha escrita actualmente en el Admin;
        2. fecha previamente guardada;
        3. fecha/hora actual resuelta por el service.
        """

        respuesta = self._validar_post(
            request
        )

        if respuesta:
            return respuesta

        proyecto = self._obtener_proyecto(
            request,
            object_id,
        )

        if proyecto is None:
            return self._redirect_changelist()

        # ==================================================
        # PERMISO
        # ==================================================

        if not puede_registrar_envio_proyecto(
            request.user,
            proyecto,
        ):
            self.message_user(
                request,
                _(
                    "El proyecto no cumple las condiciones "
                    "para registrar el envío al cliente."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(
                proyecto
            )

        # ==================================================
        # FECHA ESCRITA EN ADMIN
        # ==================================================

        try:
            fecha = (
                self._obtener_fecha_hora_post(
                    request,
                    "fecha_envio_cliente",
                )
            )

        except ValidationError as exc:
            self._mostrar_error(
                request,
                exc,
            )

            return self._redirect_change(
                proyecto
            )

        # ==================================================
        # SERVICE
        # ==================================================

        try:
            registrar_envio_proyecto(
                proyecto=proyecto,
                usuario=request.user,
                fecha=fecha,
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
                    "Envío al cliente registrado "
                    "correctamente."
                ),
                level=messages.SUCCESS,
            )

        return self._redirect_change(
            proyecto
        )

    # ======================================================
    # ACEPTACIÓN
    # ======================================================

    def registrar_aceptacion_view(
        self,
        request,
        object_id,
    ):
        """
        Registra la aceptación del proyecto
        por parte del cliente.

        Prioridad para la fecha de respuesta:

        1. fecha escrita actualmente en el Admin;
        2. fecha previamente guardada;
        3. fecha/hora actual resuelta por el service.

        El service cambia automáticamente
        el proyecto a APROBADO.
        """

        respuesta = self._validar_post(
            request
        )

        if respuesta:
            return respuesta

        proyecto = self._obtener_proyecto(
            request,
            object_id,
        )

        if proyecto is None:
            return self._redirect_changelist()

        # ==================================================
        # PERMISO
        # ==================================================

        if not puede_registrar_aceptacion_proyecto(
            request.user,
            proyecto,
        ):
            self.message_user(
                request,
                _(
                    "No puede registrar la aceptación "
                    "de este proyecto."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(
                proyecto
            )

        # ==================================================
        # FECHA ESCRITA EN ADMIN
        # ==================================================

        try:
            fecha_respuesta = (
                self._obtener_fecha_hora_post(
                    request,
                    "fecha_respuesta_cliente",
                )
            )

        except ValidationError as exc:
            self._mostrar_error(
                request,
                exc,
            )

            return self._redirect_change(
                proyecto
            )

        # ==================================================
        # SERVICE
        # ==================================================

        try:
            registrar_aceptacion_proyecto(
                proyecto=proyecto,
                usuario=request.user,
                fecha=fecha_respuesta,
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
                    "Aceptación registrada correctamente. "
                    "El proyecto quedó aprobado."
                ),
                level=messages.SUCCESS,
            )

        return self._redirect_change(
            proyecto
        )

    # ======================================================
    # RECHAZO
    # ======================================================

    def registrar_rechazo_view(
        self,
        request,
        object_id,
    ):
        """
        Registra el rechazo del proyecto.

        Prioridad para la fecha de respuesta:

        1. fecha escrita actualmente en el Admin;
        2. fecha previamente guardada;
        3. fecha/hora actual resuelta por el service.

        El proyecto no se cancela automáticamente.
        """

        respuesta = self._validar_post(
            request
        )

        if respuesta:
            return respuesta

        proyecto = self._obtener_proyecto(
            request,
            object_id,
        )

        if proyecto is None:
            return self._redirect_changelist()

        # ==================================================
        # PERMISO
        # ==================================================

        if not puede_registrar_rechazo_proyecto(
            request.user,
            proyecto,
        ):
            self.message_user(
                request,
                _(
                    "No puede registrar el rechazo "
                    "de este proyecto."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(
                proyecto
            )

        # ==================================================
        # FECHA ESCRITA EN ADMIN
        # ==================================================

        try:
            fecha_respuesta = (
                self._obtener_fecha_hora_post(
                    request,
                    "fecha_respuesta_cliente",
                )
            )

        except ValidationError as exc:
            self._mostrar_error(
                request,
                exc,
            )

            return self._redirect_change(
                proyecto
            )

        # ==================================================
        # SERVICE
        # ==================================================

        try:
            registrar_rechazo_proyecto(
                proyecto=proyecto,
                usuario=request.user,
                fecha=fecha_respuesta,
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
                    "Rechazo del cliente registrado "
                    "correctamente."
                ),
                level=messages.WARNING,
            )

        return self._redirect_change(
            proyecto
        )

    # ======================================================
    # GENERAR OT
    # ======================================================

    def generar_ot_view(
        self,
        request,
        object_id,
    ):
        """
        Genera una OT a partir de un proyecto aprobado
        y redirige directamente al Admin de la nueva OT.
        """

        respuesta = self._validar_post(
            request
        )

        if respuesta:
            return respuesta

        proyecto = self._obtener_proyecto(
            request,
            object_id,
        )

        if proyecto is None:
            return self._redirect_changelist()

        if not puede_generar_ot_desde_proyecto(
            request.user,
            proyecto,
        ):
            self.message_user(
                request,
                _(
                    "El proyecto no cumple las condiciones "
                    "para generar una orden de trabajo."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(
                proyecto
            )

        try:
            orden = (
                crear_orden_trabajo_desde_proyecto(
                    proyecto=proyecto,
                )
            )

        except ValidationError as exc:
            self._mostrar_error(
                request,
                exc,
            )

            return self._redirect_change(
                proyecto
            )

        self.message_user(
            request,
            _(
                "Orden de trabajo %(codigo)s "
                "generada correctamente."
            )
            % {
                "codigo": orden.codigo,
            },
            level=messages.SUCCESS,
        )

        return HttpResponseRedirect(
            reverse(
                "admin:"
                "orden_trabajo_ordentrabajo_change",
                args=(
                    orden.pk,
                ),
                current_app=self.admin_site.name,
            )
        )

    # ======================================================
    # CONTEXTO DEL FORMULARIO
    # ======================================================

    def changeform_view(
        self,
        request,
        object_id=None,
        form_url="",
        extra_context=None,
    ):
        """
        Expone al template únicamente las acciones
        permitidas para el proyecto actual.
        """

        extra_context = (
            extra_context
            or {}
        )

        proyecto = None

        if object_id:
            proyecto = self.get_object(
                request,
                object_id,
            )

        if proyecto:
            extra_context.update(
                {
                    "puede_registrar_recepcion_proyecto": (
                        puede_registrar_recepcion_proyecto(
                            request.user,
                            proyecto,
                        )
                    ),

                    "puede_planificar_proyecto": (
                        puede_planificar_proyecto(
                            request.user,
                            proyecto,
                        )
                    ),

                    "puede_registrar_envio_proyecto": (
                        puede_registrar_envio_proyecto(
                            request.user,
                            proyecto,
                        )
                    ),

                    "puede_registrar_aceptacion_proyecto": (
                        puede_registrar_aceptacion_proyecto(
                            request.user,
                            proyecto,
                        )
                    ),

                    "puede_registrar_rechazo_proyecto": (
                        puede_registrar_rechazo_proyecto(
                            request.user,
                            proyecto,
                        )
                    ),

                    "puede_generar_ot_desde_proyecto": (
                        puede_generar_ot_desde_proyecto(
                            request.user,
                            proyecto,
                        )
                    ),

                    "puede_finalizar_proyecto": (
                        puede_finalizar_proyecto(
                            request.user,
                            proyecto,
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
    # FINALIZAR PROYECTO
    # ======================================================

    def finalizar_proyecto_view(
        self,
        request,
        object_id,
    ):
        """
        Finaliza formalmente el Proyecto.

        Prioridad:

        1. fecha escrita actualmente en el Admin;
        2. fecha previamente guardada;
        3. fecha actual resuelta por el service.
        """

        respuesta = self._validar_post(
            request
        )

        if respuesta:
            return respuesta

        proyecto = self._obtener_proyecto(
            request,
            object_id,
        )

        if proyecto is None:
            return self._redirect_changelist()

        # ==================================================
        # PERMISO
        # ==================================================

        if not puede_finalizar_proyecto(
            request.user,
            proyecto,
        ):
            self.message_user(
                request,
                _(
                    "El proyecto no cumple las condiciones "
                    "necesarias para finalizarse."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(
                proyecto
            )

        # ==================================================
        # FECHA ESCRITA EN ADMIN
        # ==================================================

        try:
            fecha_finalizacion = (
                self._obtener_fecha_post(
                    request,
                    "fecha_finalizacion",
                )
            )

        except ValidationError as exc:
            self._mostrar_error(
                request,
                exc,
            )

            return self._redirect_change(
                proyecto
            )

        # ==================================================
        # SERVICE
        # ==================================================

        try:
            proyecto_finalizado = (
                finalizar_proyecto(
                    proyecto=proyecto,
                    fecha_finalizacion=(
                        fecha_finalizacion
                    ),
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
                    "Proyecto %(codigo)s finalizado "
                    "correctamente."
                )
                % {
                    "codigo": (
                        proyecto_finalizado.codigo
                    ),
                },
                level=messages.SUCCESS,
            )

        return self._redirect_change(
            proyecto
        )

    # ======================================================
    # GUARDADO DE INLINES MEDIANTE SERVICES
    # ======================================================

    @transaction.atomic
    def save_formset(
        self,
        request,
        form,
        formset,
        change,
    ):
        """
        Guarda los detalles del proyecto mediante
        los services de la app Proyecto.

        Los formsets correspondientes a otros modelos
        conservan el comportamiento estándar de Django.
        """

        if formset.model is not ProyectoDetalle:
            super().save_formset(
                request,
                form,
                formset,
                change,
            )

            return

        # Obtiene instancias nuevas y modificadas
        # sin persistirlas todavía.
        instancias = formset.save(
            commit=False,
        )

        # ==================================================
        # ELIMINACIONES
        # ==================================================

        for detalle_eliminado in (
            formset.deleted_objects
        ):
            eliminar_detalle_proyecto(
                detalle=detalle_eliminado,
            )

        # ==================================================
        # ALTAS Y MODIFICACIONES
        # ==================================================

        for instancia in instancias:

            if instancia.pk:
                detalle_guardado = (
                    actualizar_detalle_proyecto(
                        detalle=instancia,
                        dispositivo=(
                            instancia.dispositivo
                        ),
                        item_catalogo=(
                            instancia.item_catalogo
                        ),
                        descripcion=(
                            instancia.descripcion
                        ),
                        orden=instancia.orden,
                        cantidad=instancia.cantidad,
                        precio_unitario=(
                            instancia.precio_unitario
                        ),
                        descuento_importe=(
                            instancia.descuento_importe
                        ),
                        impuestos_importe=(
                            instancia.impuestos_importe
                        ),
                        observaciones=(
                            instancia.observaciones
                        ),
                        is_active=(
                            instancia.is_active
                        ),
                    )
                )

            else:
                detalle_guardado = (
                    crear_detalle_proyecto(
                        proyecto=form.instance,
                        dispositivo=(
                            instancia.dispositivo
                        ),
                        item_catalogo=(
                            instancia.item_catalogo
                        ),
                        descripcion=(
                            instancia.descripcion
                        ),
                        orden=instancia.orden,
                        cantidad=instancia.cantidad,
                        precio_unitario=(
                            instancia.precio_unitario
                        ),
                        descuento_importe=(
                            instancia.descuento_importe
                        ),
                        impuestos_importe=(
                            instancia.impuestos_importe
                        ),
                        observaciones=(
                            instancia.observaciones
                        ),
                        is_active=(
                            instancia.is_active
                        ),
                    )
                )

            self._sincronizar_detalle_inline(
                destino=instancia,
                origen=detalle_guardado,
            )

        # Actualmente ProyectoDetalle no posee M2M,
        # pero preservamos el flujo estándar de Django.
        formset.save_m2m()

    # ======================================================
    # SINCRONIZACIÓN DEL INLINE
    # ======================================================

    @staticmethod
    def _sincronizar_detalle_inline(
        *,
        destino: ProyectoDetalle,
        origen: ProyectoDetalle,
    ) -> None:
        """
        Sincroniza la instancia administrada por el formset
        con la instancia persistida por el service.
        """

        destino.pk = origen.pk
        destino.id = origen.id
        destino.codigo = origen.codigo

        destino.proyecto = origen.proyecto

        destino.dispositivo = (
            origen.dispositivo
        )

        destino.item_catalogo = (
            origen.item_catalogo
        )

        destino.tipo = origen.tipo
        destino.descripcion = origen.descripcion
        destino.orden = origen.orden
        destino.cantidad = origen.cantidad
        destino.unidad = origen.unidad

        destino.precio_unitario = (
            origen.precio_unitario
        )

        destino.descuento_importe = (
            origen.descuento_importe
        )

        destino.impuestos_importe = (
            origen.impuestos_importe
        )

        destino.subtotal = origen.subtotal
        destino.total = origen.total

        destino.observaciones = (
            origen.observaciones
        )

        destino.is_active = origen.is_active
        destino.created_at = origen.created_at
        destino.updated_at = origen.updated_at

        destino._state.adding = False
        destino._state.db = origen._state.db

    # ======================================================
    # COLUMNAS PERSONALIZADAS
    # ======================================================

    @admin.display(
        description=_("Detalles"),
        ordering="_cantidad_detalles",
    )
    def cantidad_detalles(
        self,
        obj,
    ):
        """
        Devuelve la cantidad de detalles del proyecto
        sin generar una consulta adicional por fila.
        """

        return obj._cantidad_detalles

    @admin.display(
        description=_("OT"),
        ordering="_cantidad_ordenes_trabajo",
    )
    def cantidad_ordenes_trabajo(
        self,
        obj,
    ):
        """
        Devuelve la cantidad de órdenes relacionadas
        sin generar una consulta adicional por fila.
        """

        return (
            obj._cantidad_ordenes_trabajo
        )

    # ======================================================
    # ACCIONES MASIVAS
    # ======================================================

    actions = ()