"""Reconstruye el albarán en PDF con la misma maquetación que el original.

Las coordenadas se expresan en puntos desde el borde SUPERIOR de la página (A4),
medidas sobre el albarán original; _y() las convierte al sistema de ReportLab.
"""
import io
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import Color, black
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen.canvas import Canvas

from app.models import Albaran

PAGE_W, PAGE_H = A4
LOGO = Path(__file__).parent / "static" / "logo-atalaya.jpg"

RED = Color(0.89, 0.12, 0.14)
GREY = Color(0.85, 0.85, 0.85)
FONT = "Helvetica"
BOLD = "Helvetica-Bold"
MONO = "Courier"

ISSUER_NAME = "ATALAYA RIOTINTO MINERA, S.L.U."
ISSUER_LINES = ["B85062677", "C/ LA DEHESA, S/N", "21660 MINAS DE RIOTINTO", "HUELVA", "(34) 959 592 850"]


def _y(top: float) -> float:
    return PAGE_H - top


def _txt(value) -> str:
    return "" if value is None else str(value).strip()


def _fmt_date(value) -> str:
    if isinstance(value, (datetime, date)):
        return value.strftime("%d/%m/%Y")
    return _txt(value)


def _fmt_time(value) -> str:
    if isinstance(value, (datetime, time)):
        return value.strftime("%H:%M")
    return _txt(value)[:5]


def _fmt_weight(value) -> str:
    if value is None or value == "":
        return ""
    number = float(value) if isinstance(value, (Decimal, int, float)) else float(str(value).replace(",", "."))
    if number.is_integer():
        return f"{int(number)} Kg"
    return f"{number:.3f}".rstrip("0").replace(".", ",") + " Kg"


def _text(c: Canvas, x: float, top: float, value: str, font: str = FONT, size: float = 11, color=black):
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawString(x, _y(top), value)


def _band(c: Canvas, x: float, top: float, width: float, height: float):
    """Banda gris de cabecera de tabla con su línea inferior."""
    c.setFillColor(GREY)
    c.rect(x, _y(top + height), width, height, stroke=0, fill=1)
    _hline(c, x, x + width, top + height)


def _hline(c: Canvas, x1: float, x2: float, top: float):
    c.setStrokeColor(black)
    c.setLineWidth(0.6)
    c.line(x1, _y(top), x2, _y(top))


def _box(c: Canvas, x: float, top: float, width: float, height: float):
    c.setStrokeColor(black)
    c.setLineWidth(0.6)
    c.rect(x, _y(top + height), width, height, stroke=1, fill=0)


def _header(c: Canvas, a: Albaran):
    c.drawImage(str(LOGO), 33, _y(36 + 93), width=256, height=93, preserveAspectRatio=True)
    _text(c, 301, 60, "Albarán / Delivery note", BOLD, 21)
    _text(c, 301, 83, "Nº:", size=17, color=RED)
    _text(c, 433, 83, _txt(a.number), size=17, color=RED)
    _text(c, 301, 105, "Fecha:", size=17)
    _text(c, 433, 105, _fmt_date(a.delivery_date), size=17)


def _issuer(c: Canvas):
    _text(c, 39, 159, ISSUER_NAME, BOLD, 11.5)
    for i, line in enumerate(ISSUER_LINES):
        _text(c, 39, 175 + i * 11.8, line)


def _client(c: Canvas, a: Albaran):
    _text(c, 301, 180, "CLIENTE / CLIENT", size=17, color=RED)
    _box(c, 299, 183, 259, 68)
    _text(c, 307, 206, _txt(a.client_name), BOLD, 10.5)
    _text(c, 307, 223, _txt(a.client_address))
    _text(c, 307, 239, _txt(a.client_city))


def _shipment(c: Canvas, a: Albaran):
    _text(c, 39, 285, f"Envío: {_txt(a.shipment)}", size=17)
    _text(c, 160, 285, f"Lote: {_txt(a.lot)}", size=17)
    _text(c, 301, 285, _txt(a.product), size=17)
    _text(c, 39, 314, f"Origen:  {_txt(a.origin)}")
    _text(c, 39, 332, f"Destino: {_txt(a.destination)}")


def _vehicle(c: Canvas, a: Albaran):
    _band(c, 62, 358, 475, 17)
    columns = [(64, "Matrícula", a.plate), (143, "Remolque", a.trailer),
               (222, "Conductor", a.driver_name), (459, "NIF", a.driver_nif)]
    for x, title, value in columns:
        _text(c, x, 371, title, size=11.5)
        _text(c, x, 387, _txt(value), size=10)
    _hline(c, 62, 537, 389)


def _company_box(c: Canvas, x: float, title: str, lines: list):
    """Recuadro de operador / transportista. Las líneas largas se parten dentro del recuadro."""
    width = 178
    _text(c, x + 3, 413, title, size=9.5)
    _box(c, x, 416, width, 76)
    top = 433
    for line in lines:
        for chunk in simpleSplit(_txt(line), FONT, 10, width - 14):
            _text(c, x + 8, top, chunk, size=10)
            top += 10
        top += 4.5


def _transport(c: Canvas, a: Albaran):
    _company_box(c, 62, "OPERADOR DE TRANSPORTES",
                 [a.operator_name, a.operator_address, a.operator_city, a.operator_nif])
    _company_box(c, 299, "TRANSPORTISTA",
                 [a.carrier_name, a.carrier_address, a.carrier_city, a.carrier_nif])


def _weights(c: Canvas, a: Albaran):
    _band(c, 36, 547, 526, 14)
    _text(c, 170, 558, "HORA", size=10)
    _text(c, 498, 558, "PESO", size=10)
    rows = [(573, "TARA / TARE", a.tare_time, a.tare_weight),
            (587, "BRUTO / GROSS", a.gross_time, a.gross_weight)]
    for top, label, moment, weight in rows:
        _text(c, 39, top, label, size=10)
        _text(c, 170, top, _fmt_time(moment), size=10)
        _text(c, 498, top, _fmt_weight(weight), size=10)
    _hline(c, 36, 562, 589)
    _text(c, 367, 603, "NETO / NET", BOLD, 11.5)
    _text(c, 498, 603, _fmt_weight(a.net_weight), BOLD, 12.5)


def _footer(c: Canvas, qr_url: str):
    size = 100
    widget = QrCodeWidget(qr_url, barLevel="M")
    x0, y0, x1, y1 = widget.getBounds()
    drawing = Drawing(size, size, transform=[size / (x1 - x0), 0, 0, size / (y1 - y0), 0, 0])
    drawing.add(widget)
    renderPDF.draw(drawing, c, 461, _y(630 + size))
    c.setFillColor(black)
    c.setFont(FONT, 9.5)
    c.drawRightString(455, _y(676), "Escanee el código para ver el albarán")
    c.drawRightString(455, _y(686), "Scan the code to view the delivery note")
    c.setFont(MONO, 8)
    c.drawRightString(455, _y(695), qr_url)


def render_albaran(albaran: Albaran, qr_url: str) -> bytes:
    """Genera el PDF del albarán. qr_url es la URL firmada que se codifica en el QR."""
    buffer = io.BytesIO()
    c = Canvas(buffer, pagesize=A4)
    c.setTitle(f"Albarán {_txt(albaran.number)}")
    c.setAuthor(ISSUER_NAME)
    _header(c, albaran)
    _issuer(c)
    _client(c, albaran)
    _shipment(c, albaran)
    _vehicle(c, albaran)
    _transport(c, albaran)
    _weights(c, albaran)
    _footer(c, qr_url)
    c.showPage()
    c.save()
    return buffer.getvalue()
