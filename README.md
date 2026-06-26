# Agente de Análisis PYME — Seguros Multirriesgo

Sistema de automatización inteligente para el análisis inicial de solicitudes de seguro Multirriesgo PYME en Colombia. Extrae información de documentos no estructurados (PDFs), detecta inconsistencias entre fuentes y clasifica cada caso para su enrutamiento operativo.

---

## Arquitectura

```
CSV / Excel ──┐
              ├─► FastAPI ──► Orquestador ──► PyMuPDF (extracción PDF)
ZIP / PDFs ───┘                           └──► Groq LLM (análisis + clasificación)
                                                        │
                                                        ▼
                                               JSON estructurado
```

**Stack:**
- **FastAPI** — API REST con documentación automática (Swagger/OpenAPI)
- **PyMuPDF** — extracción de texto nativo de PDFs sin OCR
- **Groq** (`llama3-8b-8192`) — análisis semántico, extracción de campos y clasificación
- **openpyxl** — lectura del Excel de solicitudes

---

## Requisitos

- Python 3.10+
- API Key de Groq (gratuita en [console.groq.com](https://console.groq.com))

---

## Instalación

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd pymes_agent

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar API Key de Groq
export GROQ_API_KEY="gsk_..."   # Linux / Mac
set GROQ_API_KEY=gsk_...        # Windows CMD
```

---

## Datos de entrada

Coloca los archivos en la carpeta `data/`:

```
data/
├── solicitudes.xlsx          # Excel con las 100 solicitudes
└── soportes/
    ├── SOL-00001/
    │   ├── Camara_Comercio_SOL-00001.pdf
    │   └── Reporte_Siniestralidad_SOL-00001.pdf
    ├── SOL-00002/
    │   └── ...
    └── ...
```

Si tienes el ZIP, extráelo directamente en `data/`:
```bash
unzip soportes.zip -d data/
```

---

## Ejecución

### Iniciar la API

```bash
cd pymes_agent
uvicorn app.main:app --reload --port 8000
```

La API queda disponible en `http://localhost:8000`.
Documentación interactiva: `http://localhost:8000/docs`

### Endpoints disponibles

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/` | Estado del servicio |
| `GET` | `/api/v1/solicitudes?limite=20` | Lista solicitudes del Excel |
| `POST` | `/api/v1/analizar/{id_solicitud}` | Analiza una solicitud por ID |
| `POST` | `/api/v1/batch?inicio=1&fin=10` | Procesa un rango en batch |

### Ejemplos con curl

```bash
# Listar solicitudes disponibles
curl http://localhost:8000/api/v1/solicitudes?limite=5

# Analizar una solicitud individual
curl -X POST http://localhost:8000/api/v1/analizar/SOL-00001

# Procesar batch (primeras 10)
curl -X POST "http://localhost:8000/api/v1/batch?inicio=1&fin=10"
```

---

## Prueba batch por consola

```bash
cd pymes_agent
python tests/prueba_batch.py
```

Procesa las 10 primeras solicitudes y guarda el JSON en `outputs/resultados_batch.json`.

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
    "documentos_analizados": [...],
    "observacion_agente": "...",
    "ruta_recomendada": "..."
  }
}
```

**Clasificaciones posibles:**
- `APROBACION_DIRECTA` — información completa y consistente, riesgo bajo o medio
- `REVISION_ESPECIALISTA` — inconsistencias detectadas, alto siniestro o zona de riesgo
- `INCOMPLETA` — faltan documentos o información mínima

---

## Estructura del proyecto

```
pymes_agent/
├── app/
│   ├── main.py                  # Punto de entrada FastAPI
│   ├── routers/
│   │   └── analisis.py          # Endpoints REST
│   ├── services/
│   │   ├── loader.py            # Lectura del Excel
│   │   ├── extractor.py         # Extracción de texto PDF (PyMuPDF)
│   │   ├── agente.py            # Integración Groq LLM
│   │   └── orquestador.py       # Pipeline completo
│   └── models/
│       └── schemas.py           # Modelos Pydantic
├── data/
│   ├── solicitudes.xlsx
│   └── soportes/
├── outputs/
│   └── resultados_batch.json    # Generado por prueba_batch.py
├── tests/
│   └── prueba_batch.py
├── requirements.txt
└── README.md
```

---

## Decisiones de diseño

### ¿Por qué Groq + llama3-8b-8192?
Modelo de uso gratuito con capacidad suficiente para extracción de entidades y clasificación de documentos cortos. Latencia baja (~1-2 segundos por solicitud) y sin costo operativo para un MVP.

### ¿Por qué PyMuPDF?
Los PDFs de soporte tienen capa de texto nativa, lo que hace innecesario OCR pesado. PyMuPDF extrae texto en milisegundos con una sola dependencia.

### ¿Por qué no guardar en base de datos?
Para MVP de demostración, el JSON en disco es suficiente y elimina dependencias adicionales. En producción se agregaría PostgreSQL o DynamoDB.

### Detección de inconsistencias
El agente compara los valores del formulario CSV contra los datos extraídos de los PDFs. Casos como SOL-00045 (ciudad declarada Medellín pero riesgo real en Bogotá) son detectados automáticamente por el LLM al leer la observación del asesor y los documentos.
