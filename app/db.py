"""Acceso de solo lectura a SQL Server — tabla deliveries con JOINs."""
from contextlib import closing
from typing import Optional

import pyodbc

from app.config import get_settings
from app.models import Albaran

# (campo Albaran, expresión SQL)
# Si companies usa nombres de columna distintos a NAME/ADDRESS/LOCATION/CIF, ajusta las
# filas client_* aquí.
_FIELD_EXPRS: list[tuple[str, str]] = [
    ("number",           "d.DELIVERY_NOTE"),
    ("delivery_date",    "d.[DATE]"),
    ("lot",              "d.LOT"),
    ("plate",            "d.PLATE"),
    ("trailer",          "d.TRAILER"),
    ("driver_name",      "d.DRIVER_NAME"),
    ("driver_nif",       "d.DRIVER_NIF"),
    ("tare_time",        "d.OUT_TIME"),
    ("tare_weight",      "d.TARE_WEIGHT"),
    ("gross_time",       "d.IN_TIME"),
    ("gross_weight",     "d.GROSS_WEIGHT"),
    ("client_name",      "co.[NAME]"),
    ("client_address",   "co.ADDRESS"),
    ("client_city",      "co.LOCATION"),
    ("origin",           "orig.[name]"),
    ("destination",      "dest.[name]"),
    ("product",          "art.[NAME]"),
    ("operator_name",    "ag.[NAME]"),
    ("operator_address", "ag.ADDRESS"),
    ("operator_city",    "ag.LOCATION"),
    ("operator_nif",     "ag.CIF"),
    ("carrier_name",     "cr.[NAME]"),
    ("carrier_address",  "cr.ADDRESS"),
    ("carrier_city",     "cr.LOCATION"),
    ("carrier_nif",      "cr.CIF"),
    ("shipment",         "CAST(d.SHIPPING_ID AS varchar(20))"),
]

_FIELD_NAMES = [f for f, _ in _FIELD_EXPRS]

_SELECT = (
    "SELECT TOP 1 "
    + ", ".join(expr for _, expr in _FIELD_EXPRS)
    + " FROM [deliveries] d"
    + " LEFT JOIN [companies] co ON co.id = d.CLIENT_ID"
    + " LEFT JOIN [places] orig ON orig.id = d.ORIGIN_ID"
    + " LEFT JOIN [places] dest ON dest.id = d.DESTINATION_ID"
    + " LEFT JOIN [articles] art ON art.id = d.ARTICLE_ID"
    + " LEFT JOIN [agencies] ag ON ag.id = d.AGENCY_ID"
    + " LEFT JOIN [carriers] cr ON cr.id = d.CARRIER_ID"
    + " WHERE d.DELIVERY_NOTE = ?"
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
    """Devuelve el albarán con ese DELIVERY_NOTE, o None si no existe."""
    timeout = get_settings().db_timeout
    with closing(pyodbc.connect(_connection_string(), timeout=timeout, readonly=True)) as conn:
        conn.timeout = timeout
        row = conn.cursor().execute(_SELECT, number).fetchone()
    if row is None:
        return None
    return Albaran(**dict(zip(_FIELD_NAMES, row)))
