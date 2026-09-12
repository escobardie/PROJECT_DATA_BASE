from __future__ import annotations

import mimetypes
from pathlib import Path
from tempfile import SpooledTemporaryFile
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload


# ======================================================
# CONSTANTES
# ======================================================

DRIVE_API_SERVICE_NAME = "drive"
DRIVE_API_VERSION = "v3"

DRIVE_FOLDER_MIME_TYPE = (
    "application/vnd.google-apps.folder"
)

DEFAULT_ROOT_FOLDER_NAME = (
    "REGISTRO CLIENTES STAR"
)

APP_PROPERTY_APP = (
    "registro_clientes_star"
)

APP_PROPERTY_ROOT_TYPE = (
    "proyectos_root"
)

APP_PROPERTY_PROJECT_TYPE = (
    "proyecto"
)


# ======================================================
# EXCEPCIÓN
# ======================================================


class GoogleDriveServiceError(Exception):
    """
    Error controlado producido por la integración
    con Google Drive.
    """


# ======================================================
# CONFIGURACIÓN
# ======================================================


def _obtener_client_secrets_file() -> Path:
    """
    Obtiene y valida la ubicación del archivo JSON
    del cliente OAuth.
    """

    ruta = Path(
        settings.GOOGLE_DRIVE_CLIENT_SECRETS_FILE
    )

    if not ruta.exists():
        raise GoogleDriveServiceError(
            _(
                "No se encontró el archivo de "
                "credenciales OAuth de Google Drive."
            )
        )

    if not ruta.is_file():
        raise GoogleDriveServiceError(
            _(
                "La ruta configurada para las "
                "credenciales de Google Drive "
                "no corresponde a un archivo."
            )
        )

    return ruta


def _obtener_token_file() -> Path:
    """
    Obtiene la ubicación donde se guarda
    el token OAuth.
    """

    return Path(
        settings.GOOGLE_DRIVE_TOKEN_FILE
    )


def _obtener_scopes() -> list[str]:
    """
    Obtiene los scopes configurados para Drive.
    """

    scopes = list(
        getattr(
            settings,
            "GOOGLE_DRIVE_SCOPES",
            [],
        )
    )

    if not scopes:
        raise GoogleDriveServiceError(
            _(
                "No se configuraron scopes "
                "para Google Drive."
            )
        )

    return scopes


def _obtener_nombre_carpeta_raiz() -> str:
    """
    Permite personalizar el nombre de la carpeta
    principal desde settings.py.
    """

    nombre = getattr(
        settings,
        "GOOGLE_DRIVE_ROOT_FOLDER_NAME",
        DEFAULT_ROOT_FOLDER_NAME,
    )

    nombre = str(
        nombre
        or DEFAULT_ROOT_FOLDER_NAME
    ).strip()

    return (
        nombre
        or DEFAULT_ROOT_FOLDER_NAME
    )


# ======================================================
# TOKEN
# ======================================================


def _guardar_credenciales(
    credenciales: Credentials,
) -> None:
    """
    Guarda las credenciales OAuth.

    El archivo debe permanecer fuera de Git.
    """

    ruta = _obtener_token_file()

    ruta.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ruta.write_text(
        credenciales.to_json(),
        encoding="utf-8",
    )


def obtener_credenciales_drive(
    *,
    refrescar: bool = True,
) -> Credentials | None:
    """
    Obtiene las credenciales almacenadas.

    Si el access token expiró y existe refresh token,
    lo renueva automáticamente.

    Retorna None cuando todavía no se realizó
    la autorización OAuth inicial.
    """

    ruta_token = _obtener_token_file()

    if not ruta_token.exists():
        return None

    try:
        credenciales = (
            Credentials.from_authorized_user_file(
                str(ruta_token),
                _obtener_scopes(),
            )
        )

    except Exception as exc:
        raise GoogleDriveServiceError(
            _(
                "No fue posible leer las credenciales "
                "guardadas de Google Drive."
            )
        ) from exc

    if (
        refrescar
        and credenciales.expired
        and credenciales.refresh_token
    ):
        try:
            credenciales.refresh(
                Request()
            )

            _guardar_credenciales(
                credenciales
            )

        except Exception as exc:
            raise GoogleDriveServiceError(
                _(
                    "No fue posible renovar la "
                    "autorización de Google Drive."
                )
            ) from exc

    return credenciales


def google_drive_esta_conectado() -> bool:
    """
    Indica si existen credenciales utilizables.

    No realiza una consulta a Drive.
    """

    try:
        credenciales = (
            obtener_credenciales_drive()
        )

    except GoogleDriveServiceError:
        return False

    if not credenciales:
        return False

    return bool(
        credenciales.valid
        or credenciales.refresh_token
    )


# ======================================================
# OAUTH
# ======================================================

def crear_flujo_oauth_drive(
    *,
    redirect_uri: str,
    state: str | None = None,
    code_verifier: str | None = None,
    autogenerate_code_verifier: bool = False,
) -> Flow:
    """
    Construye el flujo OAuth de Google Drive.

    PKCE:
    - al iniciar OAuth puede generar code_verifier;
    - durante el callback debe reutilizarse
      exactamente el mismo code_verifier.
    """

    if not redirect_uri:
        raise GoogleDriveServiceError(
            _(
                "No se recibió una URL de retorno "
                "para Google OAuth."
            )
        )

    try:

        flujo = Flow.from_client_secrets_file(
            str(
                _obtener_client_secrets_file()
            ),
            scopes=_obtener_scopes(),
            state=state,
            code_verifier=code_verifier,
            autogenerate_code_verifier=(
                autogenerate_code_verifier
            ),
        )

    except Exception as exc:

        raise GoogleDriveServiceError(
            _(
                "No fue posible crear el flujo "
                "OAuth de Google Drive."
            )
        ) from exc

    flujo.redirect_uri = redirect_uri

    return flujo

def generar_url_autorizacion_drive(
    *,
    redirect_uri: str,
) -> tuple[str, str, str]:
    """
    Genera la URL OAuth de Google Drive.

    Retorna:

        authorization_url
        state
        code_verifier

    El code_verifier debe conservarse hasta
    que Google regrese al callback.
    """

    flujo = crear_flujo_oauth_drive(
        redirect_uri=redirect_uri,
        autogenerate_code_verifier=True,
    )

    try:

        authorization_url, state = (
            flujo.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                prompt="consent",
            )
        )

    except Exception as exc:

        raise GoogleDriveServiceError(
            _(
                "No fue posible generar la URL "
                "de autorización de Google Drive."
            )
        ) from exc

    code_verifier = (
        flujo.code_verifier
    )

    if not code_verifier:
        raise GoogleDriveServiceError(
            _(
                "No fue posible generar el código "
                "de seguridad PKCE de Google OAuth."
            )
        )

    return (
        authorization_url,
        state,
        code_verifier,
    )

def procesar_callback_oauth_drive(
    *,
    redirect_uri: str,
    authorization_response: str,
    state: str,
    code_verifier: str,
) -> Credentials:
    """
    Procesa el callback OAuth de Google Drive.

    Reutiliza el code_verifier generado antes
    de enviar al usuario a Google.
    """

    if not authorization_response:
        raise GoogleDriveServiceError(
            _(
                "Google no devolvió una respuesta "
                "de autorización válida."
            )
        )

    if not state:
        raise GoogleDriveServiceError(
            _(
                "No se encontró el estado de "
                "seguridad del flujo OAuth."
            )
        )

    if not code_verifier:
        raise GoogleDriveServiceError(
            _(
                "No se encontró el código PKCE "
                "de la autorización de Google Drive."
            )
        )

    # ==================================================
    # RECONSTRUIR EL MISMO FLUJO PKCE
    # ==================================================

    flujo = crear_flujo_oauth_drive(
        redirect_uri=redirect_uri,
        state=state,
        code_verifier=code_verifier,
        autogenerate_code_verifier=False,
    )

    try:

        flujo.fetch_token(
            authorization_response=(
                authorization_response
            )
        )

    except Exception as exc:

        raise GoogleDriveServiceError(
            (
                "No fue posible completar la autorización "
                "con Google Drive. "
                f"Detalle: {exc.__class__.__name__}: {exc}"
            )
        ) from exc

    credenciales = (
        flujo.credentials
    )

    if not credenciales:
        raise GoogleDriveServiceError(
            _(
                "Google no devolvió credenciales "
                "OAuth válidas."
            )
        )

    _guardar_credenciales(
        credenciales
    )

    return credenciales

# ======================================================
# SERVICIO DRIVE
# ======================================================


def obtener_servicio_drive():
    """
    Construye el cliente oficial de Google Drive API v3.
    """

    credenciales = (
        obtener_credenciales_drive()
    )

    if not credenciales:
        raise GoogleDriveServiceError(
            _(
                "Google Drive todavía no está conectado. "
                "Debe realizar primero la autorización OAuth."
            )
        )

    if (
        not credenciales.valid
        and not credenciales.refresh_token
    ):
        raise GoogleDriveServiceError(
            _(
                "Las credenciales de Google Drive "
                "ya no son válidas."
            )
        )

    try:
        return build(
            DRIVE_API_SERVICE_NAME,
            DRIVE_API_VERSION,
            credentials=credenciales,
            cache_discovery=False,
        )

    except Exception as exc:
        raise GoogleDriveServiceError(
            _(
                "No fue posible inicializar "
                "Google Drive API."
            )
        ) from exc


# ======================================================
# CONSULTAS AUXILIARES
# ======================================================


def _escapar_valor_query(
    valor: Any,
) -> str:
    """
    Escapa valores utilizados dentro de queries
    de Google Drive.
    """

    return (
        str(valor)
        .replace("\\", "\\\\")
        .replace("'", "\\'")
    )


def _buscar_primera_carpeta(
    *,
    servicio,
    query: str,
) -> dict | None:
    """
    Ejecuta una búsqueda y devuelve
    la primera carpeta encontrada.
    """

    try:
        resultado = (
            servicio.files()
            .list(
                q=query,
                spaces="drive",
                pageSize=10,
                fields=(
                    "files("
                    "id,"
                    "name,"
                    "mimeType,"
                    "webViewLink,"
                    "appProperties"
                    ")"
                ),
            )
            .execute()
        )

    except HttpError as exc:
        raise GoogleDriveServiceError(
            _(
                "Google Drive no pudo buscar "
                "la carpeta solicitada."
            )
        ) from exc

    archivos = resultado.get(
        "files",
        [],
    )

    if not archivos:
        return None

    return archivos[0]


# ======================================================
# CARPETA RAÍZ
# ======================================================


def obtener_o_crear_carpeta_raiz_drive(
    *,
    servicio=None,
) -> dict:
    """
    Obtiene o crea:

        REGISTRO CLIENTES STAR

    La carpeta se identifica mediante appProperties,
    no solamente por nombre.
    """

    servicio = (
        servicio
        or obtener_servicio_drive()
    )

    query = (
        f"mimeType = '{DRIVE_FOLDER_MIME_TYPE}' "
        "and trashed = false "
        "and appProperties has "
        "{ "
        "key='rce_app' "
        f"and value='{APP_PROPERTY_APP}' "
        "} "
        "and appProperties has "
        "{ "
        "key='rce_tipo' "
        f"and value='{APP_PROPERTY_ROOT_TYPE}' "
        "}"
    )

    carpeta = _buscar_primera_carpeta(
        servicio=servicio,
        query=query,
    )

    if carpeta:
        return carpeta

    metadata = {
        "name": (
            _obtener_nombre_carpeta_raiz()
        ),
        "mimeType": (
            DRIVE_FOLDER_MIME_TYPE
        ),
        "appProperties": {
            "rce_app": (
                APP_PROPERTY_APP
            ),
            "rce_tipo": (
                APP_PROPERTY_ROOT_TYPE
            ),
        },
    }

    try:
        return (
            servicio.files()
            .create(
                body=metadata,
                fields=(
                    "id,"
                    "name,"
                    "mimeType,"
                    "webViewLink,"
                    "appProperties"
                ),
            )
            .execute()
        )

    except HttpError as exc:
        raise GoogleDriveServiceError(
            _(
                "No fue posible crear la carpeta "
                "principal en Google Drive."
            )
        ) from exc


# ======================================================
# CARPETA DEL PROYECTO
# ======================================================


def _nombre_carpeta_proyecto(
    proyecto,
) -> str:
    """
    Construye un nombre legible para la carpeta
    del Proyecto.
    """

    codigo = str(
        getattr(
            proyecto,
            "codigo",
            proyecto.pk,
        )
    ).strip()

    nombre = str(
        getattr(
            proyecto,
            "nombre",
            "",
        )
        or ""
    ).strip()

    if nombre:
        return (
            f"{codigo} - {nombre}"
        )

    return codigo


def obtener_o_crear_carpeta_proyecto_drive(
    proyecto,
    *,
    servicio=None,
) -> dict:
    """
    Obtiene o crea la carpeta Drive correspondiente
    a un Proyecto.

    Ejemplo:

        REGISTRO CLIENTES STAR/
            PRO-000026 - Proyecto CCTV/
    """

    if not getattr(
        proyecto,
        "pk",
        None,
    ):
        raise ValidationError(
            _(
                "El Proyecto debe estar guardado "
                "antes de utilizar Google Drive."
            )
        )

    servicio = (
        servicio
        or obtener_servicio_drive()
    )

    carpeta_raiz = (
        obtener_o_crear_carpeta_raiz_drive(
            servicio=servicio,
        )
    )

    proyecto_id = (
        str(proyecto.pk)
    )

    query = (
        f"mimeType = '{DRIVE_FOLDER_MIME_TYPE}' "
        "and trashed = false "
        f"and '{_escapar_valor_query(carpeta_raiz['id'])}' "
        "in parents "
        "and appProperties has "
        "{ "
        "key='rce_app' "
        f"and value='{APP_PROPERTY_APP}' "
        "} "
        "and appProperties has "
        "{ "
        "key='rce_tipo' "
        f"and value='{APP_PROPERTY_PROJECT_TYPE}' "
        "} "
        "and appProperties has "
        "{ "
        "key='rce_proyecto_id' "
        f"and value='{_escapar_valor_query(proyecto_id)}' "
        "}"
    )

    carpeta = _buscar_primera_carpeta(
        servicio=servicio,
        query=query,
    )

    if carpeta:
        return carpeta

    metadata = {
        "name": (
            _nombre_carpeta_proyecto(
                proyecto
            )
        ),
        "mimeType": (
            DRIVE_FOLDER_MIME_TYPE
        ),
        "parents": [
            carpeta_raiz["id"],
        ],
        "appProperties": {
            "rce_app": (
                APP_PROPERTY_APP
            ),
            "rce_tipo": (
                APP_PROPERTY_PROJECT_TYPE
            ),
            "rce_proyecto_id": (
                proyecto_id
            ),
            "rce_proyecto_codigo": (
                str(
                    getattr(
                        proyecto,
                        "codigo",
                        "",
                    )
                    or ""
                )[:124]
            ),
        },
    }

    try:
        return (
            servicio.files()
            .create(
                body=metadata,
                fields=(
                    "id,"
                    "name,"
                    "mimeType,"
                    "webViewLink,"
                    "appProperties,"
                    "parents"
                ),
            )
            .execute()
        )

    except HttpError as exc:
        raise GoogleDriveServiceError(
            _(
                "No fue posible crear la carpeta "
                "del Proyecto en Google Drive."
            )
        ) from exc


# ======================================================
# MIME TYPE
# ======================================================


def _obtener_mime_type(
    archivo,
) -> str:
    """
    Determina el MIME type del archivo.

    Prioridad:

    1. content_type enviado por Django;
    2. extensión;
    3. application/octet-stream.
    """

    content_type = getattr(
        archivo,
        "content_type",
        None,
    )

    if content_type:
        return str(
            content_type
        )

    nombre = str(
        getattr(
            archivo,
            "name",
            "",
        )
    )

    mime_type, _ = (
        mimetypes.guess_type(
            nombre
        )
    )

    return (
        mime_type
        or "application/octet-stream"
    )


# ======================================================
# SUBIDA
# ======================================================


def subir_archivo_proyecto_drive(
    *,
    proyecto,
    archivo,
) -> dict:
    """
    Sube un archivo a Google Drive dentro
    de la carpeta correspondiente al Proyecto.

    El archivo se conserva en su formato original.

    Por ejemplo:

        .xlsx
        .docx
        .pptx
        .pdf

    Retorna los metadatos necesarios para
    crear ProyectoArchivo.
    """

    if not getattr(
        proyecto,
        "pk",
        None,
    ):
        raise ValidationError(
            _(
                "El Proyecto debe estar guardado "
                "antes de subir documentos."
            )
        )

    if archivo is None:
        raise ValidationError(
            {
                "archivo": _(
                    "Debe seleccionar un archivo."
                )
            }
        )

    nombre_archivo = str(
        getattr(
            archivo,
            "name",
            "",
        )
        or ""
    ).strip()

    if not nombre_archivo:
        raise ValidationError(
            {
                "archivo": _(
                    "El archivo no posee un "
                    "nombre válido."
                )
            }
        )

    tamaño = getattr(
        archivo,
        "size",
        None,
    )

    if tamaño == 0:
        raise ValidationError(
            {
                "archivo": _(
                    "No puede subir un archivo vacío."
                )
            }
        )

    servicio = (
        obtener_servicio_drive()
    )

    carpeta = (
        obtener_o_crear_carpeta_proyecto_drive(
            proyecto,
            servicio=servicio,
        )
    )

    mime_type = (
        _obtener_mime_type(
            archivo
        )
    )

    metadata = {
        "name": (
            nombre_archivo
        ),
        "parents": [
            carpeta["id"],
        ],
        "appProperties": {
            "rce_app": (
                APP_PROPERTY_APP
            ),
            "rce_tipo": (
                "archivo_proyecto"
            ),
            "rce_proyecto_id": (
                str(proyecto.pk)
            ),
            "rce_proyecto_codigo": (
                str(
                    getattr(
                        proyecto,
                        "codigo",
                        "",
                    )
                    or ""
                )[:124]
            ),
        },
    }

    # ==================================================
    # ARCHIVO TEMPORAL
    # ==================================================
    #
    # SpooledTemporaryFile mantiene archivos pequeños
    # en memoria y pasa automáticamente a disco cuando
    # superan el límite configurado.
    #
    # Esto evita cargar archivos grandes completamente
    # en RAM.
    # ==================================================

    temporal = SpooledTemporaryFile(
        max_size=10 * 1024 * 1024,
        mode="w+b",
    )

    try:

        if hasattr(
            archivo,
            "chunks",
        ):
            for chunk in archivo.chunks():
                temporal.write(
                    chunk
                )

        else:
            contenido = archivo.read()

            temporal.write(
                contenido
            )

        temporal.seek(0)

        media = MediaIoBaseUpload(
            temporal,
            mimetype=mime_type,
            resumable=True,
        )

        resultado = (
            servicio.files()
            .create(
                body=metadata,
                media_body=media,
                fields=(
                    "id,"
                    "name,"
                    "mimeType,"
                    "webViewLink,"
                    "webContentLink,"
                    "size,"
                    "createdTime,"
                    "modifiedTime,"
                    "parents"
                ),
            )
            .execute()
        )

    except HttpError as exc:
        raise GoogleDriveServiceError(
            _(
                "Google Drive rechazó la subida "
                "del archivo."
            )
        ) from exc

    except Exception as exc:
        raise GoogleDriveServiceError(
            _(
                "Ocurrió un error durante la "
                "subida del archivo a Google Drive."
            )
        ) from exc

    finally:
        temporal.close()

    # ==================================================
    # VALIDAR RESPUESTA
    # ==================================================

    if not resultado.get(
        "id"
    ):
        raise GoogleDriveServiceError(
            _(
                "Google Drive creó el documento "
                "sin devolver su identificador."
            )
        )

    if not resultado.get(
        "webViewLink"
    ):
        raise GoogleDriveServiceError(
            _(
                "Google Drive no devolvió un enlace "
                "para abrir el documento."
            )
        )

    return resultado


# ======================================================
# OBTENER METADATOS
# ======================================================


def obtener_archivo_drive(
    drive_file_id: str,
) -> dict:
    """
    Obtiene los metadatos actuales
    de un archivo de Google Drive.
    """

    drive_file_id = str(
        drive_file_id
        or ""
    ).strip()

    if not drive_file_id:
        raise ValidationError(
            _(
                "Debe indicar el identificador "
                "del archivo de Google Drive."
            )
        )

    servicio = (
        obtener_servicio_drive()
    )

    try:
        return (
            servicio.files()
            .get(
                fileId=drive_file_id,
                fields=(
                    "id,"
                    "name,"
                    "mimeType,"
                    "webViewLink,"
                    "webContentLink,"
                    "size,"
                    "createdTime,"
                    "modifiedTime,"
                    "trashed"
                ),
            )
            .execute()
        )

    except HttpError as exc:
        raise GoogleDriveServiceError(
            _(
                "No fue posible consultar "
                "el archivo en Google Drive."
            )
        ) from exc

# ======================================================
# ELIMINAR ARCHIVO
# ======================================================


def eliminar_archivo_drive(
    drive_file_id: str,
) -> None:
    """
    Elimina un archivo de Google Drive.

    Se utiliza principalmente como mecanismo
    compensatorio cuando la subida a Drive fue
    correcta pero posteriormente no pudo crearse
    el registro ProyectoArchivo en la base de datos.
    """

    drive_file_id = str(
        drive_file_id
        or ""
    ).strip()

    if not drive_file_id:
        raise ValidationError(
            _(
                "Debe indicar el identificador "
                "del archivo de Google Drive."
            )
        )

    servicio = obtener_servicio_drive()

    try:

        (
            servicio.files()
            .delete(
                fileId=drive_file_id,
            )
            .execute()
        )

    except HttpError as exc:

        raise GoogleDriveServiceError(
            _(
                "No fue posible eliminar el archivo "
                "de Google Drive."
            )
        ) from exc