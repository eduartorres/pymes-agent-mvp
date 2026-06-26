from fastapi import APIRouter, HTTPException
from app.services.loader import obtener_solicitud_por_id, obtener_solicitudes_rango
from app.services.orquestador import procesar_solicitud
from app.models.schemas import RespuestaAPI, RespuestaBatch

router = APIRouter(prefix="/api/v1", tags=["Agente PYME"])


@router.post("/analizar/{id_solicitud}", response_model=RespuestaAPI)
def analizar_por_id(id_solicitud: str):
    """
    Analiza una solicitud individual por su ID.
    Extrae datos de los PDFs, detecta inconsistencias y clasifica el caso.
    """
    solicitud = obtener_solicitud_por_id(id_solicitud)
    if not solicitud:
        raise HTTPException(status_code=404, detail=f"Solicitud {id_solicitud} no encontrada.")

    try:
        resultado = procesar_solicitud(solicitud)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar solicitud: {str(e)}")

    return RespuestaAPI(
        status="ok",
        id_solicitud=id_solicitud,
        resultado=resultado,
    )


@router.post("/batch", response_model=RespuestaBatch)
def analizar_batch(inicio: int = 1, fin: int = 10):
    """
    Procesa un rango de solicitudes del Excel en modo batch.
    Por defecto procesa las primeras 10 (inicio=1, fin=10).
    """
    solicitudes = obtener_solicitudes_rango(inicio, fin)
    if not solicitudes:
        raise HTTPException(status_code=404, detail="No se encontraron solicitudes en el rango indicado.")

    resultados = []
    exitosas = 0
    fallidas = 0

    for sol in solicitudes:
        try:
            resultado = procesar_solicitud(sol)
            resultados.append(RespuestaAPI(
                status="ok",
                id_solicitud=sol["id_solicitud"],
                resultado=resultado,
            ))
            exitosas += 1
        except Exception as e:
            resultados.append(RespuestaAPI(
                status="error",
                id_solicitud=sol.get("id_solicitud", "desconocido"),
                resultado=None,
            ))
            fallidas += 1

    return RespuestaBatch(
        status="completado",
        total_procesadas=len(solicitudes),
        exitosas=exitosas,
        fallidas=fallidas,
        resultados=resultados,
    )


@router.get("/solicitudes")
def listar_solicitudes(limite: int = 20):
    """Lista las primeras N solicitudes disponibles en el Excel."""
    solicitudes = obtener_solicitudes_rango(1, limite)
    return {
        "total": len(solicitudes),
        "solicitudes": [
            {
                "id_solicitud": s["id_solicitud"],
                "razon_social": s["razon_social"],
                "ciudad": s["ciudad_registrada"],
                "sector": s["sector_declarado"],
            }
            for s in solicitudes
        ],
    }
