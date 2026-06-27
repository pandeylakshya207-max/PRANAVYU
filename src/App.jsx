import React, { useState, useEffect } from 'react'
import AQIMap from './components/AQIMap'
import AttributionPanel from './components/AttributionPanel'
import ForecastChart from './components/ForecastChart'
import EnforcementPanel from './components/EnforcementPanel'
import AdvisoryPanel from './components/AdvisoryPanel'
import AgentTrace from './components/AgentTrace'
import StatsBar from './components/StatsBar'
import { useDashboard } from './hooks/useData'

const TABS = [
  { id: 'attribution', label: '🔍 Attribution',  title: 'Source Attribution' },
  { id: 'forecast',    label: '📈 Forecast',      title: '72-Hour Forecast' },
  { id: 'enforcement', label: '🚔 Enforcement',   title: 'Enforcement Intelligence' },
  { id: 'advisories',  label: '📢 Advisories',    title: 'Citizen Advisories' },
  { id: 'trace',       label: '⚡ Agent Trace',   title: 'Multi-Agent Execution Trace' },
]

export default function App() {
  const [tab, setTab] = useState('attribution')
  const [selectedWard, setSelectedWard] = useState(null)
  const { data, loading, error, lastUpdated, refresh } = useDashboard('Bengaluru')

  // Auto-select first high-risk ward when data loads
  useEffect(() => {
    if (data && !selectedWard) {
      const highRisk = (data.attribution_results || [])
        .sort((a, b) => b.current_aqi - a.current_aqi)[0]
      if (highRisk) setSelectedWard(highRisk.ward_id)
    }
  }, [data])

  const readings = data?.readings || []
  const attributions = data?.attribution_results || []
  const forecasts = data?.ward_forecasts || []
  const enforcement = data?.enforcement_plan
  const advisories = data?.advisories_en || []
  const crossCity = data?.cross_city_recommendations || []
  const trace = data?.agent_trace || []
  const completedAgents = (data?.completed_agents) ||
    (trace.map(t => t.agent).filter(a => a !== 'data_ingestion' && a !== 'synthesizer'))
  const summary = data?.summary || {}

  const selectedAttribution = attributions.find(a => a.ward_id === selectedWard) || attributions[0]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#0a0f1a', color: '#e8edf5' }}>
      {/* Header */}
      <header style={{
        padding: '0 20px', height: 52,
        background: '#060c18', borderBottom: '1px solid #1e293b',
        display: 'flex', alignItems: 'center', gap: 16, flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: 'linear-gradient(135deg, #1d4ed8, #7c3aed)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 16,
          }}>🌬️</div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 800, letterSpacing: 1, color: '#e2e8f0' }}>PRANAVYU</div>
            <div style={{ fontSize: 10, color: '#475569', letterSpacing: 1.5 }}>
              URBAN AIR QUALITY INTELLIGENCE
            </div>
          </div>
        </div>

        <div style={{ flex: 1 }} />

        {/* City badge */}
        <div style={{
          padding: '4px 12px', borderRadius: 20, fontSize: 12, fontWeight: 600,
          background: '#1e293b', color: '#60a5fa', border: '1px solid #334155',
        }}>
          📍 Bengaluru
        </div>

        {/* Live indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{
            width: 8, height: 8, borderRadius: '50%',
            background: loading ? '#fbbf24' : '#4ade80',
            boxShadow: `0 0 6px ${loading ? '#fbbf24' : '#4ade80'}`,
            animation: loading ? 'none' : 'pulse 2s infinite',
          }} />
          <span style={{ fontSize: 11, color: loading ? '#fbbf24' : '#4ade80' }}>
            {loading ? 'UPDATING...' : 'LIVE'}
          </span>
        </div>

        {/* Refresh button */}
        <button
          onClick={refresh}
          style={{
            padding: '5px 12px', borderRadius: 6, fontSize: 11,
            background: '#1e293b', color: '#94a3b8',
            border: '1px solid #334155', cursor: 'pointer',
          }}
        >
          ↻ Refresh
        </button>
      </header>

      {/* Stats bar */}
      <StatsBar summary={summary} lastUpdated={lastUpdated} />

      {/* Main layout */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Left: Map */}
        <div style={{ flex: '0 0 55%', position: 'relative', borderRight: '1px solid #1e293b' }}>
          {loading && !data && (
            <div style={{
              position: 'absolute', inset: 0, zIndex: 10,
              background: 'rgba(10,15,26,0.85)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexDirection: 'column', gap: 12,
            }}>
              <div style={{ fontSize: 32 }}>🌬️</div>
              <div style={{ fontSize: 14, color: '#60a5fa' }}>Loading PRANAVYU intelligence...</div>
              <div style={{ fontSize: 12, color: '#475569' }}>Running 6 AI agents</div>
            </div>
          )}
          <AQIMap
            readings={readings}
            attributionResults={attributions}
            selectedWard={selectedWard}
            onWardSelect={ward => {
              setSelectedWard(ward)
              setTab('attribution')
            }}
          />

          {/* Map overlay: ward count */}
          <div style={{
            position: 'absolute', top: 12, left: 12, zIndex: 900,
            background: 'rgba(6,12,24,0.9)', borderRadius: 8, padding: '6px 12px',
            border: '1px solid #1e293b', fontSize: 12, color: '#94a3b8',
          }}>
            {readings.length} wards monitored · Click any ward for attribution
          </div>
        </div>

        {/* Right: Intelligence panel */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Tab navigation */}
          <div style={{
            display: 'flex', borderBottom: '1px solid #1e293b',
            background: '#060c18', flexShrink: 0, overflowX: 'auto',
          }}>
            {TABS.map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                style={{
                  padding: '10px 14px', fontSize: 12, cursor: 'pointer', flexShrink: 0,
                  background: 'transparent', border: 'none',
                  borderBottom: tab === t.id ? '2px solid #3b82f6' : '2px solid transparent',
                  color: tab === t.id ? '#60a5fa' : '#64748b',
                  fontWeight: tab === t.id ? 600 : 400,
                  transition: 'all 0.15s',
                }}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
            {tab === 'attribution' && (
              <AttributionPanel result={selectedAttribution} />
            )}

            {tab === 'forecast' && (
              <ForecastChart forecasts={forecasts} />
            )}

            {tab === 'enforcement' && (
              <EnforcementPanel plan={enforcement} />
            )}

            {tab === 'advisories' && (
              <AdvisoryPanel advisories={advisories} crossCityRecs={crossCity} />
            )}

            {tab === 'trace' && (
              <AgentTrace trace={trace} completedAgents={completedAgents} />
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{
        padding: '6px 20px', background: '#060c18',
        borderTop: '1px solid #1e293b', fontSize: 11,
        color: '#334155', display: 'flex', justifyContent: 'space-between',
      }}>
        <span>PRANAVYU · ET AI Hackathon 2026 · Multi-Agent Urban Air Quality Intelligence</span>
        <span>Data: CPCB CAAQMS · Sentinel-5P · IMD · OpenAQ</span>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: #0a0f1a; }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 2px; }
        .pranavyu-popup .leaflet-popup-content-wrapper {
          background: #0f172a !important;
          border: 1px solid #334155 !important;
          color: #e2e8f0 !important;
        }
        .pranavyu-popup .leaflet-popup-tip { background: #0f172a !important; }
      `}</style>
    </div>
  )
}
