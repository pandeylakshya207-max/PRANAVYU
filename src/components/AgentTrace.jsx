import React from 'react'

const AGENT_META = {
  data_ingestion:         { label: 'Data Ingestion',         icon: '📡', color: '#60a5fa' },
  attribution_agent:      { label: 'Source Attribution',     icon: '🔍', color: '#a78bfa' },
  forecast_agent:         { label: 'Predictive Forecast',    icon: '📈', color: '#34d399' },
  enforcement_agent:      { label: 'Enforcement Intel',      icon: '🚔', color: '#f87171' },
  citizen_advisory_agent: { label: 'Citizen Advisory',       icon: '📢', color: '#fbbf24' },
  cross_city_agent:       { label: 'Cross-City Learning',    icon: '🏙️', color: '#fb923c' },
  synthesizer:            { label: 'Output Synthesizer',     icon: '⚡', color: '#4ade80' },
}

function fmt_time(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleTimeString()
}

export default function AgentTrace({ trace = [], completedAgents = [] }) {
  const agentOrder = [
    'data_ingestion', 'attribution_agent', 'forecast_agent',
    'enforcement_agent', 'citizen_advisory_agent', 'cross_city_agent', 'synthesizer'
  ]

  return (
    <div>
      <div style={{ fontSize: 11, color: '#64748b', textTransform:'uppercase', letterSpacing:1, marginBottom: 12 }}>
        MULTI-AGENT EXECUTION TRACE
      </div>

      {/* Pipeline visualization */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
        {agentOrder.map((agentKey, i) => {
          const meta = AGENT_META[agentKey] || { label: agentKey, icon: '🤖', color: '#94a3b8' }
          const traceEntry = trace.find(t => t.agent === agentKey)
          const completed = completedAgents.includes(agentKey) || !!traceEntry

          return (
            <div key={agentKey}>
              <div style={{
                display: 'flex', alignItems: 'flex-start', gap: 12,
                padding: '10px 14px',
                background: completed ? '#0f172a' : 'transparent',
                borderRadius: 8,
                border: completed ? `1px solid ${meta.color}33` : '1px solid transparent',
                opacity: completed ? 1 : 0.4,
                transition: 'all 0.3s',
              }}>
                {/* Icon + connector */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: '50%',
                    background: completed ? meta.color + '22' : '#1e293b',
                    border: `2px solid ${completed ? meta.color : '#334155'}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 14, transition: 'all 0.3s',
                  }}>
                    {completed ? meta.icon : '○'}
                  </div>
                  {i < agentOrder.length - 1 && (
                    <div style={{
                      width: 2, height: 20, marginTop: 2,
                      background: completed ? meta.color + '44' : '#1e293b',
                      transition: 'background 0.3s',
                    }} />
                  )}
                </div>

                {/* Content */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: 13, fontWeight: 600, color: completed ? '#e2e8f0' : '#475569' }}>
                      {meta.label}
                    </span>
                    {traceEntry?.timestamp && (
                      <span style={{ fontSize: 11, color: '#475569' }}>
                        {fmt_time(traceEntry.timestamp)}
                      </span>
                    )}
                  </div>

                  {traceEntry && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {Object.entries(traceEntry)
                        .filter(([k]) => !['agent','timestamp'].includes(k))
                        .slice(0, 4)
                        .map(([k, v]) => (
                          <span key={k} style={{
                            padding: '1px 7px', borderRadius: 4, fontSize: 11,
                            background: '#1e293b', color: '#94a3b8',
                          }}>
                            {k.replace(/_/g,' ')}: <span style={{ color: meta.color }}>{String(v)}</span>
                          </span>
                        ))}
                    </div>
                  )}
                </div>

                {/* Status dot */}
                {completed && (
                  <div style={{
                    width: 8, height: 8, borderRadius: '50%',
                    background: meta.color, flexShrink: 0, marginTop: 4,
                    boxShadow: `0 0 6px ${meta.color}`,
                  }} />
                )}
              </div>
            </div>
          )
        })}
      </div>

      {completedAgents.length > 0 && (
        <div style={{
          marginTop: 12, padding: '8px 12px',
          background: '#0a1628', borderRadius: 6,
          border: '1px solid #1e293b', fontSize: 12, color: '#475569',
        }}>
          ⚡ All {completedAgents.length} agents completed · Full pipeline in ~60ms
        </div>
      )}
    </div>
  )
}
