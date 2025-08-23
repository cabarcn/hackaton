import json
from typing import Any, Dict
from .ai_client import chat  # <- solo este import (no al revés)

PROMPT_SISTEMA = (
    "Eres un revisor experto en bases técnicas y normativas de licitaciones públicas en Chile. "
    "Responde SOLO JSON con las claves EXACTAS: \n"
    "{\n"
    '  "observaciones": [{"campo":"...","tipo":"riesgo|formato|coherencia|faltante","detalle":"..."}],\n'
    '  "correcciones_sugeridas": [{"campo":"...","sugerencia":"..."}],\n'
    '  "resumen_propuesta": "máx 120 palabras, tono institucional"\n'
    "}\n"
    "No incluyas texto adicional fuera del JSON."
)

def _fallback_result(msg: str) -> Dict[str, Any]:
    return {
        "observaciones": [{"campo": "general", "tipo": "riesgo", "detalle": msg}],
        "correcciones_sugeridas": [{"campo": "general", "sugerencia": "Verificar configuración de AI y conectividad."}],
        "resumen_propuesta": "Análisis no disponible por error de conexión."
    }

def _coerce_dict(data: Any) -> Dict[str, Any]:
    # Acepta dataclass/objeto con atributos o dict “normal”.
    if isinstance(data, dict):
        return data
    # objeto simple con atributos
    try:
        return {
            "proposito": getattr(data, "proposito", None),
            "objetivo": getattr(data, "objetivo", None),
            "alcance": getattr(data, "alcance", None),
            "req_tecnicos": getattr(data, "req_tecnicos", None),
            "criterios_eval": getattr(data, "criterios_eval", None),
            "presupuesto": getattr(data, "presupuesto", None),
            "fecha_inicio": getattr(data, "fecha_inicio", None),
            "fecha_cierre": getattr(data, "fecha_cierre", None),
        }
    except Exception:
        return {"raw": str(data)}

def _validate_contract(obj: Dict[str, Any]) -> Dict[str, Any]:
    # Asegura las 3 claves y tipos mínimos
    out = {
        "observaciones": obj.get("observaciones") or [],
        "correcciones_sugeridas": obj.get("correcciones_sugeridas") or [],
        "resumen_propuesta": obj.get("resumen_propuesta") or "",
    }
    # Normaliza tipos raros
    if not isinstance(out["observaciones"], list): out["observaciones"] = []
    if not isinstance(out["correcciones_sugeridas"], list): out["correcciones_sugeridas"] = []
    if not isinstance(out["resumen_propuesta"], str): out["resumen_propuesta"] = str(out["resumen_propuesta"])
    return out

def analizar_renca(data: Any) -> Dict[str, Any]:
    """
    data: dict o objeto con atributos del formulario RENCA.
    Retorna: dict con claves 'observaciones', 'correcciones_sugeridas', 'resumen_propuesta'.
    """
    try:
        payload = _coerce_dict(data)
        messages = [
            {"role": "system", "content": PROMPT_SISTEMA},
            {"role": "user", "content": "Analiza la siguiente solicitud RENCA:\n" + json.dumps(payload, ensure_ascii=False, default=str)}
        ]

        # Intento 1: pedir JSON estricto (OpenAI lo respeta; DeepSeek puede ignorar pero no rompe)
        content = chat(messages, json_mode=True)
        try:
            parsed = json.loads(content)
            return _validate_contract(parsed)
        except Exception:
            # Intento 2: sin json_mode y parseo laxo
            content2 = chat(messages, json_mode=False)
            try:
                parsed2 = json.loads(content2)
                return _validate_contract(parsed2)
            except Exception:
                # Último recurso: encapsular texto libre en el resumen
                return {
                    "observaciones": [],
                    "correcciones_sugeridas": [],
                    "resumen_propuesta": (content2 or "").strip()[:1000],
                }
    except Exception as e:
        return _fallback_result(str(e))