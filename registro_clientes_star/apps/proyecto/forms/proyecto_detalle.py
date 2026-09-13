from django import forms
from django.utils.translation import gettext_lazy as _
from django.db.models import Max
from django.forms.models import BaseInlineFormSet

from apps.common.choices import (
    TipoProyectoDetalleChoices,
    UnidadMedidaChoices,
)

from apps.proyecto.models import ProyectoDetalle

class ProyectoDetalleInlineFormSet(
    BaseInlineFormSet
):
    """
    Formset del inline de detalles.

    Calcula un orden sugerido automático para
    cada nuevo detalle del Proyecto.

    Ejemplo:

        1
        2
        3
        nueva fila -> 4
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.ultimo_orden = 0

        if (
            self.instance
            and self.instance.pk
        ):
            self.ultimo_orden = (
                self.instance.detalles
                .aggregate(
                    maximo=Max(
                        "orden"
                    )
                )
                .get(
                    "maximo"
                )
                or 0
            )

    def get_form_kwargs(
        self,
        index,
    ):
        kwargs = super().get_form_kwargs(
            index
        )

        # ==============================================
        # EMPTY FORM DEL JAVASCRIPT
        # ==============================================

        if index is None:

            kwargs[
                "orden_sugerido"
            ] = (
                self.ultimo_orden
                + 1
            )

            return kwargs

        # ==============================================
        # FORMULARIOS EXISTENTES
        # ==============================================

        cantidad_existentes = (
            self.initial_form_count()
        )

        if index < cantidad_existentes:
            return kwargs

        # ==============================================
        # NUEVOS DETALLES
        # ==============================================

        posicion_nueva = (
            index
            - cantidad_existentes
            + 1
        )

        kwargs[
            "orden_sugerido"
        ] = (
            self.ultimo_orden
            + posicion_nueva
        )

        return kwargs


class ProyectoDetalleForm(forms.ModelForm):
    """
    Formulario utilizado para crear y modificar
    detalles de proyectos.

    Completa los campos automáticos antes de ejecutar
    la validación del modelo.
    """

    class Meta:
        model = ProyectoDetalle
        fields = "__all__"

    def __init__(
        self,
        *args,
        orden_sugerido=None,
        **kwargs,
    ):
        self.orden_sugerido = (
            orden_sugerido
        )

        super().__init__(
            *args,
            **kwargs,
        )

        # ==============================================
        # ORDEN AUTOMÁTICO PARA NUEVOS DETALLES
        # ==============================================

        if (
            not self.instance.pk
            and self.orden_sugerido is not None
        ):

            self.initial[
                "orden"
            ] = self.orden_sugerido

            self.fields[
                "orden"
            ].initial = (
                self.orden_sugerido
            )

            self.instance.orden = (
                self.orden_sugerido
            )

    def clean(self):
        """
        Valida el origen seleccionado y sincroniza
        los campos automáticos:

        - tipo;
        - unidad.

        El detalle debe provenir exclusivamente de:

        - un dispositivo; o
        - un ítem de catálogo.
        """

        cleaned_data = super().clean()

        # ==================================================
        # ORDEN AUTOMÁTICO
        # ==================================================

        if (
            not self.instance.pk
            and self.orden_sugerido is not None
        ):

            cleaned_data[
                "orden"
            ] = self.orden_sugerido

            self.instance.orden = (
                self.orden_sugerido
            )

        dispositivo = cleaned_data.get(
            "dispositivo"
        )

        item_catalogo = cleaned_data.get(
            "item_catalogo"
        )

        # ==================================================
        # VALIDACIÓN DEL ORIGEN
        # ==================================================

        if dispositivo and item_catalogo:

            mensaje = _(
                "Seleccione solamente un origen: "
                "un dispositivo o un ítem de catálogo."
            )

            self.add_error(
                "dispositivo",
                mensaje,
            )

            self.add_error(
                "item_catalogo",
                mensaje,
            )

            return cleaned_data

        if not dispositivo and not item_catalogo:

            mensaje = _(
                "Debe seleccionar un dispositivo "
                "o un ítem de catálogo."
            )

            self.add_error(
                "dispositivo",
                mensaje,
            )

            self.add_error(
                "item_catalogo",
                mensaje,
            )

            return cleaned_data

        # ==================================================
        # DISPOSITIVO
        # ==================================================

        if dispositivo:

            tipo = (
                TipoProyectoDetalleChoices.DISPOSITIVO
            )

            unidad = (
                UnidadMedidaChoices.UNIDAD
            )

        # ==================================================
        # ÍTEM DE CATÁLOGO
        # ==================================================

        else:

            tipo = (
                item_catalogo.tipo
            )

            unidad = (
                item_catalogo.unidad
            )

        # ==================================================
        # SINCRONIZAR FORMULARIO
        # ==================================================

        cleaned_data[
            "tipo"
        ] = tipo

        cleaned_data[
            "unidad"
        ] = unidad

        # ==================================================
        # SINCRONIZAR INSTANCIA
        # ==================================================

        self.instance.tipo = tipo
        self.instance.unidad = unidad

        return cleaned_data