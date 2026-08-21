from django import forms
from django.contrib import admin, messages
from django.core.exceptions import (
    ObjectDoesNotExist,
    PermissionDenied,
    ValidationError,
)
from django.http import (
    HttpResponseNotAllowed,
    HttpResponseRedirect,
    FileResponse,
    Http404,
)
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.orden_trabajo.models import (
    OrdenTrabajo,
    OrdenTrabajoSeguimiento,
    OrdenTrabajoTecnico,
    OrdenTrabajoArchivo,
)

from apps.orden_trabajo.services import (
    adjuntar_archivo_ot,
    retirar_archivo_ot,
    asignar_tecnico_ot,
    crear_instalacion_desde_ot,
    desasignar_tecnico_ot,
    establecer_tecnico_principal_ot,
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
    registrar_seguimiento_ot,
)

from apps.usuarios.models import Usuario

from apps.usuarios.permissions import (
    puede_asignar_tecnico_ot,
    puede_cobrar_ot,
    puede_crear_instalacion_desde_ot,
    puede_desasignar_tecnico_ot,
    puede_establecer_tecnico_principal_ot,
    puede_facturar_ot,
    puede_finalizar_ot,
    puede_gestionar_tecnicos_ot,
    puede_iniciar_ot,
    puede_pausar_ot,
    puede_programar_ot,
    puede_reanudar_ot,
    puede_registrar_aceptacion_ot,
    puede_registrar_envio_ot,
    puede_registrar_recepcion_ot,
    puede_registrar_rechazo_ot,
    puede_registrar_seguimiento_ot,
    puede_adjuntar_archivo_ot,
    puede_retirar_archivo_ot,
    puede_ver_archivo_ot,
)

from apps.usuarios.services.roles import (
    es_tecnico,
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


# ======================================================
# FORMULARIO - ASIGNAR TÉCNICO
# ======================================================


class AsignarTecnicoOTForm(forms.Form):
    """
    Formulario administrativo para asignar
    un técnico a una Orden de Trabajo.

    La validación definitiva permanece
    centralizada en asignar_tecnico_ot().
    """

    tecnico = forms.ModelChoiceField(
        queryset=Usuario.objects.none(),
        label=_("Técnico"),
        help_text=_(
            "Seleccione el técnico que participará "
            "en la orden de trabajo."
        ),
    )

    es_principal = forms.BooleanField(
        required=False,
        label=_("Técnico principal"),
        help_text=_(
            "Marcar si será el responsable principal "
            "de la ejecución."
        ),
    )

    fecha_asignacion = forms.SplitDateTimeField(
        required=False,
        label=_("Fecha de asignación"),
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
                "class": "vDateField",
            },
            time_attrs={
                "type": "time",
                "class": "vTimeField",
                "step": "60",
            },
        ),
        help_text=_(
            "Puede indicar la fecha y hora real "
            "de asignación. Si se deja vacío, "
            "se utilizará la fecha y hora actuales."
        ),
    )

    observaciones = forms.CharField(
        required=False,
        label=_("Observaciones"),
        widget=forms.Textarea(
            attrs={
                "rows": 3,
            }
        ),
    )

    def __init__(
        self,
        *args,
        orden_trabajo=None,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        # ==================================================
        # USUARIOS ACTIVOS
        # ==================================================

        usuarios = (
            Usuario.objects
            .filter(
                is_active=True,
            )
            .prefetch_related(
                "groups",
            )
            .order_by(
                "last_name",
                "first_name",
                "email",
            )
        )

        # ==================================================
        # TÉCNICOS ACTUALMENTE ASIGNADOS
        # ==================================================

        ids_asignados = set()

        if orden_trabajo:
            ids_asignados = set(
                orden_trabajo.tecnicos
                .filter(
                    is_active=True,
                )
                .values_list(
                    "tecnico_id",
                    flat=True,
                )
            )

        # ==================================================
        # SOLO USUARIOS CON ROL TÉCNICO
        # ==================================================

        ids_tecnicos = [
            usuario.pk
            for usuario in usuarios
            if (
                es_tecnico(usuario)
                and usuario.pk not in ids_asignados
            )
        ]

        self.fields["tecnico"].queryset = (
            Usuario.objects
            .filter(
                pk__in=ids_tecnicos,
                is_active=True,
            )
            .order_by(
                "last_name",
                "first_name",
                "email",
            )
        )


# ======================================================
# FORMULARIO - REGISTRAR SEGUIMIENTO
# ======================================================


class RegistrarSeguimientoOTForm(forms.Form):
    """
    Formulario administrativo para registrar
    una novedad o avance de una Orden de Trabajo.

    El usuario que registra el seguimiento
    se obtiene siempre desde request.user.
    """

    fecha_seguimiento = forms.SplitDateTimeField(
        required=False,
        label=_("Fecha del seguimiento"),
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
            "Indique cuándo ocurrió la novedad. "
            "Si queda vacío se utilizará "
            "la fecha y hora actuales."
        ),
    )

    comentario = forms.CharField(
        label=_("Comentario"),
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "placeholder": _(
                    "Describa la novedad, avance, "
                    "inconveniente o tarea realizada..."
                ),
            }
        ),
        help_text=_(
            "El seguimiento quedará registrado "
            "como parte del historial de la OT."
        ),
    )

# ======================================================
# FORMULARIO - ADJUNTAR ARCHIVO
# ======================================================


class AdjuntarArchivoOTForm(forms.Form):
    """
    Formulario administrativo para adjuntar
    documentación a una Orden de Trabajo.

    El usuario que realiza la carga se obtiene
    siempre desde request.user.
    """

    archivo = forms.FileField(
        required=True,
        label=_("Archivo"),
        help_text=_(
            "Seleccione el documento, fotografía "
            "o evidencia que desea adjuntar."
        ),
    )

    fecha_documento = forms.SplitDateTimeField(
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
            "Fecha y hora correspondiente al documento "
            "o evidencia. Si se deja vacío se utilizará "
            "la fecha y hora actuales."
        ),
    )

    descripcion = forms.CharField(
        required=False,
        label=_("Descripción"),
        max_length=150,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": _(
                    "Descripción breve del documento "
                    "o evidencia..."
                ),
            }
        ),
        help_text=_(
            "Descripción breve del contenido del archivo."
        ),
    )


# ======================================================
# FORMULARIO - RETIRAR ARCHIVO
# ======================================================


class RetirarArchivoOTForm(forms.Form):
    """
    Formulario utilizado para retirar lógicamente
    un archivo del historial operativo.
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
    )

    motivo_retiro = forms.CharField(
        required=True,
        label=_("Motivo"),
        max_length=250,
        widget=forms.Textarea(
            attrs={
                "rows": 2,
                "placeholder": _(
                    "Indique el motivo del retiro..."
                ),
            }
        ),
    )


# ======================================================
# ADMIN - ORDEN DE TRABAJO
# ======================================================


@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    """
    Administración de órdenes de trabajo.

    Arquitectura:

        Admin
            ↓
        Permissions
            ↓
        Services
            ↓
        Models

    Regla general para fechas:

        1. fecha escrita actualmente en el Admin;
        2. fecha previamente guardada;
        3. fecha/hora actual resuelta por el service.

    Las fechas permanecen editables.

    Los estados y usuarios de auditoría son gestionados
    mediante services.

    Los técnicos asignados se visualizan mediante inline
    de solo lectura y se administran mediante una pantalla
    específica:

        Gestionar técnicos
            ↓
        Permissions
            ↓
        Services
            ↓
        OrdenTrabajoTecnico
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

        # Instalación relacionada
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
    def mostrar_instalacion(
        self,
        obj,
    ):
        """
        Indica si la OT generó una instalación.
        """

        return obj.tiene_instalacion

    @admin.display(
        boolean=True,
        description=_("Fact."),
    )
    def mostrar_facturada(
        self,
        obj,
    ):
        """
        Indica si la OT posee fecha de facturación.
        """

        return obj.esta_facturada

    @admin.display(
        boolean=True,
        description=_("Cob."),
    )
    def mostrar_cobrada(
        self,
        obj,
    ):
        """
        Indica si la OT posee fecha de cobro.
        """

        return obj.esta_cobrada

    # ======================================================
    # INFORMACIÓN DERIVADA
    # ======================================================

    @admin.display(
        description=_("Instalación generada"),
    )
    def instalacion_generada(
        self,
        obj,
    ):
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
            args=(
                instalacion.pk,
            ),
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

    def get_queryset(
        self,
        request,
    ):
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
        Protege los campos administrados por services.

        Las fechas permanecen editables para poder
        cargar fechas reales o históricas.
        """

        campos = list(
            super().get_readonly_fields(
                request,
                obj,
            )
        )

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
                    "Aplicable a órdenes provenientes "
                    "de Proyecto o Presupuesto Telecom."
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

    def get_urls(
        self,
    ):
        """
        Endpoints administrativos para ejecutar
        el ciclo funcional mediante services.
        """

        urls = super().get_urls()

        custom_urls = [
            # ==================================================
            # TÉCNICOS
            # ==================================================

            path(
                "<path:object_id>/tecnicos/",
                self.admin_site.admin_view(
                    self.gestionar_tecnicos_view
                ),
                name=(
                    "orden_trabajo_ordentrabajo_"
                    "gestionar_tecnicos"
                ),
            ),

            path(
                "<path:object_id>/tecnicos/"
                "<int:asignacion_id>/principal/",
                self.admin_site.admin_view(
                    self.establecer_tecnico_principal_view
                ),
                name=(
                    "orden_trabajo_ordentrabajo_"
                    "tecnico_principal"
                ),
            ),

            path(
                "<path:object_id>/tecnicos/"
                "<int:asignacion_id>/desasignar/",
                self.admin_site.admin_view(
                    self.desasignar_tecnico_view
                ),
                name=(
                    "orden_trabajo_ordentrabajo_"
                    "tecnico_desasignar"
                ),
            ),

            # ==================================================
            # SEGUIMIENTOS
            # ==================================================

            path(
                "<path:object_id>/seguimientos/",
                self.admin_site.admin_view(
                    self.gestionar_seguimientos_view
                ),
                name=(
                    "orden_trabajo_ordentrabajo_"
                    "gestionar_seguimientos"
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
                    "orden_trabajo_ordentrabajo_"
                    "registrar_recepcion"
                ),
            ),

            # ==================================================
            # PROGRAMACIÓN
            # ==================================================

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

            # ==================================================
            # ENVÍO
            # ==================================================

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

            # ==================================================
            # ACEPTACIÓN
            # ==================================================

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

            # ==================================================
            # RECHAZO
            # ==================================================

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

            # ==================================================
            # INICIO
            # ==================================================

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

            # ==================================================
            # PAUSA
            # ==================================================

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

            # ==================================================
            # REANUDACIÓN
            # ==================================================

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

            # ==================================================
            # INSTALACIÓN
            # ==================================================

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

            # ==================================================
            # FINALIZACIÓN
            # ==================================================

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

            # ==================================================
            # FACTURACIÓN
            # ==================================================

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

            # ==================================================
            # COBRO
            # ==================================================

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

            # ==================================================
            # ARCHIVOS
            # ==================================================

            path(
                "<path:object_id>/archivos/",
                self.admin_site.admin_view(
                    self.gestionar_archivos_view
                ),
                name=(
                    "orden_trabajo_ordentrabajo_"
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
                    "orden_trabajo_ordentrabajo_"
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
                    "orden_trabajo_ordentrabajo_"
                    "descargar_archivo"
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

    def _redirect_changelist(
        self,
    ):
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

    def _redirect_gestion_tecnicos(
        self,
        obj,
    ):
        """
        Redirige a la pantalla de gestión
        de técnicos de la OT.
        """

        url = reverse(
            "admin:"
            "orden_trabajo_ordentrabajo_"
            "gestionar_tecnicos",
            args=(
                obj.pk,
            ),
            current_app=self.admin_site.name,
        )

        return HttpResponseRedirect(
            url
        )

    def _redirect_gestion_seguimientos(
        self,
        obj,
    ):
        """
        Redirige a la pantalla de seguimientos
        de la Orden de Trabajo.
        """

        url = reverse(
            "admin:"
            "orden_trabajo_ordentrabajo_"
            "gestionar_seguimientos",
            args=(
                obj.pk,
            ),
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

    def _validar_post(
        self,
        request,
    ):
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

    # ======================================================
    # REDIRECT - ARCHIVOS
    # ======================================================

    def _redirect_gestion_archivos(
        self,
        obj,
    ):
        """
        Redirige a la pantalla de gestión documental
        de una Orden de Trabajo.
        """

        url = reverse(
            (
                "admin:"
                "orden_trabajo_ordentrabajo_"
                "gestionar_archivos"
            ),
            args=(
                obj.pk,
            ),
            current_app=self.admin_site.name,
        )

        return HttpResponseRedirect(
            url
        )

    # ======================================================
    # HELPER DATETIME
    # ======================================================

    def _obtener_fecha_hora_post(
        self,
        request,
        nombre_campo,
    ):
        """
        Obtiene un DateTimeField enviado por
        un botón personalizado del Admin.

        Soporta:

        - DateTimeField simple;
        - AdminSplitDateTime:
              campo_0 = fecha
              campo_1 = hora.

        Si no existe valor retorna None.

        El service resolverá:

            fecha enviada
                ↓
            fecha guardada
                ↓
            timezone.now()
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
        # WIDGET DIVIDIDO
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
    # GESTIÓN DE TÉCNICOS
    # ======================================================

    def gestionar_tecnicos_view(
        self,
        request,
        object_id,
    ):
        """
        Pantalla específica para administrar
        el equipo técnico de una OT.

        Permite:

        - asignar;
        - reactivar;
        - establecer principal;
        - desasignar.

        Nunca elimina físicamente asignaciones.
        """

        obj = self._obtener_objeto(
            request,
            object_id,
        )

        if obj is None:
            return self._redirect_changelist()

        # ==================================================
        # PERMISO
        # ==================================================

        if not puede_gestionar_tecnicos_ot(
            request.user,
            obj,
        ):
            raise PermissionDenied

        # ==================================================
        # FORMULARIO
        # ==================================================

        form = AsignarTecnicoOTForm(
            request.POST or None,
            orden_trabajo=obj,
        )

        # ==================================================
        # ASIGNAR TÉCNICO
        # ==================================================

        if request.method == "POST":

            if not puede_asignar_tecnico_ot(
                request.user,
                obj,
            ):
                raise PermissionDenied

            if form.is_valid():

                try:
                    asignacion = asignar_tecnico_ot(
                        orden_trabajo=obj,
                        tecnico=(
                            form.cleaned_data[
                                "tecnico"
                            ]
                        ),
                        usuario=request.user,
                        es_principal=(
                            form.cleaned_data[
                                "es_principal"
                            ]
                        ),
                        fecha=(
                            form.cleaned_data[
                                "fecha_asignacion"
                            ]
                        ),
                        observaciones=(
                            form.cleaned_data[
                                "observaciones"
                            ]
                        ),
                    )

                except ValidationError as exc:

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

                    form.add_error(
                        None,
                        mensaje,
                    )

                else:
                    self.message_user(
                        request,
                        _(
                            "El técnico %(tecnico)s "
                            "fue asignado correctamente."
                        )
                        % {
                            "tecnico": asignacion.tecnico,
                        },
                        level=messages.SUCCESS,
                    )

                    return (
                        self._redirect_gestion_tecnicos(
                            obj
                        )
                    )

        # ==================================================
        # ASIGNACIONES
        # ==================================================

        asignaciones = (
            OrdenTrabajoTecnico.objects
            .filter(
                orden_trabajo=obj,
            )
            .select_related(
                "tecnico",
                "usuario_asignacion",
                "usuario_desasignacion",
            )
            .order_by(
                "-is_active",
                "-es_principal",
                "tecnico__last_name",
                "tecnico__first_name",
            )
        )

        filas = []

        for asignacion in asignaciones:

            filas.append(
                {
                    "asignacion": asignacion,

                    "puede_principal": (
                        puede_establecer_tecnico_principal_ot(
                            request.user,
                            asignacion,
                        )
                        and not asignacion.es_principal
                    ),

                    "puede_desasignar": (
                        puede_desasignar_tecnico_ot(
                            request.user,
                            asignacion,
                        )
                    ),
                }
            )

        # ==================================================
        # CONTEXTO ADMIN
        # ==================================================

        request.current_app = (
            self.admin_site.name
        )

        context = {
            **self.admin_site.each_context(
                request
            ),

            "title": _(
                "Gestionar técnicos de %(orden)s"
            )
            % {
                "orden": obj.codigo,
            },

            "opts": self.model._meta,

            "original": obj,

            "orden_trabajo": obj,

            "form": form,

            "media": (
                self.media
                + form.media
            ),

            "asignaciones": filas,

            "url_volver": reverse(
                "admin:"
                "orden_trabajo_ordentrabajo_change",
                args=(
                    obj.pk,
                ),
                current_app=self.admin_site.name,
            ),
        }

        return TemplateResponse(
            request,
            (
                "admin/orden_trabajo/"
                "ordentrabajo/"
                "gestionar_tecnicos.html"
            ),
            context,
        )

    # ======================================================
    # ESTABLECER TÉCNICO PRINCIPAL
    # ======================================================

    def establecer_tecnico_principal_view(
        self,
        request,
        object_id,
        asignacion_id,
    ):
        """
        Establece un técnico activo
        como principal.
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

        asignacion = (
            OrdenTrabajoTecnico.objects
            .select_related(
                "orden_trabajo",
                "tecnico",
            )
            .filter(
                pk=asignacion_id,
                orden_trabajo=obj,
            )
            .first()
        )

        if asignacion is None:
            self.message_user(
                request,
                _(
                    "La asignación indicada no existe."
                ),
                level=messages.ERROR,
            )

            return self._redirect_gestion_tecnicos(
                obj
            )

        if not puede_establecer_tecnico_principal_ot(
            request.user,
            asignacion,
        ):
            raise PermissionDenied

        try:
            asignacion = (
                establecer_tecnico_principal_ot(
                    asignacion=asignacion,
                    usuario=request.user,
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
                    "%(tecnico)s ahora es "
                    "el técnico principal."
                )
                % {
                    "tecnico": asignacion.tecnico,
                },
                level=messages.SUCCESS,
            )

        return self._redirect_gestion_tecnicos(
            obj
        )

    # ======================================================
    # DESASIGNAR TÉCNICO
    # ======================================================

    def desasignar_tecnico_view(
        self,
        request,
        object_id,
        asignacion_id,
    ):
        """
        Desasigna formalmente un técnico.

        No elimina el registro.

        Fecha:

            escrita → existente → actual.
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

        asignacion = (
            OrdenTrabajoTecnico.objects
            .select_related(
                "orden_trabajo",
                "tecnico",
            )
            .filter(
                pk=asignacion_id,
                orden_trabajo=obj,
            )
            .first()
        )

        if asignacion is None:
            self.message_user(
                request,
                _(
                    "La asignación indicada no existe."
                ),
                level=messages.ERROR,
            )

            return self._redirect_gestion_tecnicos(
                obj
            )

        if not puede_desasignar_tecnico_ot(
            request.user,
            asignacion,
        ):
            raise PermissionDenied

        # ==================================================
        # FECHA
        # ==================================================

        try:
            fecha = (
                self._obtener_fecha_hora_post(
                    request,
                    "fecha_desasignacion",
                )
            )

        except ValidationError as exc:
            self._mostrar_error(
                request,
                exc,
            )

            return self._redirect_gestion_tecnicos(
                obj
            )

        # ==================================================
        # SERVICE
        # ==================================================

        try:
            asignacion = (
                desasignar_tecnico_ot(
                    asignacion=asignacion,
                    usuario=request.user,
                    fecha=fecha,
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
                    "%(tecnico)s fue desasignado "
                    "correctamente."
                )
                % {
                    "tecnico": asignacion.tecnico,
                },
                level=messages.SUCCESS,
            )

        return self._redirect_gestion_tecnicos(
            obj
        )

    # ======================================================
    # GESTIÓN DE SEGUIMIENTOS
    # ======================================================

    def gestionar_seguimientos_view(
        self,
        request,
        object_id,
    ):
        """
        Permite registrar nuevas novedades
        y consultar el historial de la OT.

        Los seguimientos existentes son inmutables:

        - no se modifican;
        - no se eliminan;
        - una corrección genera un seguimiento nuevo.
        """

        obj = self._obtener_objeto(
            request,
            object_id,
        )

        if obj is None:
            return self._redirect_changelist()

        # ==================================================
        # PERMISO
        # ==================================================

        if not puede_registrar_seguimiento_ot(
            request.user,
            obj,
        ):
            raise PermissionDenied

        # ==================================================
        # FORMULARIO
        # ==================================================

        form = RegistrarSeguimientoOTForm(
            request.POST or None,
        )

        # ==================================================
        # REGISTRAR
        # ==================================================

        if request.method == "POST":

            if form.is_valid():

                try:
                    seguimiento = (
                        registrar_seguimiento_ot(
                            orden_trabajo=obj,
                            usuario=request.user,
                            comentario=(
                                form.cleaned_data[
                                    "comentario"
                                ]
                            ),
                            fecha=(
                                form.cleaned_data[
                                    "fecha_seguimiento"
                                ]
                            ),
                        )
                    )

                except ValidationError as exc:

                    mensaje = " ".join(
                        str(item)
                        for item in exc.messages
                    )

                    form.add_error(
                        None,
                        mensaje,
                    )

                else:
                    self.message_user(
                        request,
                        _(
                            "Seguimiento registrado "
                            "correctamente."
                        ),
                        level=messages.SUCCESS,
                    )

                    return (
                        self._redirect_gestion_seguimientos(
                            obj
                        )
                    )

        # ==================================================
        # HISTORIAL
        # ==================================================

        seguimientos = (
            OrdenTrabajoSeguimiento.objects
            .filter(
                orden_trabajo=obj,
            )
            .select_related(
                "usuario",
            )
            .order_by(
                "-fecha_seguimiento",
                "-created_at",
            )
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
                "Seguimientos de %(orden)s"
            )
            % {
                "orden": obj.codigo,
            },

            "opts": self.model._meta,

            "original": obj,

            "orden_trabajo": obj,

            "form": form,

            "media": (
                self.media
                + form.media
            ),

            "seguimientos": seguimientos,

            "url_volver": reverse(
                "admin:"
                "orden_trabajo_ordentrabajo_change",
                args=(
                    obj.pk,
                ),
                current_app=self.admin_site.name,
            ),
        }

        return TemplateResponse(
            request,
            (
                "admin/orden_trabajo/"
                "ordentrabajo/"
                "gestionar_seguimientos.html"
            ),
            context,
        )

    # ======================================================
    # RECEPCIÓN
    # ======================================================

    def registrar_recepcion_view(
        self,
        request,
        object_id,
    ):
        """
        Registra formalmente la recepción.

        Fecha:
        escrita → guardada → actual.
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

            return self._redirect_change(
                obj
            )

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
                obj
            )

        try:
            registrar_recepcion_solicitud(
                orden_trabajo=obj,
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
                    "Recepción registrada correctamente."
                ),
                level=messages.SUCCESS,
            )

        return self._redirect_change(
            obj
        )

    # ======================================================
    # PROGRAMACIÓN
    # ======================================================

    def programar_view(
        self,
        request,
        object_id,
    ):
        """
        Programa la OT.

        Fecha:
        escrita → guardada → actual.
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

            return self._redirect_change(
                obj
            )

        try:
            fecha_programada = (
                self._obtener_fecha_hora_post(
                    request,
                    "fecha_programada",
                )
            )

        except ValidationError as exc:
            self._mostrar_error(
                request,
                exc,
            )

            return self._redirect_change(
                obj
            )

        try:
            programar_orden_trabajo(
                orden_trabajo=obj,
                fecha_programada=(
                    fecha_programada
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
                    "Orden programada correctamente."
                ),
                level=messages.SUCCESS,
            )

        return self._redirect_change(
            obj
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
        Registra formalmente el envío al cliente.

        Fecha:
        escrita → guardada → actual.
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

            return self._redirect_change(
                obj
            )

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
                obj
            )

        try:
            registrar_envio_cliente(
                orden_trabajo=obj,
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
                    "Envío al cliente registrado."
                ),
                level=messages.SUCCESS,
            )

        return self._redirect_change(
            obj
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
        Registra la aceptación del cliente.

        Fecha:
        escrita → guardada → actual.
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

            return self._redirect_change(
                obj
            )

        try:
            fecha = (
                self._obtener_fecha_hora_post(
                    request,
                    "fecha_aceptacion",
                )
            )

        except ValidationError as exc:
            self._mostrar_error(
                request,
                exc,
            )

            return self._redirect_change(
                obj
            )

        try:
            registrar_aceptacion_cliente(
                orden_trabajo=obj,
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
                    "Aceptación del cliente registrada."
                ),
                level=messages.SUCCESS,
            )

        return self._redirect_change(
            obj
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
        Registra el rechazo del cliente.

        Fecha:
        escrita → guardada → actual.
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

            return self._redirect_change(
                obj
            )

        try:
            fecha = (
                self._obtener_fecha_hora_post(
                    request,
                    "fecha_aceptacion",
                )
            )

        except ValidationError as exc:
            self._mostrar_error(
                request,
                exc,
            )

            return self._redirect_change(
                obj
            )

        try:
            registrar_rechazo_cliente(
                orden_trabajo=obj,
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
                    "Rechazo del cliente registrado."
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
        """
        Inicia la ejecución de la OT.

        Fecha:
        escrita → guardada → actual.
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

            return self._redirect_change(
                obj
            )

        try:
            fecha = (
                self._obtener_fecha_hora_post(
                    request,
                    "fecha_inicio",
                )
            )

        except ValidationError as exc:
            self._mostrar_error(
                request,
                exc,
            )

            return self._redirect_change(
                obj
            )

        try:
            iniciar_orden_trabajo(
                orden_trabajo=obj,
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
                    "Orden iniciada correctamente."
                ),
                level=messages.SUCCESS,
            )

        return self._redirect_change(
            obj
        )

    # ======================================================
    # PAUSA
    # ======================================================

    def pausar_view(
        self,
        request,
        object_id,
    ):
        """
        Pausa la OT.

        Actualmente no existe fecha específica
        de pausa en el modelo.
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

        if not puede_pausar_ot(
            request.user,
            obj,
        ):
            self.message_user(
                request,
                _(
                    "La orden no puede pausarse."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(
                obj
            )

        try:
            pausar_orden_trabajo(
                orden_trabajo=obj,
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
                    "Orden pausada correctamente."
                ),
                level=messages.SUCCESS,
            )

        return self._redirect_change(
            obj
        )

    # ======================================================
    # REANUDACIÓN
    # ======================================================

    def reanudar_view(
        self,
        request,
        object_id,
    ):
        """
        Reanuda una OT pausada.

        Actualmente no existe fecha específica
        de reanudación en el modelo.
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

        if not puede_reanudar_ot(
            request.user,
            obj,
        ):
            self.message_user(
                request,
                _(
                    "La orden no puede reanudarse."
                ),
                level=messages.ERROR,
            )

            return self._redirect_change(
                obj
            )

        try:
            reanudar_orden_trabajo(
                orden_trabajo=obj,
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
                    "Orden reanudada correctamente."
                ),
                level=messages.SUCCESS,
            )

        return self._redirect_change(
            obj
        )

    # ======================================================
    # GENERAR INSTALACIÓN
    # ======================================================

    def generar_instalacion_view(
        self,
        request,
        object_id,
    ):
        """
        Genera una instalación desde la OT.

        El service valida:

        - tipo de OT;
        - estado;
        - origen;
        - aceptación cuando corresponda;
        - técnicos activos;
        - técnico principal;
        - existencia de seguimiento;
        - ausencia de instalación previa.
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

            return self._redirect_change(
                obj
            )

        try:
            instalacion = (
                crear_instalacion_desde_ot(
                    orden_trabajo=obj,
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
                    "Instalación %(codigo)s "
                    "generada correctamente."
                )
                % {
                    "codigo": instalacion.codigo,
                },
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
        """
        Finaliza operativamente la OT.

        Fecha:
        escrita → guardada → actual.
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

            return self._redirect_change(
                obj
            )

        try:
            fecha = (
                self._obtener_fecha_hora_post(
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
                obj
            )

        try:
            finalizar_orden_trabajo(
                orden_trabajo=obj,
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
                    "Orden finalizada correctamente."
                ),
                level=messages.SUCCESS,
            )

        return self._redirect_change(
            obj
        )

    # ======================================================
    # FACTURACIÓN
    # ======================================================

    def registrar_facturacion_view(
        self,
        request,
        object_id,
    ):
        """
        Registra formalmente la facturación.

        Fecha:
        escrita → guardada → actual.
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

            return self._redirect_change(
                obj
            )

        try:
            fecha = (
                self._obtener_fecha_hora_post(
                    request,
                    "fecha_facturacion",
                )
            )

        except ValidationError as exc:
            self._mostrar_error(
                request,
                exc,
            )

            return self._redirect_change(
                obj
            )

        try:
            registrar_facturacion_ot(
                orden_trabajo=obj,
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
                    "Facturación registrada correctamente."
                ),
                level=messages.SUCCESS,
            )

        return self._redirect_change(
            obj
        )

    # ======================================================
    # COBRO
    # ======================================================

    def registrar_cobro_view(
        self,
        request,
        object_id,
    ):
        """
        Registra formalmente el cobro.

        Fecha:
        escrita → guardada → actual.
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

            return self._redirect_change(
                obj
            )

        try:
            fecha = (
                self._obtener_fecha_hora_post(
                    request,
                    "fecha_cobro",
                )
            )

        except ValidationError as exc:
            self._mostrar_error(
                request,
                exc,
            )

            return self._redirect_change(
                obj
            )

        try:
            registrar_cobro_ot(
                orden_trabajo=obj,
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
                    "Cobro registrado correctamente."
                ),
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
                    # ==========================================
                    # TÉCNICOS
                    # ==========================================

                    "puede_gestionar_tecnicos_ot": (
                        puede_gestionar_tecnicos_ot(
                            request.user,
                            obj,
                        )
                    ),

                    # ==========================================
                    # SEGUIMIENTOS
                    # ==========================================

                    "puede_registrar_seguimiento_ot": (
                        puede_registrar_seguimiento_ot(
                            request.user,
                            obj,
                        )
                    ),

                    # ==========================================
                    # ARCHIVOS
                    # ==========================================

                    "puede_ver_archivos_ot": (
                        self.has_view_permission(
                            request,
                            obj,
                        )
                    ),

                    "puede_adjuntar_archivo_ot": (
                        puede_adjuntar_archivo_ot(
                            request.user,
                            obj,
                        )
                    ),

                    # ==========================================
                    # CICLO OT
                    # ==========================================

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
    # GESTIÓN DE ARCHIVOS
    # ======================================================

    def gestionar_archivos_view(
        self,
        request,
        object_id,
    ):
        """
        Permite:

        - consultar el historial documental;
        - adjuntar nuevos archivos;
        - visualizar archivos retirados;
        - acceder a las acciones documentales.

        El alta siempre utiliza:

            Admin
                ↓
            Permission
                ↓
            Service
                ↓
            Model
        """

        # ==================================================
        # OBTENER OT
        # ==================================================

        obj = self._obtener_objeto(
            request,
            object_id,
        )

        if obj is None:
            return self._redirect_changelist()

        # ==================================================
        # ACCESO
        # ==================================================

        if not self.has_view_permission(
            request,
            obj,
        ):
            raise PermissionDenied

        puede_adjuntar = (
            puede_adjuntar_archivo_ot(
                request.user,
                obj,
            )
        )

        # ==================================================
        # FORMULARIO
        # ==================================================

        form = AdjuntarArchivoOTForm(
            request.POST or None,
            request.FILES or None,
        )

        # ==================================================
        # ADJUNTAR ARCHIVO
        # ==================================================

        if request.method == "POST":

            if not puede_adjuntar:
                raise PermissionDenied

            if form.is_valid():

                try:
                    adjuntar_archivo_ot(
                        orden_trabajo=obj,
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

                    # --------------------------------------
                    # ERRORES POR CAMPO
                    # --------------------------------------

                    if hasattr(
                        exc,
                        "message_dict",
                    ):

                        for campo, errores in (
                            exc.message_dict.items()
                        ):

                            campo_formulario = (
                                campo
                                if campo in form.fields
                                else None
                            )

                            for error in errores:
                                form.add_error(
                                    campo_formulario,
                                    error,
                                )

                    # --------------------------------------
                    # ERROR GENERAL
                    # --------------------------------------

                    else:

                        for error in exc.messages:
                            form.add_error(
                                None,
                                error,
                            )

                else:

                    self.message_user(
                        request,
                        _(
                            "Archivo adjuntado "
                            "correctamente."
                        ),
                        level=messages.SUCCESS,
                    )

                    return (
                        self._redirect_gestion_archivos(
                            obj
                        )
                    )

        # ==================================================
        # ARCHIVOS
        # ==================================================

        archivos = (
            OrdenTrabajoArchivo.objects
            .filter(
                orden_trabajo=obj,
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
        # PERMISOS POR ARCHIVO
        # ==================================================

        archivos_contexto = []

        for archivo_ot in archivos:

            archivos_contexto.append(
                {
                    "archivo": archivo_ot,

                    "puede_ver": (
                        puede_ver_archivo_ot(
                            request.user,
                            archivo_ot,
                        )
                    ),

                    "puede_retirar": (
                        puede_retirar_archivo_ot(
                            request.user,
                            archivo_ot,
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
                "Archivos de %(orden)s"
            )
            % {
                "orden": obj.codigo,
            },

            "opts": self.model._meta,

            "original": obj,

            "orden_trabajo": obj,

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
                (
                    "admin:"
                    "orden_trabajo_ordentrabajo_change"
                ),
                args=(
                    obj.pk,
                ),
                current_app=self.admin_site.name,
            ),
        }

        return TemplateResponse(
            request,
            (
                "admin/orden_trabajo/"
                "ordentrabajo/"
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
        Retira lógicamente un archivo de la OT.

        El archivo:

        - no se elimina de la base;
        - no se elimina físicamente;
        - conserva su historial.
        """

        if request.method != "POST":
            return HttpResponseNotAllowed(
                [
                    "POST",
                ]
            )

        # ==================================================
        # OT
        # ==================================================

        obj = self._obtener_objeto(
            request,
            object_id,
        )

        if obj is None:
            return self._redirect_changelist()

        # ==================================================
        # ARCHIVO
        # ==================================================

        archivo_ot = (
            OrdenTrabajoArchivo.objects
            .select_related(
                "orden_trabajo",
                "usuario",
                "usuario_retiro",
            )
            .filter(
                pk=archivo_id,
                orden_trabajo=obj,
            )
            .first()
        )

        if archivo_ot is None:
            raise Http404(
                _("Archivo no encontrado.")
            )

        # ==================================================
        # PERMISO
        # ==================================================

        if not puede_retirar_archivo_ot(
            request.user,
            archivo_ot,
        ):
            raise PermissionDenied

        # ==================================================
        # FORMULARIO
        # ==================================================

        form = RetirarArchivoOTForm(
            request.POST,
        )

        if not form.is_valid():

            for campo, errores in (
                form.errors.items()
            ):

                for error in errores:

                    self.message_user(
                        request,
                        error,
                        level=messages.ERROR,
                    )

            return (
                self._redirect_gestion_archivos(
                    obj
                )
            )

        # ==================================================
        # SERVICE
        # ==================================================

        try:
            retirar_archivo_ot(
                archivo_ot=archivo_ot,
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

            for error in exc.messages:

                self.message_user(
                    request,
                    error,
                    level=messages.ERROR,
                )

        else:

            self.message_user(
                request,
                _(
                    "Archivo retirado correctamente."
                ),
                level=messages.SUCCESS,
            )

        return (
            self._redirect_gestion_archivos(
                obj
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
        Entrega un archivo únicamente después
        de verificar el permiso sobre la OT.

        Los archivos retirados siguen formando
        parte del historial y pueden consultarse
        si el usuario conserva permiso de lectura.
        """

        # ==================================================
        # OT
        # ==================================================

        obj = self._obtener_objeto(
            request,
            object_id,
        )

        if obj is None:
            raise Http404

        # ==================================================
        # ARCHIVO
        # ==================================================

        archivo_ot = (
            OrdenTrabajoArchivo.objects
            .select_related(
                "orden_trabajo",
                "usuario",
            )
            .filter(
                pk=archivo_id,
                orden_trabajo=obj,
            )
            .first()
        )

        if archivo_ot is None:
            raise Http404(
                _("Archivo no encontrado.")
            )

        # ==================================================
        # PERMISO
        # ==================================================

        if not puede_ver_archivo_ot(
            request.user,
            archivo_ot,
        ):
            raise PermissionDenied

        # ==================================================
        # VALIDAR ARCHIVO
        # ==================================================

        if not archivo_ot.archivo:
            raise Http404(
                _("El archivo no está disponible.")
            )

        # ==================================================
        # ABRIR STORAGE
        # ==================================================

        try:
            archivo_abierto = (
                archivo_ot.archivo.open(
                    "rb"
                )
            )

        except (FileNotFoundError, OSError):

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
            filename=archivo_ot.nombre_archivo,
        )

    # ======================================================
    # ACCIONES MASIVAS
    # ======================================================

    actions = ()