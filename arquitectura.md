# Diagrama de Arquitectura — Agente PYME

## Flujo general

```
Entrada
───────────────────────────────────────────────────────────────
  Excel de solicitudes          ZIP de soportes
  (campos estructurados)        (PDFs por solicitud)
         │                              │
         └──────────────┬───────────────┘
                        │
                        ▼
API Gateway
───────────────────────────────────────────────────────────────
                   FastAPI
          POST /analizar/{id}
          POST /batch?inicio=1&fin=10
          GET  /solicitudes

                        │
                        ▼
Orquestador
───────────────────────────────────────────────────────────────
             Pipeline de procesamiento
          valida entrada / coordina etapas

              │                    │
              ▼                    ▼
     Módulo de carga        Módulo de extracción
     loader.py              extractor.py
     Lee Excel              Lee PDFs con PyMuPDF
     Normaliza NITs         Clasifica tipo de documento
     Normaliza tipos        Retorna texto por archivo

              └────────────────────┘
                        │
                        ▼
Agente de análisis
───────────────────────────────────────────────────────────────
                    agente.py
         Construye prompt con datos + documentos
         Llama al modelo de lenguaje (Groq / LLM)
         Parsea JSON de respuesta
         Detecta inconsistencias entre fuentes
         Clasifica el caso operativamente

                        │
                        ▼
Salida
───────────────────────────────────────────────────────────────
              JSON estructurado por solicitud
      {
        clasificacion: APROBACION_DIRECTA
                       REVISION_ESPECIALISTA
                       INCOMPLETA

        nivel_riesgo:  BAJO / MEDIO / ALTO

        inconsistencias: [ { campo, valor_formulario,
                              valor_documento, descripcion } ]

        documentos_analizados: [ { nombre, tipo, campos } ]

        observacion_agente: resumen del análisis
        ruta_recomendada:   acción para el equipo de suscripción
      }
```

## Componentes y responsabilidades

| Componente | Archivo | Responsabilidad |
|---|---|---|
| API Gateway | routers/analisis.py | Expone los endpoints REST y valida las entradas |
| Orquestador | services/orquestador.py | Coordina el pipeline y construye la respuesta tipada |
| Carga | services/loader.py | Lee el Excel y normaliza los datos estructurados |
| Extracción | services/extractor.py | Extrae texto de PDFs y clasifica el tipo de documento |
| Agente | services/agente.py | Llama al LLM, construye el prompt y parsea la respuesta |
| Esquemas | models/schemas.py | Define los contratos de entrada y salida con Pydantic |

## Tecnologías

| Capa | Tecnología | Justificación |
|---|---|---|
| API | FastAPI + Uvicorn | Tipado nativo con Pydantic, documentación automática, alto rendimiento |
| Extracción PDF | PyMuPDF | Extracción de texto nativo sin OCR, una sola dependencia |
| Análisis LLM | Groq (llama3-8b-8192) | Acceso gratuito, latencia baja, suficiente capacidad para extracción estructurada |
| Lectura Excel | openpyxl | Lectura en modo read-only, eficiente en memoria |
| Contratos | Pydantic v2 | Validación automática de tipos en entrada y salida de la API |

## Decisiones de diseño relevantes

**Separación de extracción y análisis.** El módulo de extracción (PyMuPDF) y el módulo de análisis (LLM) son independientes. Esto permite reemplazar cualquiera de los dos sin afectar el resto del pipeline. Si en el futuro los documentos llegan escaneados, se agrega OCR únicamente en el extractor.

**Prompt con reglas de negocio explícitas.** Las reglas de clasificación operativa están en el system prompt del agente, no dispersas en el código. Eso facilita ajustarlas cuando cambien los criterios de suscripción sin tocar la lógica de la aplicación.

**Fallback a datos del formulario.** Cuando el modelo no puede extraer un campo de los documentos, el sistema usa el valor declarado en el formulario como valor por defecto. El caso no falla, queda marcado como incompleto con indicación del campo faltante.

**API stateless.** Cada llamada es independiente. El sistema no mantiene sesión ni estado entre solicitudes, lo que facilita el escalado horizontal cuando el volumen de solicitudes lo requiera.
