from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UsuarioManager(BaseUserManager):
    """
    Manager personalizado para el modelo Usuario.

    Utiliza el correo electrónico como identificador
    principal para la autenticación.
    """

    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        """
        Crea y guarda un usuario común.
        """

        if not email:
            raise ValueError(_("El correo electrónico es obligatorio."))

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            **extra_fields,
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Crea y guarda un superusuario.
        """

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(
                _("El superusuario debe tener is_staff=True.")
            )

        if extra_fields.get("is_superuser") is not True:
            raise ValueError(
                _("El superusuario debe tener is_superuser=True.")
            )

        return self.create_user(
            email=email,
            password=password,
            **extra_fields,
        )