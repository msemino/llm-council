"""OpenRouter API client for making LLM requests."""

import httpx
from typing import List, Dict, Any, Optional
from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via OpenRouter API.

    Args:
        model: OpenRouter model identifier (e.g., "openai/gpt-4o")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content' and optional 'reasoning_details', or None if failed
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
            message = data['choices'][0]['message']

            return {
                'content': message.get('content'),
                'reasoning_details': message.get('reasoning_details')
            }

    except Exception as e:
        print(f"Error querying model {model}: {e}")
        return None


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]]
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models in parallel.

    Args:
        models: List of OpenRouter model identifiers
        messages: List of message dicts to send to each model

    Returns:
        Dict mapping model identifier to response dict (or None if failed)
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
    Fetch the list of free models from OpenRouter's /api/v1/models endpoint.

    Args:
        timeout: Request timeout in seconds

    Returns:
        List of dicts with 'id', 'name', 'context_length', and 'pricing' for each free model
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
