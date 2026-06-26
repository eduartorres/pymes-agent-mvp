"""
Script de prueba batch para el agente de analisis PYME.

Procesa las primeras 10 solicitudes del Excel, imprime un resumen por consola
y guarda el JSON completo en outputs/resultados_batch.json.

Uso:
    export GROQ_API_KEY="gsk_..."
    python tests/prueba_batch.py
"""
import json
import os
import sys

# Permite ejecutar el script desde la raiz del proyecto sin instalar el paquete
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.loader import obtener_solicitudes_rango
from app.services.orquestador import procesar_solicitud


RUTA_SALIDA = os.path.join(os.path.dirname(__file__), "../outputs/resultados_batch.json")
TOTAL_SOLICITUDES = 10


def main():
    solicitudes = obtener_solicitudes_rango(1, TOTAL_SOLICITUDES)
    print(f"Iniciando procesamiento de {len(solicitudes)} solicitudes...\n")

    resultados = []
    exitosas = 0

    for i, solicitud in enumerate(solicitudes, start=1):
        id_sol = solicitud["id_solicitud"]
        etiqueta = f"[{i:02d}/{TOTAL_SOLICITUDES}] {id_sol} | {solicitud['razon_social']}"

        try:
            resultado = procesar_solicitud(solicitud)
            resumen = (
                f"clasificacion={resultado.clasificacion} | "
                f"riesgo={resultado.nivel_riesgo} | "
                f"inconsistencias={len(resultado.inconsistencias)}"
            )
            print(f"{etiqueta} -> {resumen}")
            resultados.append({
                "status": "ok",
                "id_solicitud": id_sol,
                "resultado": resultado.model_dump(),
            })
            exitosas += 1

        except Exception as exc:
            print(f"{etiqueta} -> ERROR: {exc}")
            resultados.append({
                "status": "error",
                "id_solicitud": id_sol,
                "error": str(exc),
            })

    # Guardar JSON consolidado
    os.makedirs(os.path.dirname(RUTA_SALIDA), exist_ok=True)
    with open(RUTA_SALIDA, "w", encoding="utf-8") as archivo:
        json.dump(resultados, archivo, ensure_ascii=False, indent=2)

    print(f"\nResultados guardados en: {RUTA_SALIDA}")
    print(f"Exitosas: {exitosas}/{TOTAL_SOLICITUDES} | Fallidas: {TOTAL_SOLICITUDES - exitosas}/{TOTAL_SOLICITUDES}")


if __name__ == "__main__":
    main()
