import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './ProcessTimeline.css';

const MODEL_COLORS = {
  'deepseek': { emoji: '🧠', color: '#4a6cf7', bg: 'rgba(74,108,247,0.08)', border: 'rgba(74,108,247,0.3)' },
  'llama':    { emoji: '🦙', color: '#f97316', bg: 'rgba(249,115,22,0.08)', border: 'rgba(249,115,22,0.3)' },
  'gemma':    { emoji: '💎', color: '#10b981', bg: 'rgba(16,185,129,0.08)', border: 'rgba(16,185,129,0.3)' },
  'qwen':     { emoji: '🐉', color: '#8b5cf6', bg: 'rgba(139,92,246,0.08)', border: 'rgba(139,92,246,0.3)' },
  'gpt':      { emoji: '🤖', color: '#22d3ee', bg: 'rgba(34,211,238,0.08)', border: 'rgba(34,211,238,0.3)' },
  'claude':   { emoji: '🎭', color: '#f59e0b', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.3)' },
  'mistral':  { emoji: '🌪️', color: '#ec4899', bg: 'rgba(236,72,153,0.08)', border: 'rgba(236,72,153,0.3)' },
  'hermes':   { emoji: '📜', color: '#a78bfa', bg: 'rgba(167,139,250,0.08)', border: 'rgba(167,139,250,0.3)' },
  'dolphin':  { emoji: '🐬', color: '#06b6d4', bg: 'rgba(6,182,212,0.08)', border: 'rgba(6,182,212,0.3)' },
  'nvidia':   { emoji: '🟢', color: '#84cc16', bg: 'rgba(132,204,22,0.08)', border: 'rgba(132,204,22,0.3)' },
  'solar':    { emoji: '☀️', color: '#eab308', bg: 'rgba(234,179,8,0.08)', border: 'rgba(234,179,8,0.3)' },
  'glm':      { emoji: '🀄', color: '#ef4444', bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.3)' },
  'liquid':   { emoji: '💧', color: '#38bdf8', bg: 'rgba(56,189,248,0.08)', border: 'rgba(56,189,248,0.3)' },
  'arcee':    { emoji: '🔮', color: '#c084fc', bg: 'rgba(192,132,252,0.08)', border: 'rgba(192,132,252,0.3)' },
  'phi':      { emoji: '🔬', color: '#14b8a6', bg: 'rgba(20,184,166,0.08)', border: 'rgba(20,184,166,0.3)' },
  'gemini':   { emoji: '✨', color: '#60a5fa', bg: 'rgba(96,165,250,0.08)', border: 'rgba(96,165,250,0.3)' },
};

function getMeta(modelName) {
  const lower = modelName.toLowerCase();
  for (const [key, val] of Object.entries(MODEL_COLORS)) {
    if (lower.includes(key)) return val;
  }
  return { emoji: '🤖', color: '#6b7280', bg: 'rgba(107,114,128,0.08)', border: 'rgba(107,114,128,0.3)' };
}

function shortName(model) {
  return model.split('/')[1]?.replace(':free', '').replace('-thinking-2507', '') || model;
}

function deAnonymize(text, labelToModel) {
  if (!labelToModel || !text) return text;
  let result = text;
  Object.entries(labelToModel).forEach(([label, model]) => {
    result = result.replace(new RegExp(label, 'g'), `**${shortName(model)}**`);
  });
  return result;
}

export default function ProcessTimeline({ message, isLoading }) {
  const [elapsed, setElapsed] = useState({ s1: 0, s2: 0, s3: 0 });
  const [starts, setStarts] = useState({ s1: null, s2: null, s3: null });
  const [expandedS2, setExpandedS2] = useState(null); // which evaluator tab is expanded

  useEffect(() => {
    if (message?.loading?.stage1 && !starts.s1) setStarts(p => ({ ...p, s1: Date.now() }));
    if (message?.loading?.stage2 && !starts.s2) setStarts(p => ({ ...p, s2: Date.now() }));
    if (message?.loading?.stage3 && !starts.s3) setStarts(p => ({ ...p, s3: Date.now() }));
  }, [message?.loading]);

  useEffect(() => {
    const iv = setInterval(() => {
      setElapsed({
        s1: starts.s1 && message?.loading?.stage1 ? Math.floor((Date.now() - starts.s1) / 1000) : elapsed.s1,
        s2: starts.s2 && message?.loading?.stage2 ? Math.floor((Date.now() - starts.s2) / 1000) : elapsed.s2,
        s3: starts.s3 && message?.loading?.stage3 ? Math.floor((Date.now() - starts.s3) / 1000) : elapsed.s3,
      });
    }, 1000);
    return () => clearInterval(iv);
  }, [starts, message?.loading]);

  if (!message || message.role !== 'assistant') return null;

  const ld = message.loading || {};
  const s1 = message.stage1;
  const s2 = message.stage2;
  const s3 = message.stage3;
  const isActive = ld.stage1 || ld.stage2 || ld.stage3;
  const labelToModel = message.metadata?.label_to_model;
  const aggRank = message.metadata?.aggregate_rankings;
  const retryInfo = message.retryInfo;
  const models = s1 ? s1.map(r => r.model) : [];
  const selectedModels = message.selectedModels || [];
  const placeholderModels = selectedModels.length > 0 ? selectedModels : ['deepseek', 'llama', 'gemma', 'qwen'];

  return (
    <div className={`arena ${isActive ? 'live' : ''}`}>

      {/* ======= HEADER + PROGRESS ======= */}
      <div className="arena-header">
        <div className="arena-title">⚔️ Arena del Consejo LLM</div>
        {isActive && <div className="badge-live">● EN VIVO</div>}
        {!isActive && s3 && <div className="badge-done">✓ COMPLETADO</div>}
      </div>

      <div className="arena-steps">
        <div className={`step ${s1 || ld.stage1 ? 'on' : ''} ${s1 ? 'ok' : ''}`}>
          <span className="step-n">{s1 ? '✓' : '1'}</span> Respuestas
        </div>
        <div className={`step-line ${s1 ? 'filled' : ''}`} />
        <div className={`step ${s2 || ld.stage2 ? 'on' : ''} ${s2 ? 'ok' : ''}`}>
          <span className="step-n">{s2 ? '✓' : '2'}</span> Evaluaciones
        </div>
        <div className={`step-line ${s2 ? 'filled' : ''}`} />
        <div className={`step ${s3 || ld.stage3 ? 'on' : ''} ${s3 ? 'ok' : ''}`}>
          <span className="step-n">{s3 ? '✓' : '3'}</span> Veredicto
        </div>
      </div>

      {/* ======= ROUND 1: SIDE-BY-SIDE RESPONSES ======= */}
      {(ld.stage1 || s1) && (
        <div className="round">
          <div className="round-header">
            <h4>🎯 Ronda 1 — Los modelos responden</h4>
            {ld.stage1 && <span className="timer">{elapsed.s1}s</span>}
            {s1 && <span className="timer done">✓ {elapsed.s1}s</span>}
          </div>

          <div className="panels">
            {(s1 || placeholderModels.map((k, i) => ({ model: k, placeholder: true, index: i }))).map((item, i) => {
              const isPlaceholder = !s1;
              const model = isPlaceholder ? placeholderModels[i] : item.model;
              const meta = getMeta(model);
              const resp = isPlaceholder ? null : item.response;

              return (
                <div
                  key={`${model}-${i}`}
                  className={`panel ${isPlaceholder ? 'thinking' : 'done'}`}
                  style={{ borderColor: meta.border, background: meta.bg }}
                >
                  <div className="panel-head" style={{ borderBottomColor: meta.border }}>
                    <span className="panel-emoji">{meta.emoji}</span>
                    <span className="panel-name" style={{ color: meta.color }}>
                      {shortName(model)}
                    </span>
                    {isPlaceholder && <span className="panel-dots">pensando<span className="dots-anim" /></span>}
                    {!isPlaceholder && <span className="panel-wc">{resp?.split(/\s+/).length || 0} palabras</span>}
                  </div>
                  <div className="panel-body">
                    {isPlaceholder ? (
                      <div className="shimmer-block">
                        <div className="shimmer-line w80" /><div className="shimmer-line w60" />
                        <div className="shimmer-line w90" /><div className="shimmer-line w40" />
                        <div className="shimmer-line w70" />
                      </div>
                    ) : (
                      <div className="panel-md markdown-content">
                        <ReactMarkdown>{resp}</ReactMarkdown>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Retry banner */}
          {retryInfo && ld.stage1 && (
            <div className="retry-banner">
              <span className="retry-icon">🔄</span>
              <span className="retry-text">
                {retryInfo.backup
                  ? `Solo ${retryInfo.successful} modelo(s) respondieron. Probando modelos de respaldo...`
                  : `Solo ${retryInfo.successful} modelo(s) respondieron. Reintentando ${retryInfo.retrying?.length || 0} modelo(s) fallido(s)...`
                }
              </span>
              <span className="dots-anim" />
            </div>
          )}
        </div>
      )}

      {/* ======= ROUND 2: EVALUACIONES CRUZADAS ======= */}
      {(ld.stage2 || s2) && (
        <div className="round">
          <div className="round-header">
            <h4>⚔️ Ronda 2 — Evaluaciones cruzadas (anonimas)</h4>
            {ld.stage2 && <span className="timer">{elapsed.s2}s</span>}
            {s2 && <span className="timer done">✓ {elapsed.s2}s</span>}
          </div>

          {ld.stage2 && !s2 ? (
            /* Loading state: show models evaluating each other */
            <div className="eval-loading">
              <div className="eval-desc">Cada modelo esta evaluando las respuestas anonimizadas de los demas...</div>
              <div className="eval-grid">
                {models.map((m, i) => {
                  const meta = getMeta(m);
                  return (
                    <div key={m} className="eval-card" style={{ borderColor: meta.border, background: meta.bg }}>
                      <div className="eval-avatar" style={{ background: meta.color }}>{meta.emoji}</div>
                      <div className="eval-name">{shortName(m)}</div>
                      <div className="eval-status">
                        evaluando<span className="dots-anim" />
                      </div>
                      <div className="eval-arrows">
                        {models.filter((_, j) => j !== i).map((t, j) => (
                          <span key={j} className="eval-arrow" style={{ color: getMeta(t).color, animationDelay: `${j * 0.3}s` }}>
                            →{getMeta(t).emoji}
                          </span>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : s2 && (
            /* Completed: show evaluation tabs + podium */
            <div className="eval-done">
              {/* Evaluator selector tabs */}
              <div className="eval-tabs">
                {s2.map((ev, i) => {
                  const meta = getMeta(ev.model);
                  return (
                    <button
                      key={i}
                      className={`eval-tab ${expandedS2 === i ? 'active' : ''}`}
                      style={expandedS2 === i ? { borderColor: meta.color, color: meta.color, background: meta.bg } : {}}
                      onClick={() => setExpandedS2(expandedS2 === i ? null : i)}
                    >
                      {meta.emoji} {shortName(ev.model)}
                    </button>
                  );
                })}
              </div>

              {/* Expanded evaluation content */}
              {expandedS2 !== null && s2[expandedS2] && (
                <div className="eval-content" style={{ borderColor: getMeta(s2[expandedS2].model).border }}>
                  <div className="eval-content-head">
                    Evaluacion de <strong>{shortName(s2[expandedS2].model)}</strong>:
                  </div>
                  <div className="eval-content-body markdown-content">
                    <ReactMarkdown>
                      {deAnonymize(s2[expandedS2].ranking, labelToModel)}
                    </ReactMarkdown>
                  </div>
                  {s2[expandedS2].parsed_ranking?.length > 0 && (
                    <div className="eval-parsed">
                      <strong>Su ranking:</strong>
                      <ol>
                        {s2[expandedS2].parsed_ranking.map((label, j) => (
                          <li key={j}>
                            {labelToModel?.[label] ? (
                              <><span style={{ color: getMeta(labelToModel[label]).color }}>{getMeta(labelToModel[label]).emoji}</span> {shortName(labelToModel[label])}</>
                            ) : label}
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}
                </div>
              )}

              {/* Podium */}
              {aggRank && aggRank.length > 0 && (
                <div className="podium-section">
                  <h5>🏆 Ranking Final Agregado</h5>
                  <div className="podium">
                    {aggRank.map((a, i) => {
                      const meta = getMeta(a.model);
                      const medals = ['🥇', '🥈', '🥉', '4️⃣'];
                      const heights = [100, 72, 50, 35];
                      return (
                        <div key={a.model} className="podium-col" style={{ animationDelay: `${i * 0.15}s` }}>
                          <div className="podium-medal">{medals[i] || `#${i + 1}`}</div>
                          <div className="podium-av" style={{ background: meta.color }}>{meta.emoji}</div>
                          <div className="podium-name">{shortName(a.model)}</div>
                          <div className="podium-score">Prom: {a.average_rank.toFixed(1)} ({a.rankings_count} votos)</div>
                          <div className="podium-bar-wrap">
                            <div className="podium-bar" style={{ height: `${heights[i]}%`, background: meta.color }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ======= ROUND 3: CHAIRMAN ======= */}
      {(ld.stage3 || s3) && (
        <div className="round round-chairman">
          <div className="round-header">
            <h4>🏛️ Ronda 3 — Veredicto del Presidente</h4>
            {ld.stage3 && <span className="timer">{elapsed.s3}s</span>}
            {s3 && <span className="timer done">✓ {elapsed.s3}s</span>}
          </div>

          {ld.stage3 && !s3 ? (
            <div className="chairman-wait">
              <div className="chairman-icon">⚖️</div>
              <div>
                <div className="chairman-msg">El Presidente analiza todas las respuestas y evaluaciones...</div>
                <div className="chairman-sub">Sintetizando el veredicto final del consejo</div>
                <div className="chairman-bar"><div className="chairman-fill" /></div>
              </div>
            </div>
          ) : s3 && (
            <div className="chairman-result">
              <div className="chairman-head">
                <span className="chairman-icon-sm">⚖️</span>
                Presidente: <strong>{shortName(s3.model)}</strong>
              </div>
              <div className="chairman-body markdown-content">
                <ReactMarkdown>{s3.response}</ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
