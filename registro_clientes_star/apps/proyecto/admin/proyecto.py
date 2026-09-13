from django import forms
from django.http import JsonResponse

from apps.catalogo.models import ItemCatalogo
from apps.dispositivo.models import Dispositivo

from apps.common.choices import (
    TipoProyectoDetalleChoices,
    UnidadMedidaChoices,
)

from django.contrib import admin, messages
from django.core.exceptions import (
    PermissionDenied,
    ValidationError,
)
from decimal import Decimal
from django.db import transaction
from django.db.models import Count
from django.http import (
    FileResponse,
    Http404,
    HttpResponseNotAllowed,
    HttpResponseRedirect,
)
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _

from apps.proyecto.models import (
    Proyecto,
    ProyectoArchivo,
    ProyectoDetalle,
)

from apps.proyecto.services import (
    actualizar_detalle_proyecto,
    adjuntar_archivo_proyecto,
    crear_detalle_proyecto,
    crear_orden_trabajo_desde_proyecto,
    eliminar_detalle_proyecto,
    finalizar_proyecto,
    planificar_proyecto,
    registrar_aceptacion_proyecto,
    registrar_envio_proyecto,
    registrar_recepcion_proyecto,
    registrar_rechazo_proyecto,
    retirar_archivo_proyecto,
    adjuntar_archivo_google_drive_proyecto,
    obtener_o_crear_carpeta_proyecto_drive,

    GoogleDriveServiceError,
    generar_url_autorizacion_drive,
    google_drive_esta_conectado,
    obtener_o_crear_carpeta_raiz_drive,
    procesar_callback_oauth_drive,
)

from apps.usuarios.permissions import (
    puede_adjuntar_archivo_proyecto,
    puede_editar_proyecto,
    puede_eliminar_proyecto,
    puede_finalizar_proyecto,
    puede_generar_ot_desde_proyecto,
    puede_planificar_proyecto,
    puede_registrar_aceptacion_proyecto,
    puede_registrar_envio_proyecto,
    puede_registrar_recepcion_proyecto,
    puede_registrar_rechazo_proyecto,
    puede_retirar_archivo_proyecto,
    puede_ver_archivo_proyecto,
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
from .proyecto_archivo import ProyectoArchivoInline

# ======================================================
# FORMULARIO - ADJUNTAR ARCHIVO
# ======================================================


class AdjuntarArchivoProyectoForm(
    forms.Form
):
    """
    Formulario utilizado para registrar
    documentación de un Proyecto.

    Permite elegir entre:

    - almacenamiento local;
    - Google Drive.
    """

    origen = forms.ChoiceField(
        choices=(),
        initial=(
            ProyectoArchivo
            .Origen
            .LOCAL
        ),
        required=True,
        widget=forms.RadioSelect,
        label=_("Origen"),
    )

    archivo = forms.FileField(
        required=True,
        label=_("Archivo"),
    )

    fecha_documento = (
        forms.SplitDateTimeField(
            required=False,
            label=_("Fecha del documento"),
            input_date_formats=[
                "%Y-%m-%d",
            ],
            input_time_formats=[
                "%H:%M",
                "%H:%M:%S",
            ],
            widget=forms.SplitDateTimeWidget(
                date_attrs={
                    "type": "date",
                },
                time_attrs={
                    "type": "time",
                    "step": "60",
                },
            ),
        )
    )

    descripcion = forms.CharField(
        required=False,
        max_length=150,
        label=_("Descripción"),
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": (
                    "Descripción breve "
                    "del documento..."
                ),
            }
        ),
    )

    def __init__(
        self,
        *args,
        google_drive_conectado=False,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        opciones = [
            (
                ProyectoArchivo
                .Origen
                .LOCAL,
                _("Archivo local"),
            ),
        ]

        if google_drive_conectado:
            opciones.append(
                (
                    ProyectoArchivo
                    .Origen
                    .GOOGLE_DRIVE,
                    _("Google Drive"),
                )
            )

        self.fields[
            "origen"
        ].choices = opciones

# ======================================================
# FORMULARIO - RETIRAR ARCHIVO
# ======================================================


class RetirarArchivoProyectoForm(forms.Form):
    """
    Formulario utilizado para retirar lógicamente
    un documento del Proyecto.

    No elimina el archivo ni el registro histórico.
    """

    fecha_retiro = forms.SplitDateTimeField(
        required=False,
        label=_("Fecha de retiro"),
        input_date_formats=[
            "%Y-%m-%d",
        ],
        input_time_formats=[
            "%H:%M",
            "%H:%M:%S",
        ],
        widget=forms.SplitDateTimeWidget(
            date_format="%Y-%m-%d",
            time_format="%H:%M",
            date_attrs={
                "type": "date",
            },
            time_attrs={
                "type": "time",
                "step": "60",
            },
        ),
        help_text=_(
            "Si se deja vacía se utilizará "
            "la fecha y hora actuales."
        ),
    )

    motivo_retiro = forms.CharField(
        required=True,
        label=_("Motivo del retiro"),
        max_length=250,
        widget=forms.Textarea(
            attrs={
                "rows": 2,
                "placeholder": _(
                    "Indique el motivo por el cual "
                    "se retira el documento..."
                ),
            }
        ),
    )


# ======================================================
# GOOGLE DRIVE - OAUTH
# ======================================================

GOOGLE_DRIVE_OAUTH_STATE_SESSION_KEY = (
    "proyecto_google_drive_oauth_state"
)

GOOGLE_DRIVE_OAUTH_PROJECT_SESSION_KEY = (
    "proyecto_google_drive_oauth_project"
)
GOOGLE_DRIVE_OAUTH_CODE_VERIFIER_SESSION_KEY = (
    "proyecto_google_drive_oauth_code_verifier"
)

# ======================================================
# PROYECTO ADMIN
# ======================================================

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
        ProyectoArchivoInline,
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
        correspondientes al flujo del Proyecto
        y a su gestión documental.
        """

        urls = super().get_urls()

        custom_urls = [

            # ==================================================
            # DETALLE DE PROYECTO
            # ==================================================
            path(
                "detalle-origen/metadata/",
                self.admin_site.admin_view(
                    self.detalle_origen_metadata_view
                ),
                name=(
                    "proyecto_proyecto_"
                    "detalle_origen_metadata"
                ),
            ),

            # ==================================================
            # GOOGLE DRIVE - OAUTH
            # ==================================================

            path(
                "google-drive/conectar/",
                self.admin_site.admin_view(
                    self.google_drive_conectar_view
                ),
                name=(
                    "proyecto_proyecto_"
                    "google_drive_conectar"
                ),
            ),

            path(
                "google-drive/oauth/callback/",
                self.admin_site.admin_view(
                    self.google_drive_oauth_callback_view
                ),
                name=(
                    "proyecto_proyecto_"
                    "google_drive_oauth_callback"
                ),
            ),

            # ==================================================
            # ARCHIVOS
            # ==================================================

            path(
                "<path:object_id>/archivos/",
                self.admin_site.admin_view(
                    self.gestionar_archivos_view
                ),
                name=(
                    "proyecto_proyecto_"
                    "gestionar_archivos"
                ),
            ),

            path(
                (
                    "<path:object_id>/archivos/"
                    "<int:archivo_id>/retirar/"
                ),
                self.admin_site.admin_view(
                    self.retirar_archivo_view
                ),
                name=(
                    "proyecto_proyecto_"
                    "retirar_archivo"
                ),
            ),

            path(
                (
                    "<path:object_id>/archivos/"
                    "<int:archivo_id>/descargar/"
                ),
                self.admin_site.admin_view(
                    self.descargar_archivo_view
                ),
                name=(
                    "proyecto_proyecto_"
                    "descargar_archivo"
                ),
            ),

            # ==================================================
            # DETALLES DEL PROYECTO
            # ==================================================

            path(
                "<path:object_id>/detalles/",
                self.admin_site.admin_view(
                    self.gestionar_detalles_view
                ),
                name=(
                    "proyecto_proyecto_"
                    "gestionar_detalles"
                ),
            ),


            # ==================================================
            # RECEPCIÓN
            # ==================================================

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

            # ==================================================
            # PLANIFICACIÓN
            # ==================================================

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

            # ==================================================
            # ENVÍO
            # ==================================================

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

            # ==================================================
            # ACEPTACIÓN
            # ==================================================

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

            # ==================================================
            # RECHAZO
            # ==================================================

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

            # ==================================================
            # FINALIZACIÓN
            # ==================================================

            path(
                "<path:object_id>/finalizar/",
                self.admin_site.admin_view(
                    self.finalizar_proyecto_view
                ),
                name=(
                    "proyecto_proyecto_finalizar"
                ),
            ),

            # ==================================================
            # GENERAR OT
            # ==================================================

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
    # HELPERS DE REDIRECCION
    # ======================================================
    
    def _redirect_gestion_archivos(
        self,
        proyecto,
    ):
        """
        Redirige a la pantalla de gestión
        documental del Proyecto.
        """

        url = reverse(
            (
                "admin:"
                "proyecto_proyecto_"
                "gestionar_archivos"
            ),
            args=(
                proyecto.pk,
            ),
            current_app=self.admin_site.name,
        )

        return HttpResponseRedirect(
            url
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
                    # ==========================================
                    # ARCHIVOS
                    # ==========================================

                    "puede_ver_archivos_proyecto": (
                        puede_ver_proyecto(
                            request.user,
                            proyecto,
                        )
                    ),

                    "puede_adjuntar_archivo_proyecto": (
                        puede_adjuntar_archivo_proyecto(
                            request.user,
                            proyecto,
                        )
                    ),

                    # ==========================================
                    # DETALLES
                    # ==========================================

                    "puede_ver_detalles_proyecto": (
                        puede_ver_proyecto(
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
    # GESTIÓN DE ARCHIVOS
    # ======================================================

    def gestionar_archivos_view(
        self,
        request,
        object_id,
    ):
        """
        Gestiona el historial documental de un Proyecto.

        Permite:

        - consultar documentos;
        - adjuntar documentación;
        - descargar documentos;
        - visualizar documentos retirados;
        - acceder al retiro lógico según permisos.

        Flujo:

            Admin
                ↓
            Permissions
                ↓
            Services
                ↓
            ProyectoArchivo
        """

        # ==================================================
        # PROYECTO
        # ==================================================

        proyecto = self._obtener_proyecto(
            request,
            object_id,
        )

        if proyecto is None:
            return self._redirect_changelist()

        # ==================================================
        # PERMISO DE LECTURA
        # ==================================================

        if not puede_ver_proyecto(
            request.user,
            proyecto,
        ):
            raise PermissionDenied

        # ==================================================
        # PERMISO DE CARGA
        # ==================================================

        puede_adjuntar = (
            puede_adjuntar_archivo_proyecto(
                request.user,
                proyecto,
            )
        )
        
        # ==================================================
        # GOOGLE
        # ==================================================

        google_drive_conectado = (
            google_drive_esta_conectado()
        )

        # ==================================================
        # CARPETA GOOGLE DRIVE DEL PROYECTO
        # ==================================================

        google_drive_carpeta_url = None

        if google_drive_conectado:

            try:

                carpeta_drive = (
                    obtener_o_crear_carpeta_proyecto_drive(
                        proyecto
                    )
                )

                google_drive_carpeta_url = (
                    carpeta_drive.get(
                        "webViewLink"
                    )
                )

            except GoogleDriveServiceError as exc:

                messages.warning(
                    request,
                    (
                        "Google Drive está conectado, "
                        "pero no fue posible obtener la "
                        f"carpeta del Proyecto: {exc}"
                    ),
                )

        # ==================================================
        # FORMULARIO
        # ==================================================

        form = AdjuntarArchivoProyectoForm(
            request.POST or None,
            request.FILES or None,
            google_drive_conectado=(
                google_drive_conectado
            ),
        )

        # ==================================================
        # ALTA
        # ==================================================

        if request.method == "POST":

            if not puede_adjuntar:
                raise PermissionDenied

            if form.is_valid():

                origen = (
                    form.cleaned_data[
                        "origen"
                    ]
                )

                try:

                    # ==================================================
                    # GOOGLE DRIVE
                    # ==================================================

                    if (
                        origen
                        == ProyectoArchivo.Origen.GOOGLE_DRIVE
                    ):

                        adjuntar_archivo_google_drive_proyecto(
                            proyecto=proyecto,
                            usuario=request.user,
                            archivo=(
                                form.cleaned_data[
                                    "archivo"
                                ]
                            ),
                            descripcion=(
                                form.cleaned_data[
                                    "descripcion"
                                ]
                            ),
                            fecha_documento=(
                                form.cleaned_data[
                                    "fecha_documento"
                                ]
                            ),
                        )

                    # ==================================================
                    # LOCAL
                    # ==================================================

                    else:

                        adjuntar_archivo_proyecto(
                            proyecto=proyecto,
                            usuario=request.user,
                            archivo=(
                                form.cleaned_data[
                                    "archivo"
                                ]
                            ),
                            descripcion=(
                                form.cleaned_data[
                                    "descripcion"
                                ]
                            ),
                            fecha_documento=(
                                form.cleaned_data[
                                    "fecha_documento"
                                ]
                            ),
                        )

                except ValidationError as exc:

                    if hasattr(
                        exc,
                        "message_dict",
                    ):

                        for campo, errores in (
                            exc.message_dict.items()
                        ):

                            if campo in form.fields:

                                for error in errores:
                                    form.add_error(
                                        campo,
                                        error,
                                    )

                            else:

                                for error in errores:
                                    form.add_error(
                                        None,
                                        error,
                                    )

                    else:

                        form.add_error(
                            None,
                            str(exc),
                        )

                except GoogleDriveServiceError as exc:

                    form.add_error(
                        None,
                        str(exc),
                    )

                else:

                    if (
                        origen
                        == ProyectoArchivo.Origen.GOOGLE_DRIVE
                    ):

                        messages.success(
                            request,
                            _(
                                "El archivo fue registrado "
                                "correctamente en Google Drive."
                            ),
                        )

                    else:

                        messages.success(
                            request,
                            _(
                                "El archivo fue adjuntado "
                                "correctamente."
                            ),
                        )

                    return self._redirect_gestion_archivos(
                        proyecto
                    )

        # ==================================================
        # HISTORIAL
        # ==================================================

        archivos = (
            ProyectoArchivo.objects
            .filter(
                proyecto=proyecto,
            )
            .select_related(
                "usuario",
                "usuario_retiro",
            )
            .order_by(
                "-is_active",
                "-fecha_documento",
                "-created_at",
            )
        )

        # ==================================================
        # PERMISOS POR DOCUMENTO
        # ==================================================

        archivos_contexto = []

        for archivo_proyecto in archivos:

            archivos_contexto.append(
                {
                    "archivo": archivo_proyecto,

                    "puede_ver": (
                        puede_ver_archivo_proyecto(
                            request.user,
                            archivo_proyecto,
                        )
                    ),

                    "puede_retirar": (
                        puede_retirar_archivo_proyecto(
                            request.user,
                            archivo_proyecto,
                        )
                    ),
                }
            )

        # ==================================================
        # CONTEXTO
        # ==================================================

        request.current_app = (
            self.admin_site.name
        )

        context = {
            **self.admin_site.each_context(
                request
            ),

            "title": _(
                "Archivos de %(proyecto)s"
            )
            % {
                "proyecto": proyecto.codigo,
            },

            "opts": self.model._meta,

            "original": proyecto,

            "proyecto": proyecto,

            "form": form,

            "media": (
                self.media
                + form.media
            ),

            "puede_adjuntar": (
                puede_adjuntar
            ),

            "archivos": (
                archivos_contexto
            ),

            "url_volver": reverse(
                "admin:proyecto_proyecto_change",
                args=(
                    proyecto.pk,
                ),
                current_app=self.admin_site.name,
            ),

            "google_drive_conectado": (
                google_drive_esta_conectado()
            ),
            
            "google_drive_carpeta_url": (
                google_drive_carpeta_url
            ),

            "puede_conectar_google_drive": (
                request.user.is_active
                and request.user.is_superuser
            ),



        }

        return TemplateResponse(
            request,
            (
                "admin/proyecto/"
                "proyecto/"
                "gestionar_archivos.html"
            ),
            context,
        )

    # ======================================================
    # RETIRAR ARCHIVO
    # ======================================================

    def retirar_archivo_view(
        self,
        request,
        object_id,
        archivo_id,
    ):
        """
        Retira lógicamente un documento del Proyecto.

        No elimina:

        - el registro;
        - el archivo físico;
        - el usuario original;
        - la fecha documental;
        - created_at.
        """

        respuesta = self._validar_post(
            request
        )

        if respuesta:
            return respuesta

        # ==================================================
        # PROYECTO
        # ==================================================

        proyecto = self._obtener_proyecto(
            request,
            object_id,
        )

        if proyecto is None:
            return self._redirect_changelist()

        # ==================================================
        # ARCHIVO
        # ==================================================

        archivo_proyecto = (
            ProyectoArchivo.objects
            .select_related(
                "proyecto",
                "usuario",
                "usuario_retiro",
            )
            .filter(
                pk=archivo_id,
                proyecto=proyecto,
            )
            .first()
        )

        if archivo_proyecto is None:
            raise Http404(
                _("Archivo no encontrado.")
            )

        # ==================================================
        # PERMISO
        # ==================================================

        if not puede_retirar_archivo_proyecto(
            request.user,
            archivo_proyecto,
        ):
            raise PermissionDenied

        # ==================================================
        # FORMULARIO
        # ==================================================

        form = RetirarArchivoProyectoForm(
            request.POST
        )

        if not form.is_valid():

            for errores in form.errors.values():

                for error in errores:

                    self.message_user(
                        request,
                        error,
                        level=messages.ERROR,
                    )

            return (
                self._redirect_gestion_archivos(
                    proyecto
                )
            )

        # ==================================================
        # SERVICE
        # ==================================================

        try:
            retirar_archivo_proyecto(
                archivo_proyecto=(
                    archivo_proyecto
                ),
                usuario=request.user,
                motivo=(
                    form.cleaned_data[
                        "motivo_retiro"
                    ]
                ),
                fecha_retiro=(
                    form.cleaned_data[
                        "fecha_retiro"
                    ]
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
                    "Archivo retirado correctamente "
                    "del flujo documental."
                ),
                level=messages.SUCCESS,
            )

        return (
            self._redirect_gestion_archivos(
                proyecto
            )
        )

    # ======================================================
    # DESCARGAR ARCHIVO
    # ======================================================

    def descargar_archivo_view(
        self,
        request,
        object_id,
        archivo_id,
    ):
        """
        Entrega un documento solamente después
        de comprobar que el usuario posee permiso
        sobre el Proyecto.

        Los documentos retirados continúan formando
        parte del historial y pueden descargarse si
        el usuario conserva permiso de lectura.
        """

        # ==================================================
        # PROYECTO
        # ==================================================

        proyecto = self._obtener_proyecto(
            request,
            object_id,
        )

        if proyecto is None:
            raise Http404

        # ==================================================
        # ARCHIVO
        # ==================================================

        archivo_proyecto = (
            ProyectoArchivo.objects
            .select_related(
                "proyecto",
                "usuario",
            )
            .filter(
                pk=archivo_id,
                proyecto=proyecto,
            )
            .first()
        )

        if archivo_proyecto is None:
            raise Http404(
                _("Archivo no encontrado.")
            )

        # ==================================================
        # PERMISO
        # ==================================================

        if not puede_ver_archivo_proyecto(
            request.user,
            archivo_proyecto,
        ):
            raise PermissionDenied

        # ==================================================
        # ARCHIVO FÍSICO
        # ==================================================

        if not archivo_proyecto.archivo:
            raise Http404(
                _("El archivo no está disponible.")
            )

        try:
            archivo_abierto = (
                archivo_proyecto.archivo.open(
                    "rb"
                )
            )

        except (
            FileNotFoundError,
            OSError,
        ):

            raise Http404(
                _(
                    "El archivo físico no se encuentra "
                    "disponible."
                )
            )

        # ==================================================
        # RESPUESTA
        # ==================================================

        return FileResponse(
            archivo_abierto,
            as_attachment=True,
            filename=(
                archivo_proyecto.nombre_archivo
            ),
        )

    # ======================================================
    # GOOGLE DRIVE - CONECTAR
    # ======================================================

    def google_drive_conectar_view(
        self,
        request,
    ):
        """
        Inicia la autorización OAuth de Google Drive.

        La conexión de la cuenta Google es una operación
        administrativa global, por lo que solamente puede
        realizarla un superusuario.

        Si la conexión se inició desde un Proyecto,
        conserva su ID en sesión para regresar a la
        Gestión de archivos después del callback.
        """

        # ==================================================
        # SEGURIDAD
        # ==================================================

        if (
            not request.user.is_active
            or not request.user.is_superuser
        ):
            raise PermissionDenied

        # ==================================================
        # CALLBACK
        # ==================================================

        callback_url = reverse(
            (
                "admin:"
                "proyecto_proyecto_"
                "google_drive_oauth_callback"
            ),
            current_app=self.admin_site.name,
        )

        redirect_uri = (
            request.build_absolute_uri(
                callback_url
            )
        )

        # ==================================================
        # GENERAR AUTORIZACIÓN
        # ==================================================

        try:

            authorization_url, state, code_verifier = (
                generar_url_autorizacion_drive(
                    redirect_uri=redirect_uri,
                )
            )

        except GoogleDriveServiceError as exc:

            messages.error(
                request,
                str(exc),
            )

            return self._redirect_changelist()

        # ==================================================
        # GUARDAR STATE + PKCE
        # ==================================================

        request.session[
            GOOGLE_DRIVE_OAUTH_STATE_SESSION_KEY
        ] = state

        request.session[
            GOOGLE_DRIVE_OAUTH_CODE_VERIFIER_SESSION_KEY
        ] = code_verifier

        # ==================================================
        # PROYECTO DE ORIGEN
        # ==================================================

        proyecto_id = (
            request.GET.get(
                "proyecto"
            )
        )

        if proyecto_id:

            request.session[
                GOOGLE_DRIVE_OAUTH_PROJECT_SESSION_KEY
            ] = str(
                proyecto_id
            )

        else:

            request.session.pop(
                GOOGLE_DRIVE_OAUTH_PROJECT_SESSION_KEY,
                None,
            )

        # ==================================================
        # GOOGLE
        # ==================================================

        return HttpResponseRedirect(
            authorization_url
        )

    # ======================================================
    # GOOGLE DRIVE - CALLBACK OAUTH
    # ======================================================

    def google_drive_oauth_callback_view(
        self,
        request,
    ):
        """
        Procesa la respuesta OAuth enviada por Google.

        Valida:

        - usuario administrativo;
        - error devuelto por Google;
        - parámetro state;
        - intercambio del código;
        - conexión real con Drive.

        Después de autorizar crea/obtiene la carpeta
        raíz de documentos de la aplicación.
        """

        # ==================================================
        # SEGURIDAD
        # ==================================================

        if (
            not request.user.is_active
            or not request.user.is_superuser
        ):
            raise PermissionDenied

        # ==================================================
        # PROYECTO DE RETORNO
        # ==================================================

        proyecto_id = (
            request.session.pop(
                GOOGLE_DRIVE_OAUTH_PROJECT_SESSION_KEY,
                None,
            )
        )

        # ==================================================
        # ERROR DEVUELTO POR GOOGLE
        # ==================================================

        error_google = (
            request.GET.get(
                "error"
            )
        )

        if error_google:

            request.session.pop(
                GOOGLE_DRIVE_OAUTH_STATE_SESSION_KEY,
                None,
            )

            request.session.pop(
                GOOGLE_DRIVE_OAUTH_CODE_VERIFIER_SESSION_KEY,
                None,
            )

            messages.error(
                request,
                (
                    "La autorización de Google Drive "
                    f"no se completó: {error_google}."
                ),
            )

            return self._redirect_changelist()

        # ==================================================
        # STATE ESPERADO
        # ==================================================

        state_esperado = (
            request.session.pop(
                GOOGLE_DRIVE_OAUTH_STATE_SESSION_KEY,
                None,
            )
        )

        state_recibido = (
            request.GET.get(
                "state"
            )
        )
        # ==================================================
        # PKCE
        # ==================================================

        code_verifier = (
            request.session.pop(
                GOOGLE_DRIVE_OAUTH_CODE_VERIFIER_SESSION_KEY,
                None,
            )
        )

        if (
            not state_esperado
            or not state_recibido
            or state_recibido != state_esperado
        ):

            messages.error(
                request,
                (
                    "La respuesta OAuth de Google Drive "
                    "no superó la validación de seguridad."
                ),
            )

            return self._redirect_changelist()

        if not code_verifier:

            messages.error(
                request,
                (
                    "No se encontró el código de seguridad "
                    "PKCE utilizado para conectar Google Drive."
                ),
            )

            return self._redirect_changelist()

        # ==================================================
        # CALLBACK URI
        # ==================================================

        callback_url = reverse(
            (
                "admin:"
                "proyecto_proyecto_"
                "google_drive_oauth_callback"
            ),
            current_app=self.admin_site.name,
        )

        redirect_uri = (
            request.build_absolute_uri(
                callback_url
            )
        )

        # ==================================================
        # PROCESAR GOOGLE OAUTH
        # ==================================================

        try:

            procesar_callback_oauth_drive(
                redirect_uri=redirect_uri,
                authorization_response=(
                    request.build_absolute_uri()
                ),
                state=state_esperado,
                code_verifier=code_verifier,
            )

            # ==============================================
            # PRUEBA REAL DE DRIVE
            # ==============================================

            carpeta_raiz = (
                obtener_o_crear_carpeta_raiz_drive()
            )

        except GoogleDriveServiceError as exc:

            messages.error(
                request,
                str(exc),
            )

            return self._redirect_changelist()

        # ==================================================
        # OK
        # ==================================================

        messages.success(
            request,
            (
                "Google Drive fue conectado correctamente. "
                "Carpeta principal: "
                f"{carpeta_raiz.get('name', 'Google Drive')}."
            ),
        )

        # ==================================================
        # REGRESAR AL PROYECTO
        # ==================================================

        if proyecto_id:

            proyecto = (
                self.get_queryset(request)
                .filter(
                    pk=proyecto_id
                )
                .first()
            )

            if proyecto is not None:
                return self._redirect_gestion_archivos(
                    proyecto
                )

        return self._redirect_changelist()

    # ======================================================
    # GESTIÓN DE DETALLES
    # ======================================================

    def _redirect_gestion_detalles(
        self,
        proyecto,
    ):
        """
        Redirige a la pantalla de gestión
        de detalles del Proyecto.
        """

        url = reverse(
            "admin:proyecto_proyecto_gestionar_detalles",
            args=(
                proyecto.pk,
            ),
            current_app=self.admin_site.name,
        )

        return HttpResponseRedirect(
            url
        )

    # ======================================================
    # GUARDADO DE DETALLES
    # ======================================================

    @transaction.atomic
    def _guardar_formset_detalles(
        self,
        *,
        request,
        proyecto,
        formset,
    ):
        """
        Persiste un formset de ProyectoDetalle
        utilizando exclusivamente los services.

        Es utilizado tanto por el Admin tradicional
        como por la pantalla Gestionar detalles.
        """

        instancias = formset.save(
            commit=False
        )

        # ==================================================
        # MAPEAR FORMULARIO -> INSTANCIA
        # ==================================================

        formularios_por_instancia = {
            id(detalle_form.instance): detalle_form
            for detalle_form in formset.forms
            if hasattr(
                detalle_form,
                "cleaned_data",
            )
        }

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
        # ALTAS / MODIFICACIONES
        # ==================================================

        for instancia in instancias:

            detalle_form = (
                formularios_por_instancia.get(
                    id(instancia)
                )
            )

            changed_data = set()

            if detalle_form is not None:
                changed_data = set(
                    detalle_form.changed_data
                )

            # ==================================================
            # CAMBIO DE ORIGEN
            # ==================================================

            cambio_origen = bool(
                {
                    "dispositivo",
                    "item_catalogo",
                }
                & changed_data
            )

            # ==================================================
            # DESCRIPCIÓN
            # ==================================================

            descripcion = (
                instancia.descripcion
            )

            if (
                cambio_origen
                and "descripcion" not in changed_data
            ):
                descripcion = ""

            # ==================================================
            # PRECIO
            # ==================================================

            precio_unitario = (
                instancia.precio_unitario
            )

            if (
                cambio_origen
                and "precio_unitario" not in changed_data
            ):
                precio_unitario = Decimal(
                    "0.00"
                )

            # ==================================================
            # ACTUALIZAR
            # ==================================================

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
                        descripcion=descripcion,
                        orden=instancia.orden,
                        cantidad=(
                            instancia.cantidad
                        ),
                        precio_unitario=(
                            precio_unitario
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
                        reiniciar_desde_origen=(
                            cambio_origen
                        ),
                    )
                )

            # ==================================================
            # CREAR
            # ==================================================

            else:

                detalle_guardado = (
                    crear_detalle_proyecto(
                        proyecto=proyecto,
                        dispositivo=(
                            instancia.dispositivo
                        ),
                        item_catalogo=(
                            instancia.item_catalogo
                        ),
                        descripcion=(
                            instancia.descripcion
                        ),

                        # El service asigna el orden
                        # definitivo bajo bloqueo.
                        orden=None,

                        cantidad=(
                            instancia.cantidad
                        ),
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

        formset.save_m2m()


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
        Persiste los detalles mediante services.

        Los demás formsets conservan el
        comportamiento estándar de Django.
        """

        if formset.model is not ProyectoDetalle:

            super().save_formset(
                request,
                form,
                formset,
                change,
            )

            return

        self._guardar_formset_detalles(
            request=request,
            proyecto=form.instance,
            formset=formset,
        )

    # ======================================================
    # DETALLE DEL PROYECTO - METADATOS DEL ORIGEN
    # ======================================================

    def detalle_origen_metadata_view(
        self,
        request,
    ):
        """
        Devuelve los datos necesarios para completar
        visualmente un ProyectoDetalle.

        Orígenes soportados:

        - dispositivo
        - catalogo
        """

        if not self.has_view_permission(
            request
        ):
            raise PermissionDenied

        origen = (
            request.GET.get(
                "origen",
                ""
            )
            .strip()
            .lower()
        )

        objeto_id = (
            request.GET.get(
                "id"
            )
        )

        try:
            objeto_id = int(
                objeto_id
            )

        except (
            TypeError,
            ValueError,
        ):
            return JsonResponse(
                {
                    "error": (
                        "Identificador inválido."
                    )
                },
                status=400,
            )

        # ==================================================
        # DISPOSITIVO
        # ==================================================

        if origen == "dispositivo":

            objeto = (
                Dispositivo.objects
                .filter(
                    pk=objeto_id
                )
                .first()
            )

            if objeto is None:
                return JsonResponse(
                    {
                        "error": (
                            "Dispositivo no encontrado."
                        )
                    },
                    status=404,
                )

            precio = (
                objeto.precio_mercado
                or Decimal("0.00")
            )

            return JsonResponse(
                {
                    "descripcion": (
                        objeto.nombre_comercial
                        or str(objeto)
                    ),

                    "precio_unitario": str(
                        precio
                    ),

                    "tipo": (
                        TipoProyectoDetalleChoices
                        .DISPOSITIVO
                    ),

                    "tipo_label": (
                        TipoProyectoDetalleChoices
                        .DISPOSITIVO
                        .label
                    ),

                    "unidad": (
                        UnidadMedidaChoices
                        .UNIDAD
                    ),

                    "unidad_label": (
                        UnidadMedidaChoices
                        .UNIDAD
                        .label
                    ),
                }
            )

        # ==================================================
        # ÍTEM DE CATÁLOGO
        # ==================================================

        if origen == "catalogo":

            objeto = (
                ItemCatalogo.objects
                .filter(
                    pk=objeto_id
                )
                .first()
            )

            if objeto is None:
                return JsonResponse(
                    {
                        "error": (
                            "Ítem de catálogo no encontrado."
                        )
                    },
                    status=404,
                )

            precio = (
                objeto.precio_venta
                or Decimal("0.00")
            )

            return JsonResponse(
                {
                    "descripcion": (
                        objeto.nombre
                    ),

                    "precio_unitario": str(
                        precio
                    ),

                    "tipo": (
                        objeto.tipo
                    ),

                    "tipo_label": (
                        objeto.get_tipo_display()
                    ),

                    "unidad": (
                        objeto.unidad
                    ),

                    "unidad_label": (
                        objeto.get_unidad_display()
                    ),
                }
            )

        return JsonResponse(
            {
                "error": (
                    "Origen no válido."
                )
            },
            status=400,
        )


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
    # GESTIONAR DETALLES
    # ======================================================

    def gestionar_detalles_view(
        self,
        request,
        object_id,
    ):
        """
        Pantalla específica para administrar los
        detalles comerciales y técnicos de un Proyecto.
        """

        # ==================================================
        # PROYECTO
        # ==================================================

        proyecto = self._obtener_proyecto(
            request,
            object_id,
        )

        if proyecto is None:
            return self._redirect_changelist()

        # ==================================================
        # VISUALIZACIÓN
        # ==================================================

        if not puede_ver_proyecto(
            request.user,
            proyecto,
        ):
            raise PermissionDenied

        puede_editar = (
            puede_editar_proyecto(
                request.user,
                proyecto,
            )
        )

        puede_ver_costos = (
            puede_ver_costos_proyecto(
                request.user
            )
        )

        # ==================================================
        # INLINE
        # ==================================================
        #
        # Reutilizamos ProyectoDetalleInline para conservar:
        #
        # - autocomplete;
        # - permisos;
        # - campos readonly;
        # - ProyectoDetalleForm;
        # - ProyectoDetalleInlineFormSet;
        # - orden automático.
        # ==================================================

        inline = ProyectoDetalleInline(
            self.model,
            self.admin_site,
        )

        FormSet = inline.get_formset(
            request,
            proyecto,
        )

        prefix = (
            FormSet.get_default_prefix()
        )

        # ==================================================
        # FORMSET
        # ==================================================

        if request.method == "POST":

            if not puede_editar:
                raise PermissionDenied

            formset = FormSet(
                data=request.POST,
                files=request.FILES,
                instance=proyecto,
                prefix=prefix,
            )

        else:

            formset = FormSet(
                instance=proyecto,
                prefix=prefix,
            )

        # ==================================================
        # GUARDAR
        # ==================================================

        if (
            request.method == "POST"
            and formset.is_valid()
        ):

            try:

                self._guardar_formset_detalles(
                    request=request,
                    proyecto=proyecto,
                    formset=formset,
                )

            except ValidationError as exc:

                self._mostrar_error(
                    request,
                    exc,
                )

            else:

                messages.success(
                    request,
                    _(
                        "Los detalles del proyecto "
                        "fueron actualizados correctamente."
                    ),
                )

                return (
                    self._redirect_gestion_detalles(
                        proyecto
                    )
                )

        # ==================================================
        # MEDIA
        # ==================================================

        media = (
            self.media
            + inline.media
        )

        for detalle_form in formset.forms:
            media = (
                media
                + detalle_form.media
            )

        media = (
            media
            + formset.empty_form.media
        )

        # ==================================================
        # URL VOLVER
        # ==================================================

        url_volver = reverse(
            "admin:proyecto_proyecto_change",
            args=(
                proyecto.pk,
            ),
            current_app=self.admin_site.name,
        )

        # ==================================================
        # CONTEXTO
        # ==================================================

        context = {
            **self.admin_site.each_context(
                request
            ),

            "title": _(
                "Gestionar detalles del proyecto"
            ),

            "opts": self.model._meta,

            "original": proyecto,

            "proyecto": proyecto,

            "formset": formset,

            "media": media,

            "puede_editar": (
                puede_editar
            ),

            "puede_ver_costos": (
                puede_ver_costos
            ),

            "url_volver": (
                url_volver
            ),
        }

        return TemplateResponse(
            request,
            (
                "admin/proyecto/proyecto/"
                "gestionar_detalles.html"
            ),
            context,
        )

    # ======================================================
    # ACCIONES MASIVAS
    # ======================================================

    actions = ()