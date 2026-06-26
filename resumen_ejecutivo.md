# Resumen Ejecutivo — Agente de Análisis Automatizado para Solicitudes PYME

## Contexto del problema

El proceso actual de análisis de solicitudes de seguro Multirriesgo PYME depende casi en su totalidad de la capacidad de un analista para revisar manualmente cada caso. Ese analista debe cruzar los datos del formulario de solicitud contra documentos de soporte en múltiples formatos, detectar inconsistencias, evaluar el perfil de riesgo y decidir si el caso avanza directamente o requiere una revisión especializada.

El problema no es la complejidad de cada solicitud individual. El problema es que ese proceso se repite de forma idéntica para cada caso, consume tiempo de profesionales calificados en tareas que no requieren juicio experto, y genera un cuello de botella que limita la capacidad de crecimiento del canal PYME sin incrementar proporcionalmente la planta de suscripción.

## Enfoque de solución

La solución propuesta automatiza la etapa de análisis inicial sin reemplazar el juicio del suscriptor en los casos que realmente lo requieren. El sistema extrae la información relevante de los documentos de soporte, la contrasta contra los datos declarados en el formulario, detecta discrepancias y produce una clasificación operativa con la ruta de acción recomendada.

El resultado es que el analista recibe un caso ya procesado, con las inconsistencias identificadas y la información consolidada, en lugar de un paquete de documentos sin procesar. Su tiempo se concentra en los casos que presentan señales de alerta, no en la revisión rutinaria de expedientes completos.

## Arquitectura y decisiones de diseño

El sistema se construyó sobre cuatro componentes con responsabilidades bien delimitadas.

El primero es el módulo de carga, que lee el archivo de solicitudes estructuradas y normaliza los datos antes de procesarlos. Esta normalización incluye la corrección de formatos numéricos que Excel introduce automáticamente, como la notación científica en los NITs, un problema frecuente cuando los datos vienen de múltiples fuentes y formularios.

El segundo es el módulo de extracción, que lee los documentos PDF de soporte y obtiene su contenido textual. Se eligió PyMuPDF para esta tarea porque los documentos del proceso tienen capa de texto nativa, lo que hace innecesario el uso de OCR. Eso reduce significativamente la complejidad técnica y el tiempo de procesamiento por documento.

El tercero es el agente de análisis, que recibe el texto de los documentos junto con los datos del formulario y produce el análisis consolidado. Este componente utiliza un modelo de lenguaje a través de la API de Groq, con un prompt diseñado específicamente para el contexto de suscripción PYME en Colombia. El modelo identifica inconsistencias entre fuentes, extrae los campos relevantes para la evaluación de riesgo y genera la clasificación operativa con la justificación correspondiente.

El cuarto es la capa de exposición, implementada en FastAPI, que publica el pipeline como una API REST con tres endpoints: análisis individual por solicitud, procesamiento en lote y consulta del catálogo de solicitudes disponibles. Esta arquitectura permite integrar el agente con los sistemas existentes de la compañía sin modificar los flujos actuales, conectándolo como un servicio independiente.

## Criterios de clasificación operativa

El agente clasifica cada solicitud en una de tres categorías que determinan su ruta dentro del flujo de suscripción.

Aprobación directa aplica cuando la información es completa y consistente entre el formulario y los documentos, el historial de siniestros está dentro de los umbrales aceptables y la ubicación del riesgo corresponde a una zona con nivel de exposición bajo o medio.

Revisión especialista aplica cuando se detectan inconsistencias entre fuentes, cuando el historial de siniestros supera el umbral definido, cuando la actividad económica corresponde a un sector de alto riesgo o cuando la zona de manzaneo indica una exposición elevada.

Incompleta aplica cuando la documentación de soporte no es suficiente para evaluar alguno de los criterios anteriores, lo que genera una devolución al asesor con indicación específica de lo que falta.

## Valor operativo esperado

El impacto directo de este sistema se concentra en tres dimensiones.

En capacidad de procesamiento, el sistema puede analizar en paralelo un volumen de solicitudes que hoy requeriría múltiples analistas trabajando en secuencia, sin que el tiempo de respuesta dependa del volumen de la cola.

En consistencia, la evaluación sigue los mismos criterios en todos los casos, eliminando la variabilidad que introduce el juicio individual en decisiones que deberían ser estandarizadas.

En trazabilidad, cada decisión queda registrada con su justificación, los campos extraídos de cada documento y las inconsistencias detectadas. Eso facilita auditorías, permite identificar patrones en los casos problemáticos y genera un historial que alimenta mejoras futuras al modelo de clasificación.

## Limitaciones del prototipo y ruta de evolución

Este prototipo demuestra la viabilidad técnica del enfoque y cubre el flujo completo desde la recepción de la solicitud hasta la clasificación operativa. Para una implementación en producción, los aspectos prioritarios a desarrollar son la integración con los sistemas internos de gestión de solicitudes, el manejo de documentos escaneados que requieren OCR, la construcción de un modelo de clasificación supervisado entrenado con el historial de decisiones de los suscriptores y la implementación de un esquema de monitoreo que permita detectar degradación en la calidad del análisis a lo largo del tiempo.

La arquitectura modular del sistema fue diseñada precisamente para facilitar esa evolución. Cada componente puede reemplazarse o mejorarse de forma independiente sin afectar los demás.
