"""
OpenRouter API client for querying Large Language Models.

Provides an asynchronous HTTP client that communicates with the OpenRouter
unified API gateway (https://openrouter.ai). Supports single-model queries,
parallel multi-model queries, and free-model discovery.

Cliente API de OpenRouter para consultar modelos de lenguaje.

Proporciona un cliente HTTP asíncrono que se comunica con el gateway unificado
de OpenRouter. Soporta consultas a un solo modelo, consultas paralelas a
múltiples modelos y descubrimiento de modelos gratuitos.

Error Handling Strategy:
    Instead of returning ``None`` on failure, every function returns a dict
    with ``error``, ``error_type``, and ``content: None`` keys. This enables
    the frontend to display specific failure reasons (timeout, rate_limit,
    http_error, api_error, empty_response, unknown) per model.

Typical error_type values:
    - ``timeout``: Request exceeded the configured timeout.
    - ``rate_limit``: HTTP 429 — provider rate limit exceeded.
    - ``http_error``: Non-429 HTTP status error from the provider.
    - ``api_error``: Error embedded in the OpenRouter JSON response body.
    - ``empty_response``: API returned 200 but with no ``choices``.
    - ``unknown``: Unexpected exception.
"""

import httpx
from typing import List, Dict, Any, Optional
from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0,
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via the OpenRouter chat completions endpoint.

    Sends a list of chat messages to the specified model and returns the
    assistant's reply. On any failure (network, HTTP, API-level), returns
    a structured error dict rather than ``None`` so callers can distinguish
    failure modes.

    Consulta un solo modelo a través del endpoint de completions de OpenRouter.

    Args:
        model: OpenRouter model identifier (e.g., ``"deepseek/deepseek-r1-0528:free"``).
        messages: Conversation history as a list of ``{"role": ..., "content": ...}`` dicts.
        timeout: Maximum seconds to wait for a response (default 120s).

    Returns:
        On success: ``{"content": str, "reasoning_details": Optional[str]}``.
        On failure: ``{"error": str, "error_type": str, "content": None}``.
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()

            # Check for OpenRouter error in response body
            if 'error' in data:
                err_msg = data['error'].get('message', str(data['error']))
                err_code = data['error'].get('code', 0)
                print(f"[API Error] {model}: {err_msg} (code: {err_code})")
                error_type = 'rate_limit' if err_code == 429 else 'api_error'
                return {'error': err_msg, 'error_type': error_type, 'content': None}

            if not data.get('choices'):
                print(f"[Empty Response] {model}: no choices returned")
                return {'error': 'Empty response (no choices)', 'error_type': 'empty_response', 'content': None}

            message = data['choices'][0]['message']

            return {
                'content': message.get('content'),
                'reasoning_details': message.get('reasoning_details')
            }

    except httpx.TimeoutException:
        print(f"[Timeout] {model}: request timed out after {timeout}s")
        return {'error': f'Timeout ({timeout}s)', 'error_type': 'timeout', 'content': None}

    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        error_type = 'rate_limit' if status == 429 else 'http_error'
        body = ''
        try:
            body = e.response.json().get('error', {}).get('message', '')
        except Exception:
            body = e.response.text[:200]
        print(f"[HTTP {status}] {model}: {body}")
        return {'error': f'HTTP {status}: {body}', 'error_type': error_type, 'content': None}

    except Exception as e:
        print(f"[Error] {model}: {e}")
        return {'error': str(e), 'error_type': 'unknown', 'content': None}


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]],
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models concurrently using ``asyncio.gather``.

    Sends the same message history to every model in *models* simultaneously.
    Each model's response (or error dict) is collected and returned as a
    mapping keyed by model identifier.

    Consulta múltiples modelos en paralelo usando ``asyncio.gather``.

    Args:
        models: List of OpenRouter model identifiers to query in parallel.
        messages: Chat message history sent identically to every model.

    Returns:
        Dict mapping each model identifier to its response dict (success or
        error). Iteration order matches *models*.
    """
    import asyncio

    # Create tasks for all models
    tasks = [query_model(model, messages) for model in models]

    # Wait for all to complete
    responses = await asyncio.gather(*tasks)

    # Map models to their responses
    return {model: response for model, response in zip(models, responses)}


async def fetch_free_models(timeout: float = 30.0) -> List[Dict[str, Any]]:
    """
    Discover all zero-cost models available on OpenRouter.

    Queries the ``/api/v1/models`` catalogue and filters for models where
    both prompt and completion pricing are exactly ``0``. Results are sorted
    alphabetically by display name and cached by the caller (see ``main.py``).

    Descubre todos los modelos de costo cero disponibles en OpenRouter.

    Args:
        timeout: Maximum seconds to wait for the catalogue response.

    Returns:
        Sorted list of dicts, each containing:
        ``{"id": str, "name": str, "context_length": int, "pricing": dict}``.
        Returns an empty list on any network or parsing error.
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

            free_models = []
            for model in data.get("data", []):
                pricing = model.get("pricing", {})
                prompt_price = pricing.get("prompt", "1")
                completion_price = pricing.get("completion", "1")

                # Check if both prompt and completion pricing are zero (free)
                try:
                    is_free = float(prompt_price) == 0 and float(completion_price) == 0
                except (ValueError, TypeError):
                    is_free = False

                if is_free:
                    free_models.append({
                        "id": model.get("id", ""),
                        "name": model.get("name", ""),
                        "context_length": model.get("context_length"),
                        "pricing": pricing,
                    })

            # Sort alphabetically by name
            free_models.sort(key=lambda m: m["name"].lower())
            return free_models

    except Exception as e:
        print(f"Error fetching free models: {e}")
        return []
