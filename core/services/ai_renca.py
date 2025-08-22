# core/services/ai_renca.py
import os, json, requests

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")  # ajusta si usas otro

PROMPT_SISTEMA = (
    "Eres un revisor experto en bases técnicas y normativas de licitaciones públicas en Chile. "
    "Revisa la información estructurada de una solicitud y devuelve: "
    "1) observaciones (campo, tipo: 'riesgo'|'formato'|'coherencia'|'faltante', detalle), "
    "2) correcciones_sugeridas (campo, sugerencia), "
    "3) resumen_propuesta (máx. 3 líneas)."
)

def _fallback_result(msg):
    return {
        "observaciones": [{"campo":"general","tipo":"riesgo","detalle":msg}],
        "correcciones_sugeridas": [{"campo":"general","sugerencia":"Verificar clave y conectividad hacia api.deepseek.com"}],
        "resumen_propuesta": "Análisis no disponible por error de conexión."
    }

def analizar_renca(data: dict) -> dict:
    """
    data: diccionario armado en la vista con todos los campos RENCA.
    Devuelve un dict con las claves: observaciones, correcciones_sugeridas, resumen_propuesta.
    """
    try:
        if not DEEPSEEK_API_KEY:
            return _fallback_result("Falta DEEPSEEK_API_KEY en variables de entorno.")

        messages = [
            {"role": "system", "content": PROMPT_SISTEMA},
            {"role": "user", "content": "Analiza la siguiente solicitud:\n" + json.dumps(data, ensure_ascii=False)}
        ]
        resp = requests.post(
            DEEPSEEK_URL,
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            json={"model": MODEL, "messages": messages, "temperature": 0.2},
            timeout=60
        )
        if resp.status_code != 200:
            return _fallback_result(f"No se pudo llamar a DeepSeek: HTTP {resp.status_code} - {resp.text}")

        content = resp.json()["choices"][0]["message"]["content"]
        # Intentamos parsear JSON; si no, devolvemos texto empaquetado
        try:
            result = json.loads(content)
            # chequeo mínimo
            if not isinstance(result, dict) or "observaciones" not in result:
                raise ValueError("Respuesta no JSON estándar.")
            return result
        except Exception:
            return {"observaciones": [], "correcciones_sugeridas": [], "resumen_propuesta": content.strip()[:1000]}
    except Exception as e:
        return _fallback_result(str(e))
