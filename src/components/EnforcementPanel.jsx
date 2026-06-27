import React, { useState } from 'react'

const CAT_ICON = { industrial:'🏭', construction:'🏗️', burning:'🔥', traffic:'🚗', other:'💨' }

function prob_color(p) {
  if (p >= 0.8) return '#ef4444'
  if (p >= 0.6) return '#f97316'
  if (p >= 0.4) return '#eab308'
  return '#4ade80'
}

export default function EnforcementPanel({ plan }) {
  const [dispatched, setDispatched] = useState({})

  if (!plan || !plan.actions?.length) {
    return (
      <div style={{ padding: 24, color: '#64748b', textAlign: 'center' }}>
        <div style={{ fontSize: 32, marginBottom: 8 }}>✅</div>
        <div>No enforcement actions required at this time</div>
      </div>
    )
  }

  const { actions = [], total_estimated_aqi_reduction } = plan

  const handleDispatch = (actionId) => {
    setDispatched(d => ({ ...d, [actionId]: true }))
    // In prod: POST /api/enforcement/dispatch
  }

  return (
    <div>
      {/* Summary bar */}
      <div style={{
        display: 'flex', gap: 16, marginBottom: 16, padding: '10px 14px',
        background: '#0f172a', borderRadius: 8, border: '1px solid #1e293b',
      }}>
        <div>
          <div style={{ fontSize: 11, color: '#64748b' }}>ACTIONS QUEUED</div>
          <div style={{ fontSize: 24, fontWeight: 800, color: '#f87171' }}>{actions.length}</div>
        </div>
        <div>
          <div style={{ fontSize: 11, color: '#64748b' }}>EST. AQI REDUCTION</div>
          <div style={{ fontSize: 24, fontWeight: 800, color: '#4ade80' }}>
            −{total_estimated_aqi_reduction?.toFixed(0)}
          </div>
        </div>
        <div style={{ flex: 1, display: 'flex', alignItems: 'center' }}>
          <div style={{ fontSize: 11, color: '#94a3b8' }}>
            Prioritised by: violation probability × estimated AQI impact
          </div>
        </div>
      </div>

      {/* Action cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {actions.slice(0, 6).map((action, i) => {
          const src = action.source || {}
          const isDispatched = dispatched[action.action_id] || action.dispatched
          const vProb = action.violation_probability || 0
          const startH = action.optimal_inspection_start || 22
          const endH = action.optimal_inspection_end || 2

          return (
            <div key={action.action_id || i} style={{
              padding: '12px 14px', background: '#0f172a',
              borderRadius: 8, border: `1px solid ${isDispatched ? '#166534' : '#1e293b'}`,
              transition: 'border-color 0.3s',
            }}>
              {/* Header row */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{
                    width: 20, height: 20, borderRadius: '50%',
                    background: '#1e293b', display: 'flex', alignItems: 'center',
                    justifyContent: 'center', fontSize: 11, fontWeight: 700,
                    color: '#94a3b8', flexShrink: 0,
                  }}>
                    {action.priority_rank}
                  </span>
                  <span style={{ fontSize: 14 }}>{CAT_ICON[src.category] || '⚠️'}</span>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0' }}>{src.name}</div>
                    <div style={{ fontSize: 11, color: '#64748b' }}>
                      {src.category} · Ward: {action.contributing_aqi_ward}
                      {src.permit_status === 'expired' && (
                        <span style={{ marginLeft: 6, color: '#ef4444', fontWeight: 600 }}>PERMIT EXPIRED</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Dispatch button */}
                {isDispatched ? (
                  <span style={{
                    padding: '4px 10px', borderRadius: 6, fontSize: 11,
                    background: '#14532d', color: '#4ade80', fontWeight: 600,
                  }}>✓ DISPATCHED</span>
                ) : (
                  <button
                    onClick={() => handleDispatch(action.action_id)}
                    style={{
                      padding: '5px 12px', borderRadius: 6, fontSize: 11,
                      background: '#1e3a5f', color: '#60a5fa', fontWeight: 600,
                      border: '1px solid #1d4ed8', cursor: 'pointer',
                      transition: 'all 0.15s',
                    }}
                    onMouseOver={e => e.target.style.background = '#1d4ed8'}
                    onMouseOut={e => e.target.style.background = '#1e3a5f'}
                  >
                    DISPATCH →
                  </button>
                )}
              </div>

              {/* Metrics row */}
              <div style={{ display: 'flex', gap: 16 }}>
                <Metric label="VIOLATION PROB" value={`${Math.round(vProb*100)}%`} color={prob_color(vProb)} />
                <Metric label="OPTIMAL TIME" value={`${startH.toString().padStart(2,'0')}:00–${endH.toString().padStart(2,'0')}:00`} color="#94a3b8" />
                <Metric label="AQI IMPACT" value={`−${action.estimated_aqi_impact?.toFixed(0)}`} color="#4ade80" />
              </div>

              {/* Evidence */}
              <div style={{
                marginTop: 8, padding: '6px 10px', background: '#0a0f1a',
                borderRadius: 6, fontSize: 11, color: '#475569', lineHeight: 1.5,
              }}>
                {action.evidence_summary}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function Metric({ label, value, color }) {
  return (
    <div>
      <div style={{ fontSize: 10, color: '#475569', textTransform: 'uppercase', letterSpacing: 0.8 }}>{label}</div>
      <div style={{ fontSize: 14, fontWeight: 700, color: color || '#e2e8f0' }}>{value}</div>
    </div>
  )
}
