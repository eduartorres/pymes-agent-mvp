import json
import os
from typing import Dict, List

import requests


ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

# La key se lee en cada llamada para que funcione tanto con variable de entorno
# como cuando se inyecta directamente al proceso via os.environ en el script.
def _get_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY no esta definida en el entorno.")
    return key


PROMPT_SISTEMA = """Eres un agente especializado en analisis de solicitudes de seguro Multirriesgo PYME en Colombia.
Tu funcion es extraer informacion estructurada de documentos de soporte y del formulario de solicitud,
detectar inconsistencias entre fuentes, y clasificar el caso para su enrutamiento operativo.

Reglas de clasificacion:
- APROBACION_DIRECTA: informacion completa y consistente, menos de 3 siniestros, zona A o B.
- REVISION_ESPECIALISTA: inconsistencias detectadas, 3 o mas siniestros, zona C o D, o actividad de alto riesgo.
- INCOMPLETA: faltan documentos clave o la informacion minima no permite evaluar el riesgo.

Reglas de nivel de riesgo:
- BAJO: zona A, sin siniestros, sector de bajo riesgo (tecnologia, educacion, servicios profesionales).
- MEDIO: zona B o C, entre 1 y 2 siniestros, manufactura o comercio.
- ALTO: zona D, 3 o mas siniestros, construccion, transporte, o inconsistencias graves de ubicacion.

Responde unicamente con un JSON valido. Sin texto adicional, sin bloques de codigo markdown."""


def analizar_solicitud(solicitud: Dict, documentos: List[Dict]) -> Dict:
    """
    Envia la solicitud y sus documentos al modelo y retorna el JSON de analisis.

    Se usa requests directamente en lugar del SDK para mayor control sobre
    el manejo de errores HTTP y para evitar dependencias de estado del cliente.
    """
    prompt = _construir_prompt(solicitud, documentos)

    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 2048,
        "system": PROMPT_SISTEMA,
        "messages": [{"role": "user", "content": prompt}],
    }

    headers = {
        "x-api-key": _get_api_key(),
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    respuesta = requests.post(ANTHROPIC_URL, json=payload, headers=headers, timeout=60)
    respuesta.raise_for_status()

    contenido = respuesta.json()["content"][0]["text"].strip()
    contenido = _limpiar_markdown(contenido)

    return json.loads(contenido)


def _construir_prompt(solicitud: Dict, documentos: List[Dict]) -> str:
    """
    Construye el prompt de usuario combinando los datos del formulario
    con el texto extraido de cada documento de soporte.
    """
    bloque_documentos = ""
    for doc in documentos:
        bloque_documentos += f"\n\n--- Documento: {doc['nombre_archivo']} ---\n{doc['texto']}"

    return f"""Analiza la siguiente solicitud PYME y sus documentos de soporte.

Datos del formulario:
- ID solicitud: {solicitud['id_solicitud']}
- NIT declarado: {solicitud['nit']}
- Razon social declarada: {solicitud['razon_social']}
- Ciudad registrada: {solicitud['ciudad_registrada']}
- Departamento: {solicitud['departamento']}
- Sector declarado: {solicitud['sector_declarado']}
- Empleados declarados: {solicitud['numero_empleados_declarado']}
- Asesor: {solicitud['nombre_asesor']}
- Observacion del asesor: {solicitud['observacion_asesor']}

Documentos de soporte:{bloque_documentos}

Extrae y consolida la informacion. Detecta cualquier inconsistencia entre el formulario y los documentos.
Clasifica el caso y define su ruta de enrutamiento operativo.

Responde con este JSON exacto:
{{
  "nit_verificado": "string",
  "razon_social_verificada": "string",
  "ciudad_riesgo": "string (ciudad real del riesgo, puede diferir del formulario)",
  "departamento_verificado": "string",
  "actividad_economica": "string",
  "numero_empleados_verificado": integer,
  "antiguedad_empresa": "string o null",
  "siniestros_ultimos_5_anos": integer o null,
  "zona_manzaneo": "A, B, C o D segun los documentos, o null si no se puede determinar",
  "clasificacion": "APROBACION_DIRECTA | REVISION_ESPECIALISTA | INCOMPLETA",
  "nivel_riesgo": "BAJO | MEDIO | ALTO",
  "inconsistencias": [
    {{
      "campo": "nombre del campo con discrepancia",
      "valor_formulario": "valor registrado en el formulario",
      "valor_documento": "valor encontrado en los documentos",
      "descripcion": "explicacion breve de la discrepancia"
    }}
  ],
  "documentos_analizados": [
    {{
      "nombre_archivo": "string",
      "tipo_documento": "string",
      "campos_extraidos": {{}}
    }}
  ],
  "observacion_agente": "resumen ejecutivo del analisis en 2 o 3 oraciones",
  "ruta_recomendada": "accion concreta que debe tomar el equipo de suscripcion"
}}"""


def _limpiar_markdown(texto: str) -> str:
    """
    Elimina bloques de codigo markdown si el modelo los incluye en la respuesta.
    Algunos modelos envuelven el JSON en backticks aunque se les indique lo contrario.
    """
    if texto.startswith("```"):
        lineas = texto.split("\n")
        return "\n".join(lineas[1:-1])
    return texto
