# LLM Council - Battle Arena for AI Models

![llmcouncil](header.jpg)

> Custom fork of [Karpathy's llm-council](https://github.com/karpathy/llm-council) with a "battle arena" UI, dynamic free model selector, retry/fallback mechanism, and full Spanish language support.

## What is this?

Instead of asking a single LLM, this app sends your question to **multiple AI models simultaneously**, has them evaluate each other, and a designated "chairman" model synthesizes the best final answer.

### The 3 Rounds of Battle

1. **Round 1 - Individual Responses**: Your question is sent in parallel to all selected models. Responses are shown side-by-side in color-coded panels with model-specific emojis. Includes an **automatic retry mechanism** if fewer than 2 models respond (retries failed models + tries backup models).

2. **Round 2 - Cross Evaluations**: Each model evaluates the others' responses (anonymized as "Response A", "Response B", etc.) and generates a ranking. An **aggregated ranking** is calculated and displayed as a podium.

3. **Round 3 - Chairman's Verdict**: A designated chairman model analyzes all responses + evaluations and synthesizes a concise final answer (3-4 paragraphs max).

## Differences vs the Original

| Feature | Karpathy original | This fork |
|---------|------------------|-----------|
| Model selector | Hardcoded in config.py | **Dynamic UI** with 30+ free models |
| Number of models | Fixed (4) | **Configurable 2-6** from frontend |
| Chairman model | Fixed | **Selectable** separately |
| Chairman response | Long | **Short and concise** (3-4 paragraphs) |
| Language | English | **Full Spanish** (UI + model responses) |
| Retry/Fallback | No | **Yes** - retries failed + backup models |
| Model names | Hidden during loading | **Always visible** with emoji and color |
| UI | Basic tabs | **Battle arena** with side-by-side panels, podium, live timeline |
| Models | Paid (GPT-5, Claude, etc.) | **100% free** via OpenRouter |

## Screenshots

The UI features:
- Configuration panel with quantity selector (2-6) and dropdowns per model
- Live arena with "EN VIVO" (LIVE) badge during battle
- Side-by-side panels with shimmer loading and real model names
- Evaluation tabs per model with de-anonymization
- Podium with aggregated ranking and color bars
- Concise chairman verdict

## Setup

### 1. Requirements

- Python 3.10+ with [uv](https://docs.astral.sh/uv/)
- Node.js 18+
- An [OpenRouter](https://openrouter.ai/) API key (free models require no balance)

### 2. Install dependencies

```bash
# Backend (Python)
uv sync

# Frontend (React)
cd frontend && npm install && cd ..
```

### 3. Configure API Key

Create a `.env` file in the project root:

```bash
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
```

Get your free API key at [openrouter.ai/keys](https://openrouter.ai/keys).

### 4. Run

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
./start.sh
```

**Or manually in two terminals:**

```bash
# Terminal 1 - Backend (port 8001)
uv run python -m backend.main

# Terminal 2 - Frontend (port 5173)
cd frontend && npm run dev
```

Open http://localhost:5173 in your browser.

## How to Use

1. Click **"+ Nueva Conversacion"** (New Conversation)
2. In the **"Configuracion de Batalla"** (Battle Config) panel:
   - Choose how many models will compete (2-6)
   - Select each model from the dropdown (30+ free options)
   - Choose the chairman model separately
3. Type your question and press Enter
4. Watch the live battle unfold through all 3 rounds

## Architecture

```
llm-council/
  backend/
    main.py          # FastAPI + SSE streaming endpoints
    council.py       # 3-stage orchestration + retry/fallback
    openrouter.py    # OpenRouter API client + free model fetching
    config.py        # Default configuration
    storage.py       # JSON persistence
  frontend/
    src/
      App.jsx                    # Global state + SSE handling
      api.js                     # API client with SSE streaming
      components/
        ModelSelector.jsx/css    # Model + quantity selector
        ProcessTimeline.jsx/css  # Battle arena (panels, podium, chairman)
        ChatInterface.jsx/css    # Main chat
        Sidebar.jsx              # Conversation list
```

## Tech Stack

- **Backend:** FastAPI, async httpx, SSE (Server-Sent Events)
- **Frontend:** React 18 + Vite, react-markdown
- **API:** OpenRouter (proxy for 30+ LLM providers)
- **Storage:** JSON files in `data/conversations/`
- **Package Management:** uv (Python), npm (JS)

## Credits

- Original idea: [Andrej Karpathy](https://github.com/karpathy/llm-council)
- Fork with arena UI, dynamic selector, retry, and Spanish: [msemino](https://github.com/msemino)
- Vibe coded with Claude Code (Opus 4.6)

---

# LLM Council - Arena de Batalla de Modelos (Espanol)

> Fork personalizado del [llm-council de Karpathy](https://github.com/karpathy/llm-council) con UI tipo "arena de batalla", selector dinamico de modelos gratuitos, mecanismo de retry/fallback, y soporte completo en espanol.

## Que es esto?

En vez de preguntar a un solo LLM, esta app envia tu pregunta a **multiples modelos de IA simultaneamente**, los hace evaluarse entre si, y un modelo "presidente" sintetiza la mejor respuesta final.

### Las 3 Rondas de la Batalla

1. **Ronda 1 - Respuestas individuales**: Tu pregunta se envia en paralelo a todos los modelos seleccionados. Se muestran las respuestas lado a lado en paneles con colores y emojis por modelo. Incluye mecanismo de **retry automatico** si menos de 2 modelos responden (reintenta modelos fallidos + usa modelos de respaldo).

2. **Ronda 2 - Evaluaciones cruzadas**: Cada modelo evalua las respuestas de los demas (anonimizadas como "Response A", "Response B", etc.) y genera un ranking. Se calcula un **ranking agregado** tipo podio.

3. **Ronda 3 - Veredicto del Presidente**: Un modelo designado como presidente analiza todas las respuestas + evaluaciones y sintetiza una respuesta final concisa (3-4 parrafos max).

## Diferencias vs el Original

| Feature | Karpathy original | Este fork |
|---------|------------------|-----------|
| Selector de modelos | Hardcoded en config.py | **UI dinamica** con 30+ modelos gratuitos |
| Cantidad de modelos | Fijo (4) | **Configurable 2-6** desde el frontend |
| Modelo presidente | Fijo | **Seleccionable** por separado |
| Respuesta presidente | Larga | **Corta y concisa** (3-4 parrafos) |
| Idioma | Ingles | **Todo en espanol** |
| Retry/Fallback | No | **Si** - reintenta fallidos + modelos de respaldo |
| Nombres de modelos | Ocultos durante carga | **Visibles siempre** con emoji y color |
| UI | Tabs basicos | **Arena de batalla** con paneles lado a lado, podio, timeline en vivo |
| Modelos | De pago (GPT-5, Claude, etc.) | **100% gratuitos** via OpenRouter |

## Instalacion

### 1. Requisitos

- Python 3.10+ con [uv](https://docs.astral.sh/uv/)
- Node.js 18+
- Una API key de [OpenRouter](https://openrouter.ai/) (los modelos gratuitos no requieren saldo)

### 2. Instalar dependencias

```bash
# Backend (Python)
uv sync

# Frontend (React)
cd frontend && npm install && cd ..
```

### 3. Configurar API Key

Crea un archivo `.env` en la raiz del proyecto:

```bash
OPENROUTER_API_KEY=sk-or-v1-tu-api-key-aqui
```

Obtene tu API key gratis en [openrouter.ai/keys](https://openrouter.ai/keys).

### 4. Ejecutar

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
./start.sh
```

**O manualmente en dos terminales:**

```bash
# Terminal 1 - Backend (puerto 8001)
uv run python -m backend.main

# Terminal 2 - Frontend (puerto 5173)
cd frontend && npm run dev
```

Abrir http://localhost:5173 en el navegador.

## Como usar

1. Click en **"+ Nueva Conversacion"**
2. En el panel **"Configuracion de Batalla"**:
   - Elegir cuantos modelos competiran (2-6)
   - Seleccionar cada modelo del dropdown (30+ opciones gratuitas)
   - Elegir el modelo presidente por separado
3. Escribir tu pregunta y presionar Enter
4. Ver la batalla en vivo con las 3 rondas

## Creditos

- Idea original: [Andrej Karpathy](https://github.com/karpathy/llm-council)
- Fork con UI arena, selector dinamico, retry, y espanol: [msemino](https://github.com/msemino)
- Vibe coded con Claude Code (Opus 4.6)
