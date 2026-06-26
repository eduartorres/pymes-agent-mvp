from fastapi import FastAPI
from app.routers.analisis import router

app = FastAPI(
    title="Agente de Análisis PYME — Seguros Multirriesgo",
    description=(
        "API para automatizar el análisis inicial de solicitudes de seguro PYME en Colombia. "
        "Extrae datos de documentos no estructurados, detecta inconsistencias y clasifica "
        "cada caso para su enrutamiento operativo."
    ),
    version="1.0.0",
)

app.include_router(router)


@app.get("/")
def raiz():
    return {
        "servicio": "Agente PYME — Seguros Multirriesgo",
        "version": "1.0.0",
        "endpoints": {
            "analizar_individual": "POST /api/v1/analizar/{id_solicitud}",
            "batch": "POST /api/v1/batch?inicio=1&fin=10",
            "listar": "GET /api/v1/solicitudes?limite=20",
            "docs": "GET /docs",
        },
    }
