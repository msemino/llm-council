"""
Configuration module for the LLM Council application.

Centralizes all environment variables, default model selections, and
application-wide constants. Values are loaded from a `.env` file at the
project root via ``python-dotenv``.

Módulo de configuración para la aplicación LLM Council.

Centraliza todas las variables de entorno, selecciones de modelos por defecto
y constantes globales de la aplicación. Los valores se cargan desde un archivo
``.env`` en la raíz del proyecto mediante ``python-dotenv``.

Environment Variables:
    OPENROUTER_API_KEY: Bearer token for authenticating with the OpenRouter API.
                        Obtain a free key at https://openrouter.ai/keys

Constants:
    COUNCIL_MODELS: Default list of models that participate in Stages 1 & 2.
    CHAIRMAN_MODEL: Default model used in Stage 3 to synthesize the verdict.
    OPENROUTER_API_URL: Base URL for the OpenRouter chat completions endpoint.
    DATA_DIR: Filesystem path where conversation JSON files are persisted.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

# ---------------------------------------------------------------------------
# Default Council Members
# These models compete in Stages 1 (responses) and 2 (cross-evaluation).
# Users can override this selection dynamically via the frontend UI.
# ---------------------------------------------------------------------------
COUNCIL_MODELS: list[str] = [
    "deepseek/deepseek-r1-0528:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-3-27b-it:free",
    "qwen/qwen3-235b-a22b-thinking-2507",
]

# ---------------------------------------------------------------------------
# Chairman Model (Stage 3 — Final Verdict)
# Reads all Stage 1 responses + Stage 2 evaluations and synthesizes a concise
# final answer. Can be overridden per-request from the frontend.
# ---------------------------------------------------------------------------
CHAIRMAN_MODEL: str = "deepseek/deepseek-r1-0528:free"

# ---------------------------------------------------------------------------
# API & Storage
# ---------------------------------------------------------------------------
OPENROUTER_API_URL: str = "https://openrouter.ai/api/v1/chat/completions"
DATA_DIR: str = "data/conversations"
