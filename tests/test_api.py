import pyodbc
import pytest
from fastapi.testclient import TestClient

from app import db, signature
from app.config import get_settings
from app.main import app

client = TestClient(app)
NUMBER = "2608743"


@pytest.fixture
def valid_sig() -> str:
    return signature.sign(NUMBER, get_settings())


def test_devuelve_pdf_cuando_qr_valido(monkeypatch, albaran, valid_sig):
    monkeypatch.setattr(db, "find_albaran", lambda n: albaran)
    response = client.get("/api/albaran/pdf", params={"n": NUMBER, "s": valid_sig})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_403_cuando_firma_no_valida(monkeypatch):
    def should_not_query(n):
        raise AssertionError("No debe consultar la BD con firma inválida")
    monkeypatch.setattr(db, "find_albaran", should_not_query)
    response = client.get("/api/albaran/pdf", params={"n": NUMBER, "s": "A" * 22})
    assert response.status_code == 403


def test_403_cuando_falta_firma():
    assert client.get("/api/albaran/pdf", params={"n": NUMBER}).status_code == 403


def test_404_cuando_no_existe(monkeypatch, valid_sig):
    monkeypatch.setattr(db, "find_albaran", lambda n: None)
    response = client.get("/api/albaran/pdf", params={"n": NUMBER, "s": valid_sig})
    assert response.status_code == 404


def test_503_cuando_falla_la_bd(monkeypatch, valid_sig):
    def broken(n):
        raise pyodbc.OperationalError("timeout")
    monkeypatch.setattr(db, "find_albaran", broken)
    response = client.get("/api/albaran/pdf", params={"n": NUMBER, "s": valid_sig})
    assert response.status_code == 503


@pytest.mark.parametrize("n", ["abc", "1; DROP TABLE receptions", "", "1" * 21])
def test_422_cuando_numero_no_valido(n):
    assert client.get("/api/albaran/pdf", params={"n": n, "s": "A" * 22}).status_code == 422


def test_docs_desactivado_por_defecto():
    assert client.get("/docs").status_code == 404
