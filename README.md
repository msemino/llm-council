# LLM Council - Arena de Batalla de Modelos

![llmcouncil](header.jpg)

> Fork personalizado del [llm-council de Karpathy](https://github.com/karpathy/llm-council) con UI tipo "arena de batalla", selector dinamico de modelos gratuitos, y respuestas 100% en espanol.

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

## Screenshots

La UI muestra:
- Panel de configuracion con selector de cantidad (2-6) y dropdowns por modelo
- Arena en vivo con badge "EN VIVO" durante la batalla
- Paneles lado a lado con shimmer loading y nombres reales
- Tabs de evaluacion por modelo con de-anonimizacion
- Podio con ranking agregado y barras de colores
- Veredicto del presidente conciso

## Setup

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

## Arquitectura

```
llm-council/
  backend/
    main.py          # FastAPI + endpoints SSE streaming
    council.py       # Orquestacion 3 etapas + retry/fallback
    openrouter.py    # Cliente API OpenRouter + fetch modelos gratis
    config.py        # Configuracion por defecto
    storage.py       # Persistencia JSON
  frontend/
    src/
      App.jsx                    # Estado global + manejo SSE
      api.js                     # Cliente API con streaming SSE
      components/
        ModelSelector.jsx/css    # Selector de modelos + cantidad
        ProcessTimeline.jsx/css  # Arena de batalla (paneles, podio, chairman)
        ChatInterface.jsx/css    # Chat principal
        Sidebar.jsx              # Lista de conversaciones
```

## Tech Stack

- **Backend:** FastAPI, async httpx, SSE (Server-Sent Events)
- **Frontend:** React 18 + Vite, react-markdown
- **API:** OpenRouter (proxy para 30+ proveedores de LLM)
- **Storage:** JSON files en `data/conversations/`
- **Package Management:** uv (Python), npm (JS)

## Creditos

- Idea original: [Andrej Karpathy](https://github.com/karpathy/llm-council)
- Fork con UI arena, selector dinamico, retry, y espanol: [msemino](https://github.com/msemino)
- Vibe coded con Claude Code (Opus 4.6)
