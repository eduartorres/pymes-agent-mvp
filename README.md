# Agente de Análisis PYME — Seguros Multirriesgo

Sistema de automatización inteligente para el análisis inicial de solicitudes de seguro Multirriesgo PYME en Colombia. Extrae información de documentos no estructurados (PDFs), detecta inconsistencias entre fuentes y clasifica cada caso para su enrutamiento operativo.

---

## Arquitectura

```
Excel / CSV ──┐
              ├──► FastAPI ──► Orquestador ──► PyMuPDF (extracción PDF)
ZIP / PDFs ───┘                            └──► Claude (análisis + clasificación)
                                                         │
                                                         ▼
                                                JSON estructurado
```

Stack:

- FastAPI — API REST con documentación automática en /docs
- PyMuPDF — extracción de texto nativo de PDFs sin OCR
- Claude claude-haiku-4-5 (Anthropic) — análisis semántico, extracción de campos y clasificación
- openpyxl — lectura del Excel de solicitudes

---

## Requisitos

- Python 3.10+
- API Key de Anthropic (console.anthropic.com)

---

## Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/eduartorres/pymes-agent-mvp.git
cd pymes_agent

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar la variable de entorno con la API Key
cp .env.example .env
# Editar .env y reemplazar el valor de ANTHROPIC_API_KEY

# 5. Exportar la variable antes de ejecutar
export ANTHROPIC_API_KEY="sk-ant-..."   # Linux / Mac
set ANTHROPIC_API_KEY=sk-ant-...        # Windows CMD
```

---

## Datos de entrada

Coloca los archivos en la carpeta `data/`:

```
data/
├── solicitudes.xlsx
└── soportes/
    ├── SOL-00001/
    │   ├── Camara_Comercio_SOL-00001.pdf
    │   └── Reporte_Siniestralidad_SOL-00001.pdf
    ├── SOL-00002/
    │   └── ...
    └── ...
```

Si tienes el ZIP de soportes, extráelo directamente en `data/`:

```bash
unzip soportes.zip -d data/
```

---

## Ejecución

### Iniciar la API

```bash
uvicorn app.main:app --reload --port 8000
```

La API queda disponible en http://localhost:8000.
Documentación interactiva: http://localhost:8000/docs

### Endpoints disponibles

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | / | Estado del servicio |
| GET | /api/v1/solicitudes?limite=20 | Lista solicitudes del Excel |
| POST | /api/v1/analizar/{id_solicitud} | Analiza una solicitud por ID |
| POST | /api/v1/batch?inicio=1&fin=10 | Procesa un rango en batch |

### Ejemplos con curl

```bash
# Listar solicitudes disponibles
curl http://localhost:8000/api/v1/solicitudes?limite=5

# Analizar una solicitud individual
curl -X POST http://localhost:8000/api/v1/analizar/SOL-00001

# Procesar batch de las primeras 10 solicitudes
curl -X POST "http://localhost:8000/api/v1/batch?inicio=1&fin=10"
```

---

## Prueba batch por consola

```bash
python tests/prueba_batch.py
```

Procesa las 10 primeras solicitudes y guarda el resultado en `outputs/resultados_batch.json`.

---

## Estructura del JSON de salida

```json
{
  "status": "ok",
  "id_solicitud": "SOL-00001",
  "resultado": {
    "nit_verificado": "900000000",
    "razon_social_verificada": "Panadería SA",
    "ciudad_riesgo": "Ibagué",
    "departamento_verificado": "Tolima",
    "actividad_economica": "Fabricación de prendas",
    "numero_empleados_verificado": 29,
    "antiguedad_empresa": "47 años",
    "siniestros_ultimos_5_anos": 5,
    "zona_manzaneo": "D",
    "clasificacion": "REVISION_ESPECIALISTA",
    "nivel_riesgo": "ALTO",
    "inconsistencias": [],
    "documentos_analizados": [],
    "observacion_agente": "...",
    "ruta_recomendada": "..."
  }
}
```

Clasificaciones posibles:

- APROBACION_DIRECTA: información completa y consistente, riesgo bajo o medio
- REVISION_ESPECIALISTA: inconsistencias detectadas, alto siniestro o zona de riesgo elevado
- INCOMPLETA: faltan documentos o información mínima para evaluar el caso

---

## Estructura del proyecto

```
pymes_agent/
├── app/
│   ├── main.py                  # Punto de entrada FastAPI
│   ├── routers/
│   │   └── analisis.py          # Endpoints REST
│   ├── services/
│   │   ├── loader.py            # Lectura y normalización del Excel
│   │   ├── extractor.py         # Extracción de texto PDF con PyMuPDF
│   │   ├── agente.py            # Integración con Claude (Anthropic)
│   │   └── orquestador.py       # Pipeline completo de análisis
│   └── models/
│       └── schemas.py           # Modelos Pydantic de entrada y salida
├── data/
│   └── solicitudes.xlsx
├── outputs/
│   └── resultados_batch.json
├── tests/
│   └── prueba_batch.py
├── arquitectura.md
├── resumen_ejecutivo.md
├── requirements.txt
├── .env.example
└── README.md
```

---

## Decisiones de diseño

**Por qué Claude de Anthropic para el análisis**
El caso requiere extracción de entidades de documentos con estructura variada y detección de inconsistencias entre fuentes. Claude maneja bien esa tarea con un prompt bien definido y produce JSON estructurado de forma consistente, lo que simplifica el parsing en el pipeline.

**Por qué PyMuPDF**
Los documentos de soporte tienen capa de texto nativa, lo que hace innecesario OCR. PyMuPDF extrae el contenido en milisegundos con una sola dependencia y sin servicios externos.

**Por qué no base de datos**
Para un MVP de demostración el JSON en disco es suficiente y elimina dependencias de infraestructura. En producción se integraría con la base de datos de gestión de solicitudes existente.

**Detección de inconsistencias**
El agente cruza los valores del formulario contra los datos extraídos de los PDFs. Casos como una ciudad declarada incorrectamente en el formulario pero corregida en la observación del asesor son detectados automáticamente porque el modelo lee todas las fuentes en un mismo contexto.
