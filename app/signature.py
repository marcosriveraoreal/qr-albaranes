"""Firma del QR: evita que se puedan descargar albaranes cambiando el número de la URL.

Firma = Base64URL sin relleno de los 16 primeros bytes de HMAC-SHA256(secreto, número) -> 22 caracteres.
"""
import base64
import hashlib
import hmac
from typing import Optional

from app.config import Settings

SIGNATURE_BYTES = 16


def sign(number: str, settings: Settings) -> str:
    key = settings.qr_signing_secret.get_secret_value().encode()
    digest = hmac.new(key, number.encode(), hashlib.sha256).digest()[:SIGNATURE_BYTES]
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def is_valid(number: str, signature: Optional[str], settings: Settings) -> bool:
    if not settings.qr_signature_required:
        return True
    if not signature:
        return False
    return hmac.compare_digest(sign(number, settings), signature)


def build_url(number: str, settings: Settings) -> str:
    return f"{settings.qr_base_url}?n={number}&s={sign(number, settings)}"
