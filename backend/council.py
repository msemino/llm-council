"""3-stage LLM Council orchestration."""

from typing import List, Dict, Any, Tuple, Optional, Callable
from .openrouter import query_models_parallel, query_model, fetch_free_models
from .config import COUNCIL_MODELS, CHAIRMAN_MODEL

# Minimum number of successful responses required for a meaningful battle
MIN_RESPONSES = 2
# Max retry rounds before giving up
MAX_RETRY_ROUNDS = 2

# Reliable backup models to try when primary models fail
BACKUP_MODELS = [
    "google/gemma-3-12b-it:free",
    "google/gemma-3-4b-it:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "microsoft/phi-4-reasoning-plus:free",
    "nvidia/llama-3.1-nemotron-70b-instruct:free",
    "deepseek/deepseek-r1-0528:free",
    "qwen/qwen3-235b-a22b-thinking-2507",
]


async def stage1_collect_responses(
    user_query: str,
    models: Optional[List[str]] = None,
    on_progress: Optional[Callable] = None,
) -> List[Dict[str, Any]]:
    """
    Stage 1: Collect individual responses from all council models.
    Includes retry and fallback mechanism to ensure at least MIN_RESPONSES models respond.

    Args:
        user_query: The user's question
        models: Optional list of model identifiers to use instead of config defaults
        on_progress: Optional async callback for progress events (type, data)

    Returns:
        List of dicts with 'model' and 'response' keys
    """
    active_models = models if models is not None else COUNCIL_MODELS
    system_msg = {"role": "system", "content": "IMPORTANTE: Siempre responde en español. Toda tu respuesta debe estar completamente en idioma español sin excepción. No uses otros idiomas."}
    messages = [system_msg, {"role": "user", "content": user_query}]

    # Query all models in parallel
    responses = await query_models_parallel(active_models, messages)

    # Format results
    stage1_results = []
    succeeded_models = set()
    failed_models = []
    failed_details = {}  # model -> error info
    for model, response in responses.items():
        if response is not None and response.get('content'):
            stage1_results.append({
                "model": model,
                "response": response.get('content', '')
            })
            succeeded_models.add(model)
        else:
            failed_models.append(model)
            if response and response.get('error'):
                failed_details[model] = {
                    'error': response['error'],
                    'error_type': response.get('error_type', 'unknown')
                }
            else:
                failed_details[model] = {
                    'error': 'No response received',
                    'error_type': 'no_response'
                }

    # --- RETRY & FALLBACK MECHANISM ---
    retry_round = 0
    while len(stage1_results) < MIN_RESPONSES and retry_round < MAX_RETRY_ROUNDS:
        retry_round += 1
        need = MIN_RESPONSES - len(stage1_results)

        if on_progress:
            await on_progress("stage1_retry", {
                "round": retry_round,
                "successful": len(stage1_results),
                "needed": need,
                "retrying": failed_models[:need] if failed_models else [],
                "failures": failed_details,
            })

        # Round 1: retry the failed models once
        if retry_round == 1 and failed_models:
            retry_targets = failed_models[:need + 1]  # try a couple extra
            print(f"[Retry round {retry_round}] Retrying {len(retry_targets)} failed models: {retry_targets}")
            retry_responses = await query_models_parallel(retry_targets, messages)
            for model, response in retry_responses.items():
                if response is not None and response.get('content') and model not in succeeded_models:
                    stage1_results.append({
                        "model": model,
                        "response": response.get('content', '')
                    })
                    succeeded_models.add(model)
            # Update failed models list
            failed_models = [m for m in failed_models if m not in succeeded_models]

        # Round 2: bring in backup models
        if len(stage1_results) < MIN_RESPONSES and retry_round >= 1:
            # Pick backup models not already tried
            all_tried = succeeded_models | set(active_models)
            candidates = [m for m in BACKUP_MODELS if m not in all_tried]

            if not candidates:
                # If all backups already tried, break out
                break

            need = MIN_RESPONSES - len(stage1_results)
            backup_targets = candidates[:need + 2]  # try extras for safety
            print(f"[Retry round {retry_round}] Trying {len(backup_targets)} backup models: {backup_targets}")

            if on_progress:
                await on_progress("stage1_retry", {
                    "round": retry_round,
                    "successful": len(stage1_results),
                    "needed": need,
                    "retrying": backup_targets,
                    "backup": True,
                })

            backup_responses = await query_models_parallel(backup_targets, messages)
            for model, response in backup_responses.items():
                if response is not None and response.get('content') and model not in succeeded_models:
                    stage1_results.append({
                        "model": model,
                        "response": response.get('content', '')
                    })
                    succeeded_models.add(model)
            all_tried.update(backup_targets)

    if len(stage1_results) < MIN_RESPONSES:
        print(f"[WARNING] Only got {len(stage1_results)} responses after {retry_round} retry rounds")

    # Attach failure details to results for frontend display
    for r in stage1_results:
        r.setdefault('status', 'success')

    # Add failed models as entries so frontend knows what failed
    for model in failed_models:
        detail = failed_details.get(model, {})
        stage1_results.append({
            "model": model,
            "response": None,
            "status": "failed",
            "error": detail.get('error', 'Unknown error'),
            "error_type": detail.get('error_type', 'unknown'),
        })

    return stage1_results


async def stage2_collect_rankings(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    models: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Stage 2: Each model ranks the anonymized responses.

    Args:
        user_query: The original user query
        stage1_results: Results from Stage 1 (may include failed entries)
        models: Optional list of model identifiers to use instead of config defaults

    Returns:
        Tuple of (rankings list, label_to_model mapping)
    """
    active_models = models if models is not None else COUNCIL_MODELS

    # Filter out failed entries - only use successful responses for ranking
    successful_results = [r for r in stage1_results if r.get('status') != 'failed' and r.get('response')]

    # Create anonymized labels for responses (Response A, Response B, etc.)
    labels = [chr(65 + i) for i in range(len(successful_results))]  # A, B, C, ...

    # Create mapping from label to model name
    label_to_model = {
        f"Response {label}": result['model']
        for label, result in zip(labels, successful_results)
    }

    # Build the ranking prompt
    responses_text = "\n\n".join([
        f"Response {label}:\n{result['response']}"
        for label, result in zip(labels, successful_results)
    ])

    ranking_prompt = f"""Estás evaluando diferentes respuestas a la siguiente pregunta:

Pregunta: {user_query}

Aquí están las respuestas de diferentes modelos (anonimizadas):

{responses_text}

Tu tarea (RESPONDE TODO EN ESPAÑOL):
1. Primero, evalúa cada respuesta individualmente. Para cada una, explica qué hace bien y qué hace mal.
2. Luego, al final de tu respuesta, proporciona un ranking final.

IMPORTANTE: Tu ranking final DEBE estar formateado EXACTAMENTE así:
- Comienza con la línea "FINAL RANKING:" (todo en mayúsculas, con dos puntos)
- Luego lista las respuestas de mejor a peor como lista numerada
- Cada línea debe ser: número, punto, espacio, y SOLO la etiqueta de respuesta (ej: "1. Response A")
- No agregues ningún otro texto o explicación en la sección del ranking

Ejemplo del formato correcto para tu respuesta COMPLETA:

Response A proporciona buen detalle sobre X pero falla en Y...
Response B es precisa pero le falta profundidad en Z...
Response C ofrece la respuesta más completa...

FINAL RANKING:
1. Response C
2. Response A
3. Response B

Ahora proporciona tu evaluación y ranking (EN ESPAÑOL):"""

    messages = [{"role": "system", "content": "IMPORTANTE: Responde siempre en español. Toda tu evaluación debe estar en español."}, {"role": "user", "content": ranking_prompt}]

    # Get rankings from all council models in parallel
    responses = await query_models_parallel(active_models, messages)

    # Format results
    stage2_results = []
    for model, response in responses.items():
        if response is not None and response.get('content'):
            full_text = response.get('content', '')
            parsed = parse_ranking_from_text(full_text)
            stage2_results.append({
                "model": model,
                "ranking": full_text,
                "parsed_ranking": parsed
            })

    return stage2_results, label_to_model


async def stage3_synthesize_final(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    chairman_model: Optional[str] = None,
    on_progress: Optional[Callable] = None,
) -> Dict[str, Any]:
    """
    Stage 3: Chairman synthesizes final response.
    Includes retry with the same model + fallback to backup models if chairman fails.

    Args:
        user_query: The original user query
        stage1_results: Individual model responses from Stage 1 (may include failed entries)
        stage2_results: Rankings from Stage 2
        chairman_model: Optional model identifier to use instead of config default
        on_progress: Optional async callback for progress events

    Returns:
        Dict with 'model', 'response' keys, and optionally 'status', 'error', 'error_type', 'attempts'
    """
    active_chairman = chairman_model if chairman_model is not None else CHAIRMAN_MODEL

    # Filter out failed entries - only use successful responses for synthesis
    successful_results = [r for r in stage1_results if r.get('status') != 'failed' and r.get('response')]

    # Build comprehensive context for chairman
    stage1_text = "\n\n".join([
        f"Model: {result['model']}\nResponse: {result['response']}"
        for result in successful_results
    ])

    stage2_text = "\n\n".join([
        f"Model: {result['model']}\nRanking: {result['ranking']}"
        for result in stage2_results
    ])

    chairman_prompt = f"""Eres el Presidente del Consejo de LLMs. Varios modelos respondieron a la pregunta de un usuario y luego evaluaron las respuestas entre sí.

Pregunta Original: {user_query}

ETAPA 1 - Respuestas Individuales:
{stage1_text}

ETAPA 2 - Rankings de Pares:
{stage2_text}

INSTRUCCIONES ESTRICTAS:
- Tu respuesta DEBE ser CORTA y CONCISA: máximo 3-4 párrafos.
- Ve directo al punto. No repitas ni resumas cada respuesta individual.
- No incluyas análisis extensos de cada modelo ni de los rankings.
- Sintetiza la mejor respuesta posible a la pregunta original, tomando lo mejor de las respuestas mejor rankeadas.
- Escribe como si respondieras directamente al usuario, no como un informe académico.
- RESPONDE COMPLETAMENTE EN ESPAÑOL."""

    messages = [{"role": "system", "content": "IMPORTANTE: Responde siempre en español. Sé breve y directo. Máximo 3-4 párrafos."}, {"role": "user", "content": chairman_prompt}]

    # --- CHAIRMAN RETRY & FALLBACK ---
    attempts = []

    # Attempt 1: Try the selected chairman model
    print(f"[Chairman] Attempting with primary: {active_chairman}")
    response = await query_model(active_chairman, messages)

    if response and response.get('content'):
        return {
            "model": active_chairman,
            "response": response.get('content', ''),
            "status": "success",
            "attempts": [{"model": active_chairman, "status": "success"}],
        }

    # Record failure
    error_info = {
        "model": active_chairman,
        "status": "failed",
        "error": response.get('error', 'Unknown error') if response else 'No response',
        "error_type": response.get('error_type', 'unknown') if response else 'no_response',
    }
    attempts.append(error_info)
    print(f"[Chairman] Primary failed: {error_info['error']} ({error_info['error_type']})")

    if on_progress:
        await on_progress("stage3_retry", {
            "attempt": 1,
            "failed_model": active_chairman,
            "error": error_info['error'],
            "error_type": error_info['error_type'],
        })

    # Attempt 2: Retry the same chairman once more
    print(f"[Chairman] Retry attempt with: {active_chairman}")
    response = await query_model(active_chairman, messages)

    if response and response.get('content'):
        attempts.append({"model": active_chairman, "status": "success"})
        return {
            "model": active_chairman,
            "response": response.get('content', ''),
            "status": "success",
            "attempts": attempts,
        }

    # Record second failure
    error_info2 = {
        "model": active_chairman,
        "status": "failed",
        "error": response.get('error', 'Unknown error') if response else 'No response',
        "error_type": response.get('error_type', 'unknown') if response else 'no_response',
    }
    attempts.append(error_info2)
    print(f"[Chairman] Retry failed: {error_info2['error']}")

    if on_progress:
        await on_progress("stage3_retry", {
            "attempt": 2,
            "failed_model": active_chairman,
            "error": error_info2['error'],
            "error_type": error_info2['error_type'],
            "trying_backup": True,
        })

    # Attempt 3+: Try backup models
    tried = {active_chairman}
    for backup_model in BACKUP_MODELS:
        if backup_model in tried:
            continue
        tried.add(backup_model)

        print(f"[Chairman] Trying backup: {backup_model}")
        if on_progress:
            await on_progress("stage3_retry", {
                "attempt": len(attempts) + 1,
                "backup_model": backup_model,
                "trying_backup": True,
            })

        response = await query_model(backup_model, messages)

        if response and response.get('content'):
            attempts.append({"model": backup_model, "status": "success"})
            return {
                "model": backup_model,
                "response": response.get('content', ''),
                "status": "success",
                "original_chairman": active_chairman,
                "attempts": attempts,
            }

        # Record backup failure
        backup_error = {
            "model": backup_model,
            "status": "failed",
            "error": response.get('error', 'Unknown error') if response else 'No response',
            "error_type": response.get('error_type', 'unknown') if response else 'no_response',
        }
        attempts.append(backup_error)
        print(f"[Chairman] Backup {backup_model} failed: {backup_error['error']}")

    # All attempts failed
    last_error = attempts[-1] if attempts else {"error": "All models failed", "error_type": "all_failed"}
    return {
        "model": active_chairman,
        "response": None,
        "status": "failed",
        "error": last_error.get('error', 'All chairman models failed'),
        "error_type": last_error.get('error_type', 'all_failed'),
        "attempts": attempts,
    }


def parse_ranking_from_text(ranking_text: str) -> List[str]:
    """
    Parse the FINAL RANKING section from the model's response.

    Args:
        ranking_text: The full text response from the model

    Returns:
        List of response labels in ranked order
    """
    import re

    # Look for "FINAL RANKING:" section
    if "FINAL RANKING:" in ranking_text:
        # Extract everything after "FINAL RANKING:"
        parts = ranking_text.split("FINAL RANKING:")
        if len(parts) >= 2:
            ranking_section = parts[1]
            # Try to extract numbered list format (e.g., "1. Response A")
            # This pattern looks for: number, period, optional space, "Response X"
            numbered_matches = re.findall(r'\d+\.\s*Response [A-Z]', ranking_section)
            if numbered_matches:
                # Extract just the "Response X" part
                return [re.search(r'Response [A-Z]', m).group() for m in numbered_matches]

            # Fallback: Extract all "Response X" patterns in order
            matches = re.findall(r'Response [A-Z]', ranking_section)
            return matches

    # Fallback: try to find any "Response X" patterns in order
    matches = re.findall(r'Response [A-Z]', ranking_text)
    return matches


def calculate_aggregate_rankings(
    stage2_results: List[Dict[str, Any]],
    label_to_model: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Calculate aggregate rankings across all models.

    Args:
        stage2_results: Rankings from each model
        label_to_model: Mapping from anonymous labels to model names

    Returns:
        List of dicts with model name and average rank, sorted best to worst
    """
    from collections import defaultdict

    # Track positions for each model
    model_positions = defaultdict(list)

    for ranking in stage2_results:
        ranking_text = ranking['ranking']

        # Parse the ranking from the structured format
        parsed_ranking = parse_ranking_from_text(ranking_text)

        for position, label in enumerate(parsed_ranking, start=1):
            if label in label_to_model:
                model_name = label_to_model[label]
                model_positions[model_name].append(position)

    # Calculate average position for each model
    aggregate = []
    for model, positions in model_positions.items():
        if positions:
            avg_rank = sum(positions) / len(positions)
            aggregate.append({
                "model": model,
                "average_rank": round(avg_rank, 2),
                "rankings_count": len(positions)
            })

    # Sort by average rank (lower is better)
    aggregate.sort(key=lambda x: x['average_rank'])

    return aggregate


async def generate_conversation_title(user_query: str) -> str:
    """
    Generate a short title for a conversation based on the first user message.

    Args:
        user_query: The first user message

    Returns:
        A short title (3-5 words)
    """
    title_prompt = f"""Generate a very short title (3-5 words maximum) that summarizes the following question.
The title should be concise and descriptive. Do not use quotes or punctuation in the title.

Question: {user_query}

Title:"""

    messages = [{"role": "user", "content": title_prompt}]

    # Use gemini-2.5-flash for title generation (fast and cheap)
    response = await query_model("google/gemini-2.5-flash", messages, timeout=30.0)

    if response is None or not response.get('content'):
        # Fallback to a generic title
        return "New Conversation"

    title = response.get('content', 'New Conversation').strip()

    # Clean up the title - remove quotes, limit length
    title = title.strip('"\'')

    # Truncate if too long
    if len(title) > 50:
        title = title[:47] + "..."

    return title


async def run_full_council(
    user_query: str,
    council_models: Optional[List[str]] = None,
    chairman_model: Optional[str] = None,
) -> Tuple[List, List, Dict, Dict]:
    """
    Run the complete 3-stage council process.

    Args:
        user_query: The user's question
        council_models: Optional list of model identifiers for stages 1 & 2
        chairman_model: Optional model identifier for stage 3

    Returns:
        Tuple of (stage1_results, stage2_results, stage3_result, metadata)
    """
    # Stage 1: Collect individual responses
    stage1_results = await stage1_collect_responses(user_query, models=council_models)

    # Check if we have any successful responses
    successful_results = [r for r in stage1_results if r.get('status') != 'failed' and r.get('response')]
    if not successful_results:
        return stage1_results, [], {
            "model": "error",
            "response": None,
            "status": "failed",
            "error": "All models failed to respond. Please try again.",
            "error_type": "all_failed",
        }, {}

    # Stage 2: Collect rankings
    stage2_results, label_to_model = await stage2_collect_rankings(user_query, stage1_results, models=council_models)

    # Calculate aggregate rankings
    aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)

    # Stage 3: Synthesize final answer
    stage3_result = await stage3_synthesize_final(
        user_query,
        stage1_results,
        stage2_results,
        chairman_model=chairman_model,
    )

    # Prepare metadata
    metadata = {
        "label_to_model": label_to_model,
        "aggregate_rankings": aggregate_rankings
    }

    return stage1_results, stage2_results, stage3_result, metadata
