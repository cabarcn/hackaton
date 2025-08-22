import os, json, re
from datetime import date
from decimal import Decimal, InvalidOperation

# --- Config ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
AI_FORCE_OFFLINE = os.getenv("AI_FORCE_OFFLINE", "0") == "1"

# Si tienes saldo luego, el SDK OpenAI sirve apuntando al base_url de DeepSeek
client = None
if DEEPSEEK_API_KEY and not AI_FORCE_OFFLINE:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    except Exception:
        client = None

PROMPT_BASE = """json
Eres revisor técnico de licitaciones (Chile).
Devuelve SOLO JSON con:
{
  "observaciones": [{"campo":"...","tipo":"faltante|formato|coherencia|riesgo","detalle":"..."}],
  "correcciones_sugeridas": [{"campo":"...","sugerencia":"..."}],
  "resumen_propuesta": "máx 120 palabras, tono institucional"
}
"""

# --------- Reglas OFFLINE (sin LLM) ----------
KW_ENTREGABLES = ["entregable", "hito", "informe", "reporte", "manual", "capacit", "soporte"]
KW_NORMAS = ["norma", "estándar", "iso", "nist", "ley", "decreto", "reglament", "oguc", "nti"]

def _find_percentages(text):
    nums = [int(x) for x in re.findall(r'(\d{1,3})\s*%', text)]
    return nums, sum(nums)

def _has_keywords(text, keywords):
    t = text.lower()
    return any(k in t for k in keywords)

def _offline_review(obj):
    obs, corr = [], []

    # Presupuesto
    if obj.presupuesto is None:
        obs.append({"campo":"presupuesto","tipo":"faltante","detalle":"No se definió presupuesto."})
        corr.append({"campo":"presupuesto","sugerencia":"Ingrese un monto o rango con tope máximo."})
    else:
        try:
            if Decimal(obj.presupuesto) <= 0:
                obs.append({"campo":"presupuesto","tipo":"formato","detalle":"Presupuesto debe ser > 0."})
                corr.append({"campo":"presupuesto","sugerencia":"Ajuste el monto a un valor positivo."})
        except InvalidOperation:
            obs.append({"campo":"presupuesto","tipo":"formato","detalle":"Formato inválido de presupuesto."})
            corr.append({"campo":"presupuesto","sugerencia":"Use solo números y separador decimal punto."})

    # Fechas
    if not obj.fecha_inicio or not obj.fecha_cierre:
        obs.append({"campo":"fechas","tipo":"faltante","detalle":"Faltan fecha de inicio o cierre."})
        corr.append({"campo":"fechas","sugerencia":"Indique ambas fechas y asegure coherencia temporal."})
    else:
        if obj.fecha_inicio < date.today():
            obs.append({"campo":"fecha_inicio","tipo":"riesgo","detalle":"Fecha de inicio en el pasado."})
        if obj.fecha_cierre <= obj.fecha_inicio:
            obs.append({"campo":"fechas","tipo":"coherencia","detalle":"Cierre debe ser posterior al inicio."})
            corr.append({"campo":"fechas","sugerencia":"Ajuste el cronograma para asegurar continuidad."})

    # Longitudes mínimas
    mins = {"objetivo":30,"alcance":50,"req_tecnicos":50,"criterios_eval":30}
    for f, m in mins.items():
        val = (getattr(obj, f) or "").strip()
        if len(val) < m:
            obs.append({"campo":f,"tipo":"faltante","detalle":f"Contenido escaso (<{m} chars)."})
            corr.append({"campo":f,"sugerencia":f"Amplíe {f} con detalle suficiente y ejemplos."})

    # Alcance con entregables
    if not _has_keywords(obj.alcance or "", KW_ENTREGABLES):
        obs.append({"campo":"alcance","tipo":"coherencia","detalle":"No se identifican entregables/hitos."})
        corr.append({"campo":"alcance","sugerencia":"Enumere entregables (informes, manuales, capacitación)."})
    
    # Requisitos con normas
    if not _has_keywords(obj.req_tecnicos or "", KW_NORMAS):
        obs.append({"campo":"req_tecnicos","tipo":"coherencia","detalle":"No se mencionan normas/estándares."})
        corr.append({"campo":"req_tecnicos","sugerencia":"Referencie normas (p.ej., ISO/NIST/leyes aplicables)."})

    # Criterios de evaluación suman 100
    nums, total = _find_percentages(obj.criterios_eval or "")
    if not nums:
        obs.append({"campo":"criterios_eval","tipo":"formato","detalle":"No se detectan porcentajes."})
        corr.append({"campo":"criterios_eval","sugerencia":"Incluya ponderaciones que sumen 100%."})
    elif total != 100:
        obs.append({"campo":"criterios_eval","tipo":"coherencia","detalle":f"Las ponderaciones suman {total}% (debe ser 100%)."})
        corr.append({"campo":"criterios_eval","sugerencia":"Ajuste los porcentajes para totalizar 100%."})

    resumen = (
        f"Propuesta para «{obj.proposito}». Se sugiere robustecer criterios, "
        f"definir entregables y referencias normativas, y validar presupuesto/fechas."
    )
    return {"observaciones": obs, "correcciones_sugeridas": corr, "resumen_propuesta": resumen}

# --------- Backend DeepSeek ----------
def _backend_deepseek(obj):
    mensajes = [
        {"role":"system","content":PROMPT_BASE},
        {"role":"user","content":(
            f"PROPÓSITO: {obj.proposito}\n"
            f"OBJETIVO: {obj.objetivo}\nALCANCE: {obj.alcance}\n"
            f"REQ_TECNICOS: {obj.req_tecnicos}\nCRITERIOS_EVAL: {obj.criterios_eval}\n"
            f"PRESUPUESTO: {obj.presupuesto}\nFECHAS: {obj.fecha_inicio} a {obj.fecha_cierre}"
        )}
    ]
    resp = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=mensajes,
        response_format={"type":"json_object"}
    )
    return json.loads(resp.choices[0].message.content)

def analizar_postulacion(obj):
    # Forzar offline por bandera
    if AI_FORCE_OFFLINE:
        return _offline_review(obj)

    # Intentar DeepSeek si hay cliente
    if client:
        try:
            return _backend_deepseek(obj)
        except Exception as e:
            msg = str(e)
            # Si es saldo insuficiente o 402 → log suave y caer a offline
            if "402" in msg or "Insufficient Balance" in msg:
                return _offline_review(obj) | {
                    "observaciones": [{"campo":"general","tipo":"riesgo",
                        "detalle":"DeepSeek: saldo insuficiente (HTTP 402). Se usó revisión offline."}]
                }
            # Cualquier otro error → offline con nota
            return _offline_review(obj) | {
                "observaciones": [{"campo":"general","tipo":"riesgo",
                    "detalle":f"DeepSeek no disponible: {msg}. Se usó revisión offline."}]
            }
    # Sin cliente → offline
    return _offline_review(obj)
