import os
import json
import requests
from typing import List, Dict, Any, Optional

# --- Configuración por entorno ---
AI_VENDOR = os.getenv("AI_VENDOR", "openai").lower().strip()

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # o el que tengas disponible
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com").rstrip("/")

# DeepSeek
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL   = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")

# Modo “sin red” para desarrollo local
AI_FORCE_OFFLINE = os.getenv("AI_FORCE_OFFLINE", "0") == "1"

# Timeouts y opciones comunes
DEFAULT_TIMEOUT = float(os.getenv("AI_HTTP_TIMEOUT", "60"))  # segundos
DEFAULT_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.2"))

# Endpoints
OPENAI_CHAT_URL   = f"{OPENAI_BASE_URL}/v1/chat/completions"
DEEPSEEK_CHAT_URL = f"{DEEPSEEK_BASE_URL}/chat/completions"


class AIClientError(RuntimeError):
    pass


def _http_post(url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
    """Wrapper HTTP con manejo de errores."""
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as e:
        raise AIClientError(f"Error de red al llamar {url}: {e}") from e

    # 200–299 OK
    if 200 <= resp.status_code < 300:
        try:
            return resp.json()
        except Exception:
            raise AIClientError("La API devolvió un cuerpo no-JSON")
    else:
        # Pasar texto para diagnóstico
        raise AIClientError(f"HTTP {resp.status_code}: {resp.text[:600]}")


def _chat_openai(messages: List[Dict[str, str]], json_mode: bool) -> str:
    if not OPENAI_API_KEY:
        raise AIClientError("Falta OPENAI_API_KEY")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload: Dict[str, Any] = {
        "model": OPENAI_MODEL,
        "messages": messages,
        "temperature": DEFAULT_TEMPERATURE,
    }

    # OpenAI soporta response_format={"type":"json_object"} para pedir JSON estricto
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    data = _http_post(OPENAI_CHAT_URL, headers, payload)
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise AIClientError("Respuesta inesperada de OpenAI (sin content)")


def _chat_deepseek(messages: List[Dict[str, str]], json_mode: bool) -> str:
    if not DEEPSEEK_API_KEY:
        raise AIClientError("Falta DEEPSEEK_API_KEY")

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    payload: Dict[str, Any] = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": DEFAULT_TEMPERATURE,
    }

    # DeepSeek (chat.completions) no siempre respeta response_format.
    # Aun así, si pides json_mode=True igual conviene pedirlo en el prompt (hazlo en tu mensaje system).
    if json_mode:
        # Algunos backends ignoran esto; no pasa nada por incluirlo.
        payload["response_format"] = {"type": "json_object"}

    data = _http_post(DEEPSEEK_CHAT_URL, headers, payload)
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise AIClientError("Respuesta inesperada de DeepSeek (sin content)")


def _offline_stub(messages: List[Dict[str, str]]) -> str:
    """
    Respuesta local para desarrollo. Devuelve un JSON “dummy” coherente con tu contrato.
    """
    return json.dumps({
        "observaciones": [
            {"campo": "general", "tipo": "faltante", "detalle": "Modo offline activo (AI_FORCE_OFFLINE=1)."}
        ],
        "correcciones_sugeridas": [
            {"campo": "general", "sugerencia": "Desactiva AI_FORCE_OFFLINE para llamar a la API real."}
        ],
        "resumen_propuesta": "No se consultó a ningún modelo; respuesta simulada localmente."
    }, ensure_ascii=False)


def chat(messages: List[Dict[str, str]], json_mode: bool = False) -> str:
    """
    Llama al proveedor configurado (OpenAI o DeepSeek) y retorna el 'content' como string.
    Si AI_FORCE_OFFLINE=1, devuelve un JSON 'dummy'.
    """
    if AI_FORCE_OFFLINE:
        return _offline_stub(messages)

    vendor = AI_VENDOR
    if vendor == "openai":
        return _chat_openai(messages, json_mode=json_mode)
    elif vendor == "deepseek":
        return _chat_deepseek(messages, json_mode=json_mode)
    else:
        # Fallback sensato: intenta OpenAI si hay key, si no DeepSeek, si no offline.
        if OPENAI_API_KEY:
            return _chat_openai(messages, json_mode=json_mode)
        if DEEPSEEK_API_KEY:
            return _chat_deepseek(messages, json_mode=json_mode)
        return _offline_stub(messages)