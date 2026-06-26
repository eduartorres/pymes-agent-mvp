from typing import Dict

from app.models.schemas import DocumentoAnalizado, InconsistenciaDetectada, ResultadoAnalisis
from app.services.agente import analizar_solicitud
from app.services.extractor import clasificar_tipo_documento, obtener_pdfs_solicitud


def procesar_solicitud(solicitud: Dict) -> ResultadoAnalisis:
    """
    Pipeline completo de analisis para una solicitud PYME.

    El flujo tiene tres etapas secuenciales:
    1. Extraccion: se leen los PDFs de soporte y se obtiene el texto de cada uno.
    2. Analisis: el agente LLM consolida el formulario con los documentos,
       detecta inconsistencias y produce la clasificacion operativa.
    3. Construccion: la respuesta del modelo se mapea al schema tipado de la API.

    Separar estas tres responsabilidades permite testear cada etapa de forma
    independiente y facilita reemplazar el LLM sin tocar la logica de extraccion.
    """
    id_solicitud = solicitud["id_solicitud"]

    # Etapa 1: extraccion de texto de los PDFs de soporte
    documentos = obtener_pdfs_solicitud(id_solicitud)
    for doc in documentos:
        doc["tipo_documento"] = clasificar_tipo_documento(doc["nombre_archivo"])

    # Etapa 2: analisis semantico y clasificacion con el agente
    resultado_llm = analizar_solicitud(solicitud, documentos)

    # Etapa 3: construccion del objeto de respuesta tipado
    return _construir_resultado(id_solicitud, solicitud, resultado_llm)


def _construir_resultado(
    id_solicitud: str,
    solicitud: Dict,
    resultado_llm: Dict,
) -> ResultadoAnalisis:
    """
    Mapea el diccionario crudo del LLM al schema Pydantic de la API.

    Los valores del formulario original actuan como fallback en caso de que
    el modelo no retorne un campo esperado, lo que puede ocurrir si el
    documento de soporte no contiene esa informacion.
    """
    inconsistencias = [
        InconsistenciaDetectada(**inc)
        for inc in resultado_llm.get("inconsistencias", [])
    ]

    documentos_analizados = [
        DocumentoAnalizado(
            nombre_archivo=doc.get("nombre_archivo", ""),
            tipo_documento=doc.get("tipo_documento", ""),
            campos_extraidos=doc.get("campos_extraidos", {}),
        )
        for doc in resultado_llm.get("documentos_analizados", [])
    ]

    return ResultadoAnalisis(
        id_solicitud=id_solicitud,
        nit_verificado=resultado_llm.get("nit_verificado", solicitud["nit"]),
        razon_social_verificada=resultado_llm.get("razon_social_verificada", solicitud["razon_social"]),
        ciudad_riesgo=resultado_llm.get("ciudad_riesgo", solicitud["ciudad_registrada"]),
        departamento_verificado=resultado_llm.get("departamento_verificado", solicitud["departamento"]),
        actividad_economica=resultado_llm.get("actividad_economica", ""),
        numero_empleados_verificado=resultado_llm.get(
            "numero_empleados_verificado", solicitud["numero_empleados_declarado"]
        ),
        antiguedad_empresa=resultado_llm.get("antiguedad_empresa"),
        siniestros_ultimos_5_anos=resultado_llm.get("siniestros_ultimos_5_anos"),
        zona_manzaneo=resultado_llm.get("zona_manzaneo"),
        clasificacion=resultado_llm.get("clasificacion", "INCOMPLETA"),
        nivel_riesgo=resultado_llm.get("nivel_riesgo", "MEDIO"),
        inconsistencias=inconsistencias,
        documentos_analizados=documentos_analizados,
        observacion_agente=resultado_llm.get("observacion_agente", ""),
        ruta_recomendada=resultado_llm.get("ruta_recomendada", ""),
    )
