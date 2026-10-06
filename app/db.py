"""Acceso de solo lectura a SQL Server."""
from contextlib import closing
from typing import Optional

import pyodbc

from app.config import get_settings
from app.models import Albaran

TABLE = "receptions"

# Campo del albarán -> columna real de la tabla receptions.
# AJUSTAR AQUÍ si los nombres de columna de la tabla son distintos.
# (Solo son constantes de código, nunca entrada del usuario: no hay riesgo de inyección.)
COLUMNS = {
    "number": "delivery_note_number",
    "delivery_date": "delivery_date",
    "shipment": "shipment_number",
    "lot": "lot_number",
    "product": "product",
    "client_name": "client_name",
    "client_address": "client_address",
    "client_city": "client_city",
    "origin": "origin",
    "destination": "destination",
    "plate": "plate",
    "trailer": "trailer",
    "driver_name": "driver_name",
    "driver_nif": "driver_nif",
    "operator_name": "operator_name",
    "operator_address": "operator_address",
    "operator_city": "operator_city",
    "operator_nif": "operator_nif",
    "carrier_name": "carrier_name",
    "carrier_address": "carrier_address",
    "carrier_city": "carrier_city",
    "carrier_nif": "carrier_nif",
    "tare_time": "tare_date",
    "tare_weight": "tare_weight",
    "gross_time": "gross_date",
    "gross_weight": "gross_weight",
}

_FIELDS = Albaran.field_names()
_SELECT = (
    "SELECT TOP 1 "
    + ", ".join(f"[{COLUMNS[name]}]" for name in _FIELDS)
    + f" FROM [{TABLE}] WHERE [{COLUMNS['number']}] = ?"
)


def _odbc_value(value: str) -> str:
    """Escapa un valor para la cadena de conexión ODBC (admite ; y } en la contraseña)."""
    return "{" + value.replace("}", "}}") + "}"


def _connection_string() -> str:
    s = get_settings()
    return (
        f"DRIVER={_odbc_value(s.db_driver)};"
        f"SERVER={s.db_host},{s.db_port};"
        f"DATABASE={_odbc_value(s.db_name)};"
        f"UID={_odbc_value(s.db_user)};"
        f"PWD={_odbc_value(s.db_password.get_secret_value())};"
        f"Encrypt={s.db_encrypt};"
        f"TrustServerCertificate={s.db_trust_server_certificate};"
        "ApplicationIntent=ReadOnly;"
    )


def find_albaran(number: str) -> Optional[Albaran]:
    """Devuelve el albarán con ese número, o None si no existe."""
    timeout = get_settings().db_timeout
    with closing(pyodbc.connect(_connection_string(), timeout=timeout, readonly=True)) as conn:
        conn.timeout = timeout
        row = conn.cursor().execute(_SELECT, number).fetchone()
    if row is None:
        return None
    return Albaran(**dict(zip(_FIELDS, row)))
