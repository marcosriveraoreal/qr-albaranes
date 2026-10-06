"""Configuración leída de variables de entorno (fichero .env vía docker compose)."""
from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    # --- SQL Server ---
    db_host: str
    db_port: int = 1433
    db_name: str
    db_user: str
    db_password: SecretStr
    db_driver: str = "ODBC Driver 18 for SQL Server"
    db_encrypt: str = "no"
    db_trust_server_certificate: str = "yes"
    db_timeout: int = 5

    # --- Código QR ---
    # URL pública del endpoint, sin parámetros. Es la que se imprime en el QR del albarán.
    qr_base_url: str = "http://172.16.7.9:9094/api/albaran/pdf"
    # Secreto HMAC con el que se firma el número de albarán (parámetro "s" del QR).
    qr_signing_secret: SecretStr = Field(min_length=32)
    # Solo para pruebas: si es false se acepta el QR sin comprobar la firma.
    qr_signature_required: bool = True

    # Swagger (/docs). Desactivado por defecto en producción.
    docs_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
