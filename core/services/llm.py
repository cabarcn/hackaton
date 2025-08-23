# core/services/llm.py
from __future__ import annotations
import os
from typing import List, Dict
from django.conf import settings
from openai import OpenAI, APIError, RateLimitError

# Lee la API key desde .env (OPENAI_API_KEY)
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError("Falta OPENAI_API_KEY en tu archivo .env")

# Modelo configurable: usa OPENAI_MODEL del .env o el settings.OPENAI_MODEL
MODEL = os.getenv("OPENAI_MODEL", getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"))

client = OpenAI(api_key=API_KEY)

def respond(prompt: str, *, max_output_tokens: int = 700, temperature: float = 0.2) -> str:
    """
    API recomendada: Responses. Retorna solo el texto.
    """
    try:
        r = client.responses.create(
            model=MODEL,
            input=prompt,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )
        return r.output_text
    except RateLimitError:
        return "Estoy recibiendo muchas solicitudes ahora mismo. Intenta nuevamente en unos segundos."
    except APIError as e:
        return f"Error del proveedor de IA: {e}"

def chat(messages: List[Dict[str, str]], *, max_tokens: int = 700, temperature: float = 0.2) -> str:
    """
    Alternativa de compatibilidad: Chat Completions (si ya usas mensajes).
    messages = [{"role":"system"/"user"/"assistant", "content":"..."}]
    """
    try:
        r = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return r.choices[0].message.content
    except RateLimitError:
        return "Estoy recibiendo muchas solicitudes ahora mismo. Intenta nuevamente en unos segundos."
    except APIError as e:
        return f"Error del proveedor de IA: {e}"
