import os
from typing import List, Dict

import fitz  # PyMuPDF


# Ruta base de los soportes extraidos del ZIP. Se resuelve relativa a este modulo
# para que funcione independientemente del directorio de trabajo.
BASE_SOPORTES = os.path.join(os.path.dirname(__file__), "../../data/soportes")


def extraer_texto_pdf(ruta_pdf: str) -> str:
    """
    Abre un PDF y concatena el texto de todas sus paginas.

    PyMuPDF extrae el texto nativo sin necesidad de OCR, lo que es suficiente
    para los documentos generados digitalmente que maneja este sistema.
    Si el archivo no se puede leer, retorna una cadena con el mensaje de error
    para que el agente pueda registrar el fallo sin detener el pipeline.
    """
    try:
        doc = fitz.open(ruta_pdf)
        paginas = [pagina.get_text() for pagina in doc]
        doc.close()
        return " ".join(paginas).strip()
    except Exception as exc:
        return f"[Error al leer {os.path.basename(ruta_pdf)}: {exc}]"


def obtener_pdfs_solicitud(id_solicitud: str) -> List[Dict[str, str]]:
    """
    Busca y extrae el texto de todos los PDFs asociados a una solicitud.

    Los soportes se organizan en carpetas por ID de solicitud dentro de BASE_SOPORTES.
    El orden alfabetico de los archivos es suficiente porque los nombres siguen
    una convencion consistente (tipo_documento_SOL-XXXXX.pdf).
    """
    carpeta = os.path.join(BASE_SOPORTES, id_solicitud)

    if not os.path.isdir(carpeta):
        return []

    documentos = []
    for nombre_archivo in sorted(os.listdir(carpeta)):
        if not nombre_archivo.lower().endswith(".pdf"):
            continue

        ruta = os.path.join(carpeta, nombre_archivo)
        documentos.append({
            "nombre_archivo": nombre_archivo,
            "texto": extraer_texto_pdf(ruta),
        })

    return documentos


def clasificar_tipo_documento(nombre_archivo: str) -> str:
    """
    Infiere el tipo de documento a partir de palabras clave en el nombre del archivo.

    Esta clasificacion es heuristica y cubre los tipos que maneja el proceso
    actual: Camara de Comercio, RUT, PILA, Formulario de Vinculacion y
    Reporte de Siniestralidad. Cualquier otro archivo queda como soporte generico.
    """
    nombre = nombre_archivo.lower()

    if "camara" in nombre or "existencia" in nombre:
        return "Camara de Comercio"
    if "rut" in nombre:
        return "RUT"
    if "siniestralidad" in nombre or "siniestro" in nombre:
        return "Reporte de Siniestralidad"
    if "formulario" in nombre or "vinculacion" in nombre:
        return "Formulario de Vinculacion"
    if "pila" in nombre or "planilla" in nombre:
        return "Planilla PILA"

    return "Documento de soporte"
