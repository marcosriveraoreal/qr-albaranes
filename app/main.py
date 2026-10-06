"""API: al escanear el QR se abre /api/albaran/pdf?n=<número>&s=<firma> y se devuelve el albarán en PDF."""
import logging
from typing import Annotated, Optional

import pyodbc
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response

from app import db, signature
from app.config import get_settings
from app.pdf import render_albaran

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
log = logging.getLogger("qr-albaran")

_docs = get_settings().docs_enabled
app = FastAPI(
    title="QR Albarán",
    docs_url="/docs" if _docs else None,
    redoc_url=None,
    openapi_url="/openapi.json" if _docs else None,
)


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "UP"}


@app.get("/api/albaran/pdf", response_class=Response,
         responses={200: {"content": {"application/pdf": {}}}, 403: {}, 404: {}, 503: {}})
def albaran_pdf(
    n: Annotated[str, Query(pattern=r"^\d{1,20}$", description="Número de albarán")],
    s: Annotated[Optional[str], Query(pattern=r"^[A-Za-z0-9_-]{22}$", description="Firma del QR")] = None,
):
    settings = get_settings()
    if not signature.is_valid(n, s, settings):
        log.warning("QR con firma no válida: albaran=%s", n)
        raise HTTPException(status_code=403, detail="Código QR no válido")

    try:
        albaran = db.find_albaran(n)
    except pyodbc.Error as ex:
        log.error("Error consultando SQL Server: %s", type(ex).__name__, exc_info=True)
        raise HTTPException(status_code=503, detail="Servicio no disponible, inténtelo más tarde")

    if albaran is None:
        raise HTTPException(status_code=404, detail="Albarán no encontrado")

    log.info("Albarán reconstruido: albaran=%s", n)
    pdf = render_albaran(albaran, signature.build_url(n, settings))
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="albaran_{n}.pdf"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
