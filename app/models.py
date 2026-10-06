"""Datos del albarán tal y como se leen de la tabla receptions."""
from dataclasses import dataclass, fields
from typing import Any, Optional


@dataclass
class Albaran:
    number: Any = None
    delivery_date: Any = None
    shipment: Any = None
    lot: Any = None
    product: Any = None
    client_name: Any = None
    client_address: Any = None
    client_city: Any = None
    origin: Any = None
    destination: Any = None
    plate: Any = None
    trailer: Any = None
    driver_name: Any = None
    driver_nif: Any = None
    operator_name: Any = None
    operator_address: Any = None
    operator_city: Any = None
    operator_nif: Any = None
    carrier_name: Any = None
    carrier_address: Any = None
    carrier_city: Any = None
    carrier_nif: Any = None
    tare_time: Any = None
    tare_weight: Any = None
    gross_time: Any = None
    gross_weight: Any = None

    @classmethod
    def field_names(cls) -> list[str]:
        return [f.name for f in fields(cls)]

    @property
    def net_weight(self) -> Optional[float]:
        """Peso neto = bruto - tara."""
        if self.gross_weight is None or self.tare_weight is None:
            return None
        return float(self.gross_weight) - float(self.tare_weight)
