import os
from datetime import date, datetime
from decimal import Decimal

import pytest

os.environ.update({
    "DB_HOST": "localhost",
    "DB_NAME": "test",
    "DB_USER": "test",
    "DB_PASSWORD": "test",
    "QR_BASE_URL": "http://172.16.7.9:9094/api/albaran/pdf",
    "QR_SIGNING_SECRET": "secreto-de-pruebas-con-al-menos-32-caracteres",
})

from app.models import Albaran  # noqa: E402


@pytest.fixture
def albaran() -> Albaran:
    """Datos del albarán de ejemplo al1.pdf."""
    return Albaran(
        number=2608743, delivery_date=date(2026, 10, 6), shipment=2646, lot=9,
        product="CONCENTRADO DE COBRE",
        client_name="EMED MARKETING LTD.", client_address="3, AGIOU DEMETRIOU STREET",
        client_city="NICOSIA, CYPRUS - P.O.BOX:  2012",
        origin="ATALAYA RIOTINTO MINERA S.L.U", destination="IMPALA TERMINALS HUELVA S.L.",
        plate="3289MSJ", trailer="R7740BDB", driver_name="JOSE RAFAEL BOMBA CARRION", driver_nif="28796475S",
        operator_name="GRUSOL LOGISTICA S.L.", operator_address="POL. IND. NUEVO PUERTO s/n",
        operator_city="21810 - PALOS DE LA FRONTERA (HUELVA)", operator_nif="B90049545",
        carrier_name="GRUSOL LOGISTICA S.L.", carrier_address="POL. IND. NUEVO PUERTO S/N",
        carrier_city="21810 - PALOS DE LA FRONTERA (Huelva)", carrier_nif="B90049545",
        tare_time=datetime(2026, 10, 6, 6, 18), tare_weight=Decimal("13040.000"),
        gross_time=datetime(2026, 10, 6, 6, 28), gross_weight=Decimal("43800.000"),
    )
