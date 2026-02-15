/**
 * @fileoverview Dynamic model selector for configuring council battles.
 *
 * Fetches the live catalogue of free OpenRouter models on mount and lets the
 * user pick 2-6 competing models (Stages 1 & 2) plus a separate chairman
 * model (Stage 3). Configuration changes are propagated to the parent via
 * the `onConfigChange` callback.
 *
 * Selector dinámico de modelos para configurar las batallas del consejo.
 * Obtiene el catálogo de modelos gratuitos de OpenRouter y permite al usuario
 * elegir 2-6 modelos competidores más un modelo presidente separado.
 *
 * @module ModelSelector
 */

import { useState, useEffect } from 'react';
import './ModelSelector.css';

/** @constant {Object.<string, string>} Emoji map for known model families. */
const MODEL_EMOJIS = {
  'deepseek': '🧠', 'llama': '🦙', 'gemma': '💎', 'qwen': '🐉',
  'gpt': '🤖', 'claude': '🎭', 'mistral': '🌪️', 'nvidia': '🟢',
  'hermes': '📜', 'solar': '☀️', 'dolphin': '🐬', 'arcee': '🔮',
  'aurora': '🌅', 'glm': '🀄', 'liquid': '💧', 'step': '👣',
  'upstage': '🔼', 'trinity': '🔺',
};

/** Resolve emoji for a model id by matching against known family names. */
function getEmoji(modelId) {
  const lower = modelId.toLowerCase();
  for (const [key, emoji] of Object.entries(MODEL_EMOJIS)) {
    if (lower.includes(key)) return emoji;
  }
  return '🤖';
}

function shortId(id) {
  return id.split('/').pop()?.replace(':free', '') || id;
}

/**
 * Collapsible configuration panel for battle parameters.
 *
 * @param {Object} props
 * @param {(config: {council_models: string[], chairman_model: string}) => void} props.onConfigChange
 * @param {boolean} props.disabled - Disable controls while a battle is in progress.
 * @returns {JSX.Element}
 */
export default function ModelSelector({ onConfigChange, disabled }) {
  const [freeModels, setFreeModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [numModels, setNumModels] = useState(4);
  const [selectedModels, setSelectedModels] = useState([]);
  const [chairmanModel, setChairmanModel] = useState('');
  const [expanded, setExpanded] = useState(true);

  // Fetch free models on mount
  useEffect(() => {
    fetch('http://localhost:8001/api/models/free')
      .then(r => r.json())
      .then(models => {
        setFreeModels(models);
        // Set defaults
        const defaults = [
          'deepseek/deepseek-r1-0528:free',
          'meta-llama/llama-3.3-70b-instruct:free',
          'google/gemma-3-27b-it:free',
          'qwen/qwen3-235b-a22b-thinking-2507',
        ];
        const validDefaults = defaults.filter(d => models.some(m => m.id === d));
        setSelectedModels(validDefaults.length > 0 ? validDefaults : models.slice(0, 4).map(m => m.id));
        setChairmanModel(validDefaults[0] || models[0]?.id || '');
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // Notify parent when config changes
  useEffect(() => {
    if (selectedModels.length > 0 && chairmanModel) {
      onConfigChange({ council_models: selectedModels, chairman_model: chairmanModel });
    }
  }, [selectedModels, chairmanModel]);

  const handleNumChange = (n) => {
    setNumModels(n);
    if (selectedModels.length > n) {
      // Trim excess models
      setSelectedModels(selectedModels.slice(0, n));
    } else if (selectedModels.length < n) {
      // Auto-fill with available models not yet selected
      const toAdd = n - selectedModels.length;
      const available = freeModels.filter(m => !selectedModels.includes(m.id));
      const newModels = [...selectedModels, ...available.slice(0, toAdd).map(m => m.id)];
      setSelectedModels(newModels);
    }
  };

  const handleModelSelect = (index, modelId) => {
    const updated = [...selectedModels];
    updated[index] = modelId;
    setSelectedModels(updated);
  };

  const addSlot = () => {
    if (selectedModels.length < numModels) {
      // Pick first model not already selected
      const available = freeModels.find(m => !selectedModels.includes(m.id));
      if (available) setSelectedModels([...selectedModels, available.id]);
    }
  };

  const removeSlot = (index) => {
    if (selectedModels.length > 2) {
      const newModels = selectedModels.filter((_, i) => i !== index);
      setSelectedModels(newModels);
      setNumModels(newModels.length);
    }
  };

  if (loading) {
    return <div className="model-selector loading-models">Cargando modelos gratuitos...</div>;
  }

  return (
    <div className="model-selector">
      <div className="ms-header" onClick={() => setExpanded(!expanded)}>
        <span className="ms-title">⚙️ Configuracion de Batalla</span>
        <span className="ms-toggle">{expanded ? '▼' : '▶'}</span>
        {!expanded && (
          <span className="ms-summary">
            {selectedModels.length} modelos | Presidente: {shortId(chairmanModel)}
          </span>
        )}
      </div>

      {expanded && (
        <div className="ms-body">
          {/* Number of models */}
          <div className="ms-section">
            <label className="ms-label">Cantidad de modelos competidores:</label>
            <div className="ms-num-row">
              {[2, 3, 4, 5, 6].map(n => (
                <button
                  key={n}
                  className={`ms-num-btn ${numModels === n ? 'active' : ''}`}
                  onClick={() => handleNumChange(n)}
                  disabled={disabled}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>

          {/* Model selectors */}
          <div className="ms-section">
            <label className="ms-label">Modelos competidores (Rondas 1 y 2):</label>
            <div className="ms-models-list">
              {selectedModels.map((modelId, i) => (
                <div key={i} className="ms-model-row">
                  <span className="ms-model-num">{i + 1}.</span>
                  <span className="ms-model-emoji">{getEmoji(modelId)}</span>
                  <select
                    className="ms-select"
                    value={modelId}
                    onChange={(e) => handleModelSelect(i, e.target.value)}
                    disabled={disabled}
                  >
                    {freeModels.map(m => (
                      <option key={m.id} value={m.id}>
                        {m.name} ({Math.round(m.context_length / 1024)}K ctx)
                      </option>
                    ))}
                  </select>
                  {selectedModels.length > 2 && (
                    <button
                      className="ms-remove-btn"
                      onClick={() => removeSlot(i)}
                      disabled={disabled}
                      title="Eliminar modelo"
                    >
                      ✕
                    </button>
                  )}
                </div>
              ))}
              {selectedModels.length < numModels && (
                <button className="ms-add-btn" onClick={addSlot} disabled={disabled}>
                  + Agregar modelo
                </button>
              )}
            </div>
          </div>

          {/* Chairman selector */}
          <div className="ms-section">
            <label className="ms-label">⚖️ Modelo Presidente (Ronda 3 - Veredicto Final):</label>
            <div className="ms-model-row">
              <span className="ms-model-emoji">{getEmoji(chairmanModel)}</span>
              <select
                className="ms-select chairman"
                value={chairmanModel}
                onChange={(e) => setChairmanModel(e.target.value)}
                disabled={disabled}
              >
                {freeModels.map(m => (
                  <option key={m.id} value={m.id}>
                    {m.name} ({Math.round(m.context_length / 1024)}K ctx)
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
