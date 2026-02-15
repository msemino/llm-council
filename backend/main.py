"""
FastAPI REST + SSE backend for the LLM Council application.

Exposes a RESTful API for conversation management and a Server-Sent Events
(SSE) streaming endpoint that pushes real-time progress updates to the
frontend as each of the three council stages executes.

Backend REST + SSE de FastAPI para la aplicación LLM Council.

Expone una API REST para gestión de conversaciones y un endpoint de
streaming SSE que envía actualizaciones de progreso en tiempo real al
frontend a medida que se ejecuta cada una de las tres etapas del consejo.

API Endpoints:
    GET  /                                        → Health check.
    GET  /api/models/free                         → List free OpenRouter models (10-min cache).
    GET  /api/conversations                       → List all conversations (metadata).
    POST /api/conversations                       → Create a new conversation.
    GET  /api/conversations/{id}                  → Get full conversation with messages.
    POST /api/conversations/{id}/message          → Synchronous 3-stage council execution.
    POST /api/conversations/{id}/message/stream   → SSE streaming of 3-stage council.

SSE Event Types (streamed to frontend):
    stage1_start, stage1_retry, stage1_complete,
    stage2_start, stage2_complete,
    stage3_start, stage3_retry, stage3_complete,
    title_complete, complete, error.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import json
import asyncio
import time

from . import storage
from .council import (
    run_full_council,
    generate_conversation_title,
    stage1_collect_responses,
    stage2_collect_rankings,
    stage3_synthesize_final,
    calculate_aggregate_rankings,
)
from .openrouter import fetch_free_models

app = FastAPI(
    title="LLM Council API",
    description="Battle arena backend for multi-model LLM evaluation.",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS — allow the Vite dev server and common local ports
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory cache for the free-models catalogue (refreshed every 10 min)
# ---------------------------------------------------------------------------
_free_models_cache: Optional[List[Dict[str, Any]]] = None
_free_models_cache_time: float = 0
FREE_MODELS_CACHE_TTL: int = 600  # seconds


# ---------------------------------------------------------------------------
# Pydantic request / response schemas
# ---------------------------------------------------------------------------
class CreateConversationRequest(BaseModel):
    """Empty body — conversations are created with a server-generated UUID."""
    pass


class SendMessageRequest(BaseModel):
    """
    Payload for sending a user message and triggering the council pipeline.

    Attributes:
        content: The user's question or prompt text.
        council_models: Optional override for which models compete in Stages 1 & 2.
        chairman_model: Optional override for the Stage 3 chairman model.
    """
    content: str
    council_models: Optional[List[str]] = None
    chairman_model: Optional[str] = None


class ConversationMetadata(BaseModel):
    """Lightweight conversation summary for the sidebar list."""
    id: str
    created_at: str
    title: str
    message_count: int


class Conversation(BaseModel):
    """Full conversation payload including all messages and stage data."""
    id: str
    created_at: str
    title: str
    messages: List[Dict[str, Any]]


@app.get("/")
async def root():
    """Health-check endpoint. Returns service name and ``"ok"`` status."""
    return {"status": "ok", "service": "LLM Council API"}


@app.get("/api/models/free")
async def list_free_models():
    """Return the catalogue of free OpenRouter models (TTL-cached 10 min)."""
    global _free_models_cache, _free_models_cache_time

    now = time.time()
    if _free_models_cache is not None and (now - _free_models_cache_time) < FREE_MODELS_CACHE_TTL:
        return _free_models_cache

    models = await fetch_free_models()
    _free_models_cache = models
    _free_models_cache_time = now
    return models


@app.get("/api/conversations", response_model=List[ConversationMetadata])
async def list_conversations():
    """List all conversations (metadata only)."""
    return storage.list_conversations()


@app.post("/api/conversations", response_model=Conversation)
async def create_conversation(request: CreateConversationRequest):
    """Create a new conversation."""
    conversation_id = str(uuid.uuid4())
    conversation = storage.create_conversation(conversation_id)
    return conversation


@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation with all its messages."""
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.post("/api/conversations/{conversation_id}/message")
async def send_message(conversation_id: str, request: SendMessageRequest):
    """
    Synchronous endpoint: run the full 3-stage council and return results.

    Useful for programmatic access; the frontend typically uses the
    ``/stream`` variant below for real-time progress.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    # Add user message
    storage.add_user_message(conversation_id, request.content)

    # If this is the first message, generate a title
    if is_first_message:
        title = await generate_conversation_title(request.content)
        storage.update_conversation_title(conversation_id, title)

    # Run the 3-stage council process
    stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
        request.content,
        council_models=request.council_models,
        chairman_model=request.chairman_model,
    )

    # Add assistant message with all stages
    storage.add_assistant_message(
        conversation_id,
        stage1_results,
        stage2_results,
        stage3_result
    )

    # Return the complete response with metadata
    return {
        "stage1": stage1_results,
        "stage2": stage2_results,
        "stage3": stage3_result,
        "metadata": metadata
    }


@app.post("/api/conversations/{conversation_id}/message/stream")
async def send_message_stream(conversation_id: str, request: SendMessageRequest):
    """
    SSE streaming endpoint for the 3-stage council pipeline.

    Emits ``text/event-stream`` events as each stage starts, retries, and
    completes.  The frontend consumes these events to progressively render
    the battle arena UI in real time.

    Event flow: ``stage1_start → [stage1_retry …] → stage1_complete →
    stage2_start → stage2_complete → stage3_start → [stage3_retry …] →
    stage3_complete → title_complete → complete``.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    async def event_generator():
        try:
            # Add user message
            storage.add_user_message(conversation_id, request.content)

            # Start title generation in parallel (don't await yet)
            title_task = None
            if is_first_message:
                title_task = asyncio.create_task(generate_conversation_title(request.content))

            # Stage 1: Collect responses (with retry/fallback for minimum responses)
            yield f"data: {json.dumps({'type': 'stage1_start'})}\n\n"

            # Progress callback to stream retry events to frontend
            retry_events = []
            async def on_stage1_progress(event_type, data):
                retry_events.append((event_type, data))

            stage1_results = await stage1_collect_responses(
                request.content,
                models=request.council_models,
                on_progress=on_stage1_progress,
            )

            # Send any retry events that occurred
            for evt_type, evt_data in retry_events:
                yield f"data: {json.dumps({'type': evt_type, 'data': evt_data})}\n\n"

            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"

            # Stage 2: Collect rankings
            yield f"data: {json.dumps({'type': 'stage2_start'})}\n\n"
            stage2_results, label_to_model = await stage2_collect_rankings(request.content, stage1_results, models=request.council_models)
            aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)
            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_results, 'metadata': {'label_to_model': label_to_model, 'aggregate_rankings': aggregate_rankings}})}\n\n"

            # Stage 3: Synthesize final answer (with retry/fallback)
            yield f"data: {json.dumps({'type': 'stage3_start'})}\n\n"

            # Progress callback to stream stage3 retry events to frontend
            stage3_retry_events = []
            async def on_stage3_progress(event_type, data):
                stage3_retry_events.append((event_type, data))

            stage3_result = await stage3_synthesize_final(
                request.content, stage1_results, stage2_results,
                chairman_model=request.chairman_model,
                on_progress=on_stage3_progress,
            )

            # Send any stage3 retry events that occurred
            for evt_type, evt_data in stage3_retry_events:
                yield f"data: {json.dumps({'type': evt_type, 'data': evt_data})}\n\n"

            yield f"data: {json.dumps({'type': 'stage3_complete', 'data': stage3_result})}\n\n"

            # Wait for title generation if it was started
            if title_task:
                title = await title_task
                storage.update_conversation_title(conversation_id, title)
                yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

            # Save complete assistant message
            storage.add_assistant_message(
                conversation_id,
                stage1_results,
                stage2_results,
                stage3_result
            )

            # Send completion event
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            # Send error event
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
