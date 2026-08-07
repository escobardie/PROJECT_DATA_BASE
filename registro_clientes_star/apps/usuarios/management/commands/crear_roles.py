from collections.abc import Iterable
from dataclasses import dataclass

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


# ======================================================
# NOMBRES DE ROLES
# ======================================================

ROL_SUPERADMIN = "SUPERADMIN"
ROL_GERENCIA = "GERENCIA"
ROL_AUDITORES = "AUDITORES"
ROL_TECNICOS = "TECNICOS"
ROL_USUARIOS_CLIENTE = "USUARIOS_CLIENTE"
ROL_PROVEEDORES = "PROVEEDORES"
ROL_CREADORES_PROYECTO = "CREADORES_PROYECTO"


# ======================================================
# ACCIONES DISPONIBLES
# ======================================================

VER = "view"
CREAR = "add"
EDITAR = "change"
ELIMINAR = "delete"

SOLO_LECTURA = (
    VER,
)

GESTION_SIN_ELIMINAR = (
    VER,
    CREAR,
    EDITAR,
)

GESTION_COMPLETA = (
    VER,
    CREAR,
    EDITAR,
    ELIMINAR,
)


# ======================================================
# DEFINICIÓN DE PERMISOS
# ======================================================

@dataclass(frozen=True)
class PermisoModelo:
    """
    Define los permisos requeridos sobre un modelo.

    app_label:
        Etiqueta interna de la aplicación Django.

    modelo:
        Nombre interno del modelo en minúsculas.

    acciones:
        Acciones estándar de Django:
        view, add, change y delete.
    """

    app_label: str
    modelo: str
    acciones: tuple[str, ...]


def permiso(
    app_label: str,
    modelo: str,
    acciones: Iterable[str],
) -> PermisoModelo:
    """
    Construye una declaración inmutable de permisos.
    """

    return PermisoModelo(
        app_label=app_label,
        modelo=modelo,
        acciones=tuple(acciones),
    )


# ======================================================
# PERMISOS REUTILIZABLES POR MÓDULO
# ======================================================

CUENTAS_LECTURA = (
    permiso(
        "cuenta_cliente",
        "cuentacliente",
        SOLO_LECTURA,
    ),
    permiso(
        "cuenta_cliente",
        "sucursal",
        SOLO_LECTURA,
    ),
)

CUENTAS_GESTION = (
    permiso(
        "cuenta_cliente",
        "cuentacliente",
        GESTION_SIN_ELIMINAR,
    ),
    permiso(
        "cuenta_cliente",
        "sucursal",
        GESTION_SIN_ELIMINAR,
    ),
)

PROYECTOS_LECTURA = (
    permiso(
        "proyecto",
        "proyecto",
        SOLO_LECTURA,
    ),
    permiso(
        "proyecto",
        "proyectodetalle",
        SOLO_LECTURA,
    ),
)

PROYECTOS_GESTION = (
    permiso(
        "proyecto",
        "proyecto",
        GESTION_SIN_ELIMINAR,
    ),
    permiso(
        "proyecto",
        "proyectodetalle",
        GESTION_COMPLETA,
    ),
)

ORDENES_LECTURA = (
    permiso(
        "orden_trabajo",
        "ordentrabajo",
        SOLO_LECTURA,
    ),
    permiso(
        "orden_trabajo",
        "ordentrabajotecnico",
        SOLO_LECTURA,
    ),
    permiso(
        "orden_trabajo",
        "ordentrabajoseguimiento",
        SOLO_LECTURA,
    ),
    permiso(
        "orden_trabajo",
        "ordentrabajoarchivo",
        SOLO_LECTURA,
    ),
)

ORDENES_GESTION = (
    permiso(
        "orden_trabajo",
        "ordentrabajo",
        GESTION_SIN_ELIMINAR,
    ),
    permiso(
        "orden_trabajo",
        "ordentrabajotecnico",
        GESTION_SIN_ELIMINAR,
    ),
    permiso(
        "orden_trabajo",
        "ordentrabajoseguimiento",
        GESTION_SIN_ELIMINAR,
    ),
    permiso(
        "orden_trabajo",
        "ordentrabajoarchivo",
        GESTION_SIN_ELIMINAR,
    ),
)

INSTALACIONES_LECTURA = (
    permiso(
        "instalacion",
        "instalacion",
        SOLO_LECTURA,
    ),
    permiso(
        "instalacion",
        "instalaciondispositivo",
        SOLO_LECTURA,
    ),
    permiso(
        "instalacion",
        "instalaciontecnico",
        SOLO_LECTURA,
    ),
)

INSTALACIONES_GESTION = (
    permiso(
        "instalacion",
        "instalacion",
        GESTION_SIN_ELIMINAR,
    ),
    permiso(
        "instalacion",
        "instalaciondispositivo",
        GESTION_SIN_ELIMINAR,
    ),
    permiso(
        "instalacion",
        "instalaciontecnico",
        GESTION_SIN_ELIMINAR,
    ),
)

DISPOSITIVOS_LECTURA = (
    permiso(
        "dispositivo",
        "tipodispositivo",
        SOLO_LECTURA,
    ),
    permiso(
        "dispositivo",
        "marca",
        SOLO_LECTURA,
    ),
    permiso(
        "dispositivo",
        "modelodispositivo",
        SOLO_LECTURA,
    ),
    permiso(
        "dispositivo",
        "dispositivo",
        SOLO_LECTURA,
    ),
)

DISPOSITIVOS_GESTION = (
    permiso(
        "dispositivo",
        "tipodispositivo",
        GESTION_SIN_ELIMINAR,
    ),
    permiso(
        "dispositivo",
        "marca",
        GESTION_SIN_ELIMINAR,
    ),
    permiso(
        "dispositivo",
        "modelodispositivo",
        GESTION_SIN_ELIMINAR,
    ),
    permiso(
        "dispositivo",
        "dispositivo",
        GESTION_SIN_ELIMINAR,
    ),
)

CATALOGO_LECTURA = (
    permiso(
        "catalogo",
        "categoriacatalogo",
        SOLO_LECTURA,
    ),
    permiso(
        "catalogo",
        "itemcatalogo",
        SOLO_LECTURA,
    ),
)

CATALOGO_GESTION = (
    permiso(
        "catalogo",
        "categoriacatalogo",
        GESTION_SIN_ELIMINAR,
    ),
    permiso(
        "catalogo",
        "itemcatalogo",
        GESTION_SIN_ELIMINAR,
    ),
)

SERVICIOS_LECTURA = (
    permiso(
        "servicio",
        "categoriaservicio",
        SOLO_LECTURA,
    ),
    permiso(
        "servicio",
        "servicio",
        SOLO_LECTURA,
    ),
    permiso(
        "servicio",
        "serviciosistema",
        SOLO_LECTURA,
    ),
    permiso(
        "servicio",
        "serviciocontratado",
        SOLO_LECTURA,
    ),
)

SERVICIOS_GESTION = (
    permiso(
        "servicio",
        "categoriaservicio",
        GESTION_SIN_ELIMINAR,
    ),
    permiso(
        "servicio",
        "servicio",
        GESTION_SIN_ELIMINAR,
    ),
    permiso(
        "servicio",
        "serviciosistema",
        GESTION_SIN_ELIMINAR,
    ),
    permiso(
        "servicio",
        "serviciocontratado",
        GESTION_SIN_ELIMINAR,
    ),
)

TELECOM_LECTURA = (
    permiso(
        "telecom",
        "zonatelecom",
        SOLO_LECTURA,
    ),
    permiso(
        "telecom",
        "conceptotelecom",
        SOLO_LECTURA,
    ),
    permiso(
        "telecom",
        "recargotelecom",
        SOLO_LECTURA,
    ),
    permiso(
        "telecom",
        "presupuestotelecom",
        SOLO_LECTURA,
    ),
    permiso(
        "telecom",
        "detallepresupuestotelecom",
        SOLO_LECTURA,
    ),
)

TELECOM_GESTION = (
    permiso(
        "telecom",
        "zonatelecom",
        GESTION_SIN_ELIMINAR,
    ),
    permiso(
        "telecom",
        "conceptotelecom",
        GESTION_SIN_ELIMINAR,
    ),
    permiso(
        "telecom",
        "recargotelecom",
        GESTION_SIN_ELIMINAR,
    ),
    permiso(
        "telecom",
        "presupuestotelecom",
        GESTION_SIN_ELIMINAR,
    ),
    permiso(
        "telecom",
        "detallepresupuestotelecom",
        GESTION_SIN_ELIMINAR,
    ),
)

FACTURACION_LECTURA = (
    permiso(
        "facturacion",
        "factura",
        SOLO_LECTURA,
    ),
    permiso(
        "facturacion",
        "detallefactura",
        SOLO_LECTURA,
    ),
)

FACTURACION_GESTION = (
    permiso(
        "facturacion",
        "factura",
        GESTION_SIN_ELIMINAR,
    ),
    permiso(
        "facturacion",
        "detallefactura",
        GESTION_SIN_ELIMINAR,
    ),
)

USUARIOS_LECTURA = (
    permiso(
        "usuarios",
        "usuario",
        SOLO_LECTURA,
    ),
)


# ======================================================
# CONFIGURACIÓN DE ROLES
# ======================================================

CONFIGURACION_ROLES: dict[str, tuple[PermisoModelo, ...]] = {
    ROL_GERENCIA: (
        *CUENTAS_GESTION,
        *PROYECTOS_GESTION,
        *ORDENES_GESTION,
        *INSTALACIONES_GESTION,
        *DISPOSITIVOS_GESTION,
        *CATALOGO_GESTION,
        *SERVICIOS_GESTION,
        *TELECOM_GESTION,
        *FACTURACION_GESTION,
        *USUARIOS_LECTURA,
    ),

    ROL_AUDITORES: (
        *CUENTAS_LECTURA,
        *PROYECTOS_LECTURA,
        *ORDENES_LECTURA,
        *INSTALACIONES_LECTURA,
        *DISPOSITIVOS_LECTURA,
        *CATALOGO_LECTURA,
        *SERVICIOS_LECTURA,
        *TELECOM_LECTURA,
        *FACTURACION_LECTURA,
        *USUARIOS_LECTURA,
    ),

    ROL_TECNICOS: (
        permiso(
            "orden_trabajo",
            "ordentrabajo",
            (
                VER,
                EDITAR,
            ),
        ),
        permiso(
            "orden_trabajo",
            "ordentrabajotecnico",
            SOLO_LECTURA,
        ),
        permiso(
            "orden_trabajo",
            "ordentrabajoseguimiento",
            (
                VER,
                CREAR,
                EDITAR,
            ),
        ),
        permiso(
            "orden_trabajo",
            "ordentrabajoarchivo",
            (
                VER,
                CREAR,
                EDITAR,
            ),
        ),
        permiso(
            "instalacion",
            "instalacion",
            (
                VER,
                CREAR,
                EDITAR,
            ),
        ),
        permiso(
            "instalacion",
            "instalaciondispositivo",
            (
                VER,
                CREAR,
                EDITAR,
            ),
        ),
        permiso(
            "instalacion",
            "instalaciontecnico",
            SOLO_LECTURA,
        ),
        *DISPOSITIVOS_LECTURA,
        *CATALOGO_LECTURA,
    ),

    ROL_CREADORES_PROYECTO: (
        *CUENTAS_LECTURA,
        *PROYECTOS_GESTION,
        *DISPOSITIVOS_LECTURA,
        *CATALOGO_LECTURA,
        *SERVICIOS_LECTURA,
    ),

    ROL_USUARIOS_CLIENTE: (
        *CUENTAS_LECTURA,
        *PROYECTOS_LECTURA,
        permiso(
            "orden_trabajo",
            "ordentrabajo",
            SOLO_LECTURA,
        ),
        permiso(
            "orden_trabajo",
            "ordentrabajoseguimiento",
            SOLO_LECTURA,
        ),
        permiso(
            "orden_trabajo",
            "ordentrabajoarchivo",
            SOLO_LECTURA,
        ),
        permiso(
            "instalacion",
            "instalacion",
            SOLO_LECTURA,
        ),
        permiso(
            "instalacion",
            "instalaciondispositivo",
            SOLO_LECTURA,
        ),
        *FACTURACION_LECTURA,
    ),

    ROL_PROVEEDORES: (
        *DISPOSITIVOS_LECTURA,
        *CATALOGO_LECTURA,
    ),
}


# ======================================================
# COMANDO
# ======================================================

class Command(BaseCommand):
    """
    Crea o actualiza los grupos funcionales del ERP
    y sincroniza sus permisos.
    """

    help = (
        "Crea y sincroniza los grupos funcionales "
        "y sus permisos en el ERP."
    )

    def add_arguments(self, parser):
        """
        Agrega opciones al comando.
        """

        parser.add_argument(
            "--verificar",
            action="store_true",
            help=(
                "Verifica la configuración y muestra los permisos "
                "sin modificar la base de datos."
            ),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        """
        Ejecuta la creación o verificación de roles.
        """

        verificar = options["verificar"]

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "Configuración de roles y permisos"
            )
        )

        if verificar:
            self.stdout.write(
                self.style.WARNING(
                    "Modo verificación: no se realizarán cambios."
                )
            )

        permisos_disponibles = self._obtener_mapa_permisos()

        if not permisos_disponibles:
            raise CommandError(
                "No se encontraron permisos en la base de datos. "
                "Ejecute primero las migraciones."
            )

        total_grupos = 0
        total_permisos = 0
        advertencias = 0

        # SUPERADMIN recibe todos los permisos existentes.
        permisos_superadmin = list(
            Permission.objects.all()
        )

        if not verificar:
            grupo_superadmin, creado = (
                Group.objects.get_or_create(
                    name=ROL_SUPERADMIN,
                )
            )

            grupo_superadmin.permissions.set(
                permisos_superadmin
            )

            estado = (
                "creado"
                if creado
                else "actualizado"
            )
        else:
            estado = "verificado"

        total_grupos += 1
        total_permisos += len(permisos_superadmin)

        self.stdout.write(
            self.style.SUCCESS(
                f"{ROL_SUPERADMIN}: {estado} "
                f"({len(permisos_superadmin)} permisos)."
            )
        )

        for nombre_grupo, declaraciones in (
            CONFIGURACION_ROLES.items()
        ):
            permisos, faltantes = self._resolver_permisos(
                declaraciones=declaraciones,
                mapa_permisos=permisos_disponibles,
            )

            advertencias += len(faltantes)

            for faltante in faltantes:
                self.stdout.write(
                    self.style.WARNING(
                        f"Permiso no encontrado: {faltante}"
                    )
                )

            if not verificar:
                grupo, creado = Group.objects.get_or_create(
                    name=nombre_grupo,
                )

                # Sincronización exacta:
                # elimina permisos antiguos no declarados
                # y agrega los permisos actuales.
                grupo.permissions.set(permisos)

                estado = (
                    "creado"
                    if creado
                    else "actualizado"
                )
            else:
                estado = "verificado"

            total_grupos += 1
            total_permisos += len(permisos)

            self.stdout.write(
                self.style.SUCCESS(
                    f"{nombre_grupo}: {estado} "
                    f"({len(permisos)} permisos)."
                )
            )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "Proceso finalizado correctamente."
            )
        )

        self.stdout.write(
            f"Grupos procesados: {total_grupos}"
        )

        self.stdout.write(
            f"Permisos asignados: {total_permisos}"
        )

        self.stdout.write(
            f"Advertencias: {advertencias}"
        )

    # ======================================================
    # MAPA DE PERMISOS
    # ======================================================

    def _obtener_mapa_permisos(
        self,
    ) -> dict[tuple[str, str], Permission]:
        """
        Devuelve los permisos disponibles indexados por:

            (app_label, codename)
        """

        permisos = (
            Permission.objects
            .select_related(
                "content_type",
            )
            .all()
        )

        return {
            (
                permiso_obj.content_type.app_label,
                permiso_obj.codename,
            ): permiso_obj
            for permiso_obj in permisos
        }

    # ======================================================
    # RESOLUCIÓN DE PERMISOS
    # ======================================================

    def _resolver_permisos(
        self,
        *,
        declaraciones: tuple[PermisoModelo, ...],
        mapa_permisos: dict[
            tuple[str, str],
            Permission,
        ],
    ) -> tuple[list[Permission], list[str]]:
        """
        Resuelve las declaraciones de permisos.

        Devuelve:

        - permisos encontrados;
        - identificadores faltantes.
        """

        permisos_encontrados: dict[int, Permission] = {}
        permisos_faltantes: list[str] = []

        for declaracion in declaraciones:
            for accion in declaracion.acciones:
                codename = (
                    f"{accion}_{declaracion.modelo}"
                )

                clave = (
                    declaracion.app_label,
                    codename,
                )

                permiso_obj = mapa_permisos.get(clave)

                if permiso_obj is None:
                    permisos_faltantes.append(
                        f"{declaracion.app_label}.{codename}"
                    )
                    continue

                permisos_encontrados[
                    permiso_obj.pk
                ] = permiso_obj

        return (
            list(permisos_encontrados.values()),
            permisos_faltantes,
        )