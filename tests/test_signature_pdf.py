from app import db, signature
from app.config import get_settings
from app.pdf import _fmt_weight, render_albaran


def test_firma_tiene_22_caracteres_y_valida():
    settings = get_settings()
    sig = signature.sign("2608743", settings)
    assert len(sig) == 22
    assert signature.is_valid("2608743", sig, settings)
    assert not signature.is_valid("2608744", sig, settings)


def test_url_del_qr():
    url = signature.build_url("2608743", get_settings())
    assert url.startswith("http://172.16.7.9:9094/api/albaran/pdf?n=2608743&s=")


def test_formato_peso():
    assert _fmt_weight(30760.0) == "30760 Kg"
    assert _fmt_weight(12.5) == "12,5 Kg"
    assert _fmt_weight(None) == ""


def test_neto(albaran):
    assert albaran.net_weight == 30760


def test_render_pdf(albaran, tmp_path):
    pdf = render_albaran(albaran, signature.build_url("2608743", get_settings()))
    assert pdf.startswith(b"%PDF")
    (tmp_path / "albaran.pdf").write_bytes(pdf)


def test_consulta_parametrizada():
    assert db._SELECT.endswith("WHERE [delivery_note_number] = ?")
    assert db._SELECT.startswith("SELECT TOP 1 ")


def test_cadena_conexion_escapa_password(monkeypatch):
    monkeypatch.setenv("DB_PASSWORD", "a;b}c")
    get_settings.cache_clear()
    try:
        assert "PWD={a;b}}c};" in db._connection_string()
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()
