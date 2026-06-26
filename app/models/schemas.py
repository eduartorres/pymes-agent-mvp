from pydantic import BaseModel
from typing import Optional, List


class SolicitudInput(BaseModel):
    id_solicitud: str
    nit: str
    razon_social: str
    ciudad_registrada: str
    departamento: str
    sector_declarado: str
    numero_empleados_declarado: int
    nombre_asesor: str
    observacion_asesor: str
    ruta_soporte: str


class InconsistenciaDetectada(BaseModel):
    campo: str
    valor_formulario: str
    valor_documento: str
    descripcion: str


class DocumentoAnalizado(BaseModel):
    nombre_archivo: str
    tipo_documento: str
    campos_extraidos: dict


class ResultadoAnalisis(BaseModel):
    id_solicitud: str
    nit_verificado: str
    razon_social_verificada: str
    ciudad_riesgo: str
    departamento_verificado: str
    actividad_economica: str
    numero_empleados_verificado: int
    antiguedad_empresa: Optional[str]
    siniestros_ultimos_5_anos: Optional[int]
    zona_manzaneo: Optional[str]
    clasificacion: str                        # APROBACION_DIRECTA | REVISION_ESPECIALISTA | INCOMPLETA
    nivel_riesgo: str                         # BAJO | MEDIO | ALTO
    inconsistencias: List[InconsistenciaDetectada]
    documentos_analizados: List[DocumentoAnalizado]
    observacion_agente: str
    ruta_recomendada: str


class RespuestaAPI(BaseModel):
    status: str
    id_solicitud: str
    resultado: ResultadoAnalisis


class RespuestaBatch(BaseModel):
    status: str
    total_procesadas: int
    exitosas: int
    fallidas: int
    resultados: List[RespuestaAPI]
