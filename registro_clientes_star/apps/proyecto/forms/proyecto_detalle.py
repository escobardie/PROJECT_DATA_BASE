from django import forms
from django.utils.translation import gettext_lazy as _

from apps.common.choices import (
    TipoProyectoDetalleChoices,
    UnidadMedidaChoices,
)

from apps.proyecto.models import ProyectoDetalle


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

    def clean(self):
        """
        Valida el origen seleccionado y completa
        tipo y unidad en la instancia.
        """

        cleaned_data = super().clean()

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
        # CAMPOS AUTOMÁTICOS
        # ==================================================

        if dispositivo:
            self.instance.tipo = (
                TipoProyectoDetalleChoices.DISPOSITIVO
            )

            self.instance.unidad = (
                UnidadMedidaChoices.UNIDAD
            )

        elif item_catalogo:
            self.instance.tipo = (
                item_catalogo.tipo
            )

            self.instance.unidad = (
                item_catalogo.unidad
            )

        return cleaned_data