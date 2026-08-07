from django import forms
from django.contrib.auth.forms import (
    UserChangeForm,
    UserCreationForm,
)
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.usuarios.models import Usuario
from apps.usuarios.services.roles import (
    ROL_USUARIOS_CLIENTE,
)

from apps.usuarios.validators import (
    validar_cuenta_y_sucursal,
)


class UsuarioCreationForm(UserCreationForm):
    """
    Formulario de creación de usuarios autenticados por email.
    """

    class Meta:
        model = Usuario

        fields = (
            "email",
            "first_name",
            "last_name",
            "telefono",
            "cargo",
            "cuenta_cliente",
            "sucursal",
            "observaciones",
            "groups",
            "is_active",
            "is_staff",
        )

    def clean(self):
        cleaned_data = super().clean()

        validar_cuenta_y_sucursal(
            cuenta_cliente=cleaned_data.get(
                "cuenta_cliente"
            ),
            sucursal=cleaned_data.get(
                "sucursal"
            ),
        )

        grupos = cleaned_data.get("groups")

        if (
            grupos
            and grupos.filter(
                name=ROL_USUARIOS_CLIENTE,
            ).exists()
            and not cleaned_data.get("cuenta_cliente")
        ):
            self.add_error(
                "cuenta_cliente",
                _(
                    "Un usuario cliente debe tener "
                    "una cuenta asignada."
                ),
            )

        return cleaned_data


class UsuarioChangeForm(UserChangeForm):
    """
    Formulario de edición de usuarios.
    """

    class Meta:
        model = Usuario

        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()

        validar_cuenta_y_sucursal(
            cuenta_cliente=cleaned_data.get(
                "cuenta_cliente"
            ),
            sucursal=cleaned_data.get(
                "sucursal"
            ),
        )

        grupos = cleaned_data.get("groups")

        if (
            grupos
            and grupos.filter(
                name=ROL_USUARIOS_CLIENTE,
            ).exists()
            and not cleaned_data.get("cuenta_cliente")
        ):
            self.add_error(
                "cuenta_cliente",
                _(
                    "Un usuario cliente debe tener "
                    "una cuenta asignada."
                ),
            )

        if (
            cleaned_data.get("is_superuser")
            and not cleaned_data.get("is_staff")
        ):
            self.add_error(
                "is_staff",
                _(
                    "Un superusuario también debe tener "
                    "acceso administrativo."
                ),
            )

        return cleaned_data