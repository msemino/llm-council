# LLM Council — Battle Arena for AI Models

> **Multi-model LLM evaluation platform** with a real-time battle arena UI, dynamic free-model selector, automatic retry/fallback, and full Spanish language support.

Custom fork of [Karpathy's llm-council](https://github.com/karpathy/llm-council) — rebuilt from scratch with a production-quality React frontend, FastAPI + SSE streaming backend, and resilient error handling.

---

## Table of Contents

- [Overview](#overview)
- [How It Works — The 3-Stage Pipeline](#how-it-works--the-3-stage-pipeline)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Error Handling & Resilience](#error-handling--resilience)
- [Credits](#credits)
- [Versión en Español](#versión-en-español)

---

## Overview

Instead of relying on a single LLM, this application sends your question to **multiple AI models simultaneously**, has them anonymously evaluate each other's responses, and a designated "chairman" model synthesizes the best final answer — all streamed in real time to a visually rich battle arena UI.

All models used are **100% free** via [OpenRouter](https://openrouter.ai/), requiring no paid API balance.

## How It Works — The 3-Stage Pipeline

### Stage 1 — Individual Responses

Your question is sent in parallel to 2–6 selected models. Responses are displayed side-by-side in color-coded panels with model-specific emojis and word counts. If fewer than 2 models respond successfully, the system **automatically retries** failed models and then tries backup models from a predefined fallback list.

### Stage 2 — Anonymous Cross-Evaluation

Each model receives the anonymized responses ("Response A", "Response B", …) and produces a structured ranking with justification. An **aggregated ranking** is calculated by averaging each model's position across all evaluators and displayed as a podium chart with medals.

### Stage 3 — Chairman's Verdict

A designated chairman model analyzes all responses and evaluations, then synthesizes a concise final answer (3–4 paragraphs). If the chairman fails, the system **retries once**, then tries every backup model sequentially until one succeeds.

## Key Features

| Feature | Description |
|---------|-------------|
| **Dynamic Model Selector** | Pick from 30+ free OpenRouter models via dropdown, configure 2–6 competitors |
| **Real-time SSE Streaming** | Server-Sent Events push each stage's progress to the UI as it happens |
| **Automatic Retry/Fallback** | Stage 1: retry failed + backup models. Stage 3: retry chairman + fallback chain |
| **Detailed Error Display** | Failed models show specific error types (timeout, rate_limit, http_error, etc.) |
| **Battle Arena UI** | Side-by-side panels, shimmer loading, podium ranking, live timer, progress steps |
| **Spanish Language** | Full Spanish UI and model responses (enforced via system prompts) |
| **Conversation Persistence** | JSON file-based storage — no database required |
| **Chairman Retry History** | UI shows every attempt made, which model succeeded, and which ones failed |

### Differences vs. Karpathy's Original

| Aspect | Original | This Fork |
|--------|----------|-----------|
| Model selection | Hardcoded in `config.py` | Dynamic UI with 30+ free models |
| Number of models | Fixed (4) | Configurable 2–6 from frontend |
| Chairman model | Fixed | Separately selectable |
| Retry mechanism | None | Full retry + backup fallback |
| Error visibility | Generic errors | Specific error types per model |
| Language | English | Full Spanish (UI + responses) |
| UI design | Basic tabs | Battle arena with panels, podium, timeline |
| Cost | Paid models | 100% free via OpenRouter |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   React Frontend                     │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Sidebar  │  │ChatInterface │  │ModelSelector  │  │
│  └──────────┘  │  ┌────────┐  │  └───────────────┘  │
│                │  │Process │  │                      │
│                │  │Timeline│  │    ← SSE Stream      │
│                │  └────────┘  │                      │
│                └──────────────┘                      │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP + SSE
┌──────────────────────┴──────────────────────────────┐
│                  FastAPI Backend                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ main.py  │→ │council.py│→ │  openrouter.py   │   │
│  │ (routes) │  │(pipeline)│  │  (API client)    │   │
│  └──────────┘  └──────────┘  └──────────────────┘   │
│       ↕                                              │
│  ┌──────────┐  ┌──────────┐                          │
│  │storage.py│  │ config.py│                          │
│  │  (JSON)  │  │ (env)    │                          │
│  └──────────┘  └──────────┘                          │
└──────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Python 3.10+, FastAPI, async httpx | REST API + SSE streaming |
| **Frontend** | React 18, Vite, react-markdown | SPA with real-time updates |
| **API Gateway** | OpenRouter | Unified access to 30+ LLM providers |
| **Storage** | JSON files | Zero-dependency conversation persistence |
| **Package Mgmt** | uv (Python), npm (JS) | Fast, reproducible installs |

## Getting Started

### Prerequisites

- **Python 3.10+** with [uv](https://docs.astral.sh/uv/) package manager
- **Node.js 18+** with npm
- **OpenRouter API key** — free at [openrouter.ai/keys](https://openrouter.ai/keys) (free models require no balance)

### Installation

```bash
# Clone the repository
git clone https://github.com/msemino/llm-council.git
cd llm-council

# Backend dependencies
uv sync

# Frontend dependencies
cd frontend && npm install && cd ..
```

### Configuration

Create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
```

### Running

**Quick start (Windows):**
```bash
start.bat
```

**Quick start (Linux/Mac):**
```bash
./start.sh
```

**Manual (two terminals):**

```bash
# Terminal 1 — Backend (port 8001)
uv run python -m backend.main

# Terminal 2 — Frontend (port 5173)
cd frontend && npm run dev
```

Open **http://localhost:5173** in your browser.

## Usage

1. Click **"+ Nueva Conversacion"** to create a new conversation
2. In the **"Configuracion de Batalla"** panel:
   - Select how many models will compete (2–6)
   - Choose specific models from the dropdown (30+ free options)
   - Select the chairman model for the final verdict
3. Type your question and press Enter
4. Watch the live battle unfold through all 3 rounds

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/api/models/free` | List free OpenRouter models (cached 10 min) |
| `GET` | `/api/conversations` | List all conversations (metadata) |
| `POST` | `/api/conversations` | Create a new conversation |
| `GET` | `/api/conversations/{id}` | Get full conversation with messages |
| `POST` | `/api/conversations/{id}/message` | Synchronous 3-stage execution |
| `POST` | `/api/conversations/{id}/message/stream` | **SSE streaming** 3-stage execution |

### SSE Event Types

```
stage1_start → [stage1_retry …] → stage1_complete →
stage2_start → stage2_complete →
stage3_start → [stage3_retry …] → stage3_complete →
title_complete → complete
```

## Project Structure

```
llm-council/
├── backend/
│   ├── __init__.py          # Package docstring
│   ├── config.py            # Environment variables + default model configuration
│   ├── openrouter.py        # Async OpenRouter API client (query, parallel, free models)
│   ├── council.py           # 3-stage pipeline orchestration + retry/fallback logic
│   ├── main.py              # FastAPI routes + SSE streaming endpoints
│   └── storage.py           # JSON file-based conversation persistence
├── frontend/
│   └── src/
│       ├── App.jsx           # Root component — global state + SSE event handling
│       ├── api.js            # HTTP + SSE client for backend communication
│       └── components/
│           ├── ModelSelector.jsx   # Dynamic model picker (2-6 models + chairman)
│           ├── ProcessTimeline.jsx # Battle arena visualization (panels, podium, chairman)
│           ├── ChatInterface.jsx   # Message thread + input form
│           ├── Sidebar.jsx         # Conversation list navigation
│           ├── Stage1.jsx          # Detailed Stage 1 view (collapsible)
│           └── Stage2.jsx          # Detailed Stage 2 view (collapsible)
├── data/conversations/       # Auto-created — JSON conversation files
├── .env                      # OpenRouter API key (not committed)
├── pyproject.toml            # Python dependencies (uv)
└── README.md                 # This file
```

## Error Handling & Resilience

The system is designed to handle the inherent unreliability of free-tier API models:

- **Stage 1 Retry**: If fewer than 2 models respond, the system retries failed models once, then tries backup models from a curated fallback list.
- **Stage 3 Chairman Fallback**: If the chairman model fails, retries once with the same model, then sequentially tries 7 backup models.
- **Structured Error Types**: Every failure returns a typed error (`timeout`, `rate_limit`, `http_error`, `api_error`, `empty_response`, `unknown`) displayed in the UI with specific icons and labels.
- **Attempt History**: The chairman's result includes a full `attempts` array showing every model tried and its outcome, visible in the UI.

## Credits

- **Original concept:** [Andrej Karpathy](https://github.com/karpathy/llm-council)
- **Fork with arena UI, dynamic selector, retry/fallback, and Spanish:** [Marcelo Semino](https://github.com/msemino)
- **Vibe coded with** Claude Code (Opus 4.6)

---

# Versión en Español

# LLM Council — Arena de Batalla de Modelos de IA

> **Plataforma de evaluación multi-modelo de LLMs** con UI de arena de batalla en tiempo real, selector dinámico de modelos gratuitos, retry/fallback automático, y soporte completo en español.

Fork personalizado del [llm-council de Karpathy](https://github.com/karpathy/llm-council) — reconstruido desde cero con un frontend React de calidad producción, backend FastAPI + streaming SSE, y manejo de errores resiliente.

---

## Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Cómo Funciona — Pipeline de 3 Etapas](#cómo-funciona--pipeline-de-3-etapas)
- [Características Principales](#características-principales)
- [Stack Tecnológico](#stack-tecnológico)
- [Instalación](#instalación)
- [Uso](#uso)
- [Manejo de Errores y Resiliencia](#manejo-de-errores-y-resiliencia)
- [Créditos](#créditos)

---

## Descripción General

En vez de depender de un solo LLM, esta aplicación envía tu pregunta a **múltiples modelos de IA simultáneamente**, los hace evaluarse entre sí de forma anónima, y un modelo "presidente" sintetiza la mejor respuesta final — todo transmitido en tiempo real a una UI de arena de batalla visualmente rica.

Todos los modelos son **100% gratuitos** vía [OpenRouter](https://openrouter.ai/), sin necesidad de saldo pagado.

## Cómo Funciona — Pipeline de 3 Etapas

### Etapa 1 — Respuestas Individuales

Tu pregunta se envía en paralelo a 2–6 modelos seleccionados. Las respuestas se muestran lado a lado en paneles con colores y emojis por modelo. Si menos de 2 modelos responden, el sistema **reintenta automáticamente** los modelos fallidos y luego prueba modelos de respaldo.

### Etapa 2 — Evaluación Cruzada Anónima

Cada modelo recibe las respuestas anonimizadas ("Response A", "Response B", …) y produce un ranking con justificación. Se calcula un **ranking agregado** y se muestra como un podio con medallas.

### Etapa 3 — Veredicto del Presidente

Un modelo presidente analiza todas las respuestas y evaluaciones, luego sintetiza una respuesta final concisa (3–4 párrafos). Si el presidente falla, el sistema **reintenta una vez** y luego prueba cada modelo de respaldo secuencialmente.

## Características Principales

| Característica | Descripción |
|----------------|-------------|
| **Selector Dinámico** | 30+ modelos gratuitos de OpenRouter, configurable 2–6 competidores |
| **Streaming SSE** | Server-Sent Events transmiten el progreso de cada etapa en tiempo real |
| **Retry/Fallback** | Etapa 1: reintenta fallidos + modelos de respaldo. Etapa 3: retry + cadena de fallback |
| **Errores Detallados** | Modelos fallidos muestran tipo específico (timeout, rate_limit, http_error, etc.) |
| **UI Arena de Batalla** | Paneles lado a lado, shimmer loading, podio, timer en vivo, pasos de progreso |
| **Español Completo** | UI y respuestas de modelos en español (forzado vía system prompts) |
| **Persistencia** | Almacenamiento basado en archivos JSON — sin base de datos externa |

## Stack Tecnológico

| Capa | Tecnología | Propósito |
|------|-----------|-----------|
| **Backend** | Python 3.10+, FastAPI, async httpx | API REST + streaming SSE |
| **Frontend** | React 18, Vite, react-markdown | SPA con actualizaciones en tiempo real |
| **Gateway API** | OpenRouter | Acceso unificado a 30+ proveedores de LLM |
| **Almacenamiento** | Archivos JSON | Persistencia sin dependencias externas |
| **Gestión Paquetes** | uv (Python), npm (JS) | Instalaciones rápidas y reproducibles |

## Instalación

### Requisitos

- **Python 3.10+** con [uv](https://docs.astral.sh/uv/)
- **Node.js 18+** con npm
- **API key de OpenRouter** — gratis en [openrouter.ai/keys](https://openrouter.ai/keys)

### Pasos

```bash
# Clonar el repositorio
git clone https://github.com/msemino/llm-council.git
cd llm-council

# Dependencias del backend
uv sync

# Dependencias del frontend
cd frontend && npm install && cd ..
```

### Configuración

Crear archivo `.env` en la raíz del proyecto:

```env
OPENROUTER_API_KEY=sk-or-v1-tu-api-key-aquí
```

### Ejecución

```bash
# Terminal 1 — Backend (puerto 8001)
uv run python -m backend.main

# Terminal 2 — Frontend (puerto 5173)
cd frontend && npm run dev
```

Abrir **http://localhost:5173** en el navegador.

## Uso

1. Click en **"+ Nueva Conversacion"**
2. En el panel **"Configuracion de Batalla"**:
   - Elegir cuántos modelos competirán (2–6)
   - Seleccionar cada modelo del dropdown (30+ opciones gratuitas)
   - Elegir el modelo presidente por separado
3. Escribir tu pregunta y presionar Enter
4. Ver la batalla en vivo con las 3 rondas

## Manejo de Errores y Resiliencia

El sistema está diseñado para manejar la inestabilidad inherente de las APIs de modelos gratuitos:

- **Retry en Etapa 1**: Si menos de 2 modelos responden, reintenta los fallidos una vez, luego prueba modelos de respaldo.
- **Fallback del Presidente**: Si el presidente falla, reintenta con el mismo modelo, luego prueba 7 modelos de respaldo secuencialmente.
- **Tipos de Error Estructurados**: Cada falla retorna un tipo (`timeout`, `rate_limit`, `http_error`, `api_error`, `empty_response`, `unknown`) con íconos y etiquetas específicos en la UI.
- **Historial de Intentos**: El resultado del presidente incluye un array `attempts` con cada modelo intentado y su resultado, visible en la UI.

## Créditos

- **Concepto original:** [Andrej Karpathy](https://github.com/karpathy/llm-council)
- **Fork con arena UI, selector dinámico, retry/fallback, y español:** [Marcelo Semino](https://github.com/msemino)
- **Vibe coded con** Claude Code (Opus 4.6)
