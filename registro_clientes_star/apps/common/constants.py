"""
Constantes compartidas por todo el proyecto.
"""
from decimal import Decimal

# ==========================================================
# PREFIJOS DE CÓDIGOS DE NEGOCIO
# ==========================================================

USER_CODE_PREFIX = "USR"

CLIENT_CODE_PREFIX = "CLI"
BRANCH_CODE_PREFIX = "SUC"

PROJECT_CODE_PREFIX = "PRO"

CATEGORY_SERVICE_CODE_PREFIX = "CAT"
SERVICE_CATEGORY_CODE_PREFIX = "CAT-S"

SERVICE_CODE_PREFIX = "SER"
CONTRACTED_SERVICE_CODE_PREFIX = "SRC"


DEVICE_CODE_PREFIX = "DSP"

INVOICE_CODE_PREFIX = "FAC"
PAYMENT_CODE_PREFIX = "PAG"

PROJECT_CODE_PREFIX = "PRY"
PROJECT_DETAIL_CODE_PREFIX = "DPY"

SYSTEM_CATEGORY_CODE_PREFIX = "CAT"
SYSTEM_CODE_PREFIX = "SIS"

# ==========================================================
# FORMATO DE CÓDIGOS
# ==========================================================

CODE_SEPARATOR = "-"
CODE_PADDING = 6


# ==========================================================
# LONGITUDES GENERALES
# ==========================================================

MAX_CODE_LENGTH = 20

MAX_NAME_LENGTH = 150
MAX_SHORT_NAME_LENGTH = 50

MAX_DESCRIPTION_LENGTH = 500

MAX_ADDRESS_LENGTH = 255

MAX_CITY_LENGTH = 100
MAX_PROVINCE_LENGTH = 100

MAX_POSTAL_CODE_LENGTH = 20

MAX_PHONE_LENGTH = 20

MAX_EMAIL_LENGTH = 254

MAX_DOCUMENT_LENGTH = 20

MAX_CUIT_LENGTH = 20

MAX_STATUS_LENGTH = 20

# ==========================================================
# IMPORTES
# ==========================================================

MAX_PRICE_DIGITS = 12

PRICE_DECIMAL_PLACES = 2

DEFAULT_AMOUNT = 0

# ==========================================================
# PAÍS POR DEFECTO
# ==========================================================

DEFAULT_COUNTRY = "Argentina"


# ==========================================================
# ARCHIVOS
# ==========================================================

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


# ==========================================================
# FECHAS
# ==========================================================

DEFAULT_PAYMENT_DAYS = 30


# ==========================================================
# CÓDIGOS DE NEGOCIO
# ==========================================================

DEVICE_TYPE_CODE_PREFIX = "TDP"

DEVICE_BRAND_CODE_PREFIX = "MAR"

DEVICE_MODEL_CODE_PREFIX = "MOD"

DEVICE_CODE_PREFIX = "DSP"

# ==========================================================
# PORCENTAJE DE DESCUENTO
# ==========================================================


MAX_PERCENTAGE_DIGITS = 5
PERCENTAGE_DECIMAL_PLACES = 2

DEFAULT_PERCENTAGE = Decimal("0.00")