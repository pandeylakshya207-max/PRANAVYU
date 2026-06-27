import React from 'react'
import { riskColor } from '../utils/colors'

const CAT_ICONS = {
  industrial: '🏭',
  construction: '🏗️',
  traffic: '🚗',
  burning: '🔥',
  other: '💨',
}

const CAT_COLORS = {
  industrial:   '#ef4444',
  construction: '#f97316',
  traffic:      '#eab308',
  burning:      '#a855f7',
  other:        '#94a3b8',
}

export default function AttributionPanel({ result }) {
  if (!result) {
    return (
      <div style={{ padding: 24, color: '#64748b', textAlign: 'center' }}>
        <div style={{ fontSize: 32, marginBottom: 8 }}>🗺️</div>
        <div>Click a ward on the map to see source attribution</div>
      </div>
    )
  }

  const { ward_name, current_aqi, attributions = [], overall_confidence, explanation, dominant_source, timestamp } = result

  return (
    <div style={{ padding: '0 4px' }}>
      {/* Ward header */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 4 }}>
          <span style={{ fontSize: 22, fontWeight: 700, color: '#f1f5f9' }}>{ward_name}</span>
          <span style={{ fontSize: 13, color: '#64748b' }}>
            {timestamp ? new Date(timestamp).toLocaleTimeString() : ''}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 36, fontWeight: 800, color: aqi_color(current_aqi) }}>
            {Math.round(current_aqi)}
          </span>
          <span style={{ fontSize: 13, color: '#94a3b8' }}>AQI</span>
          <span style={{
            marginLeft: 6, padding: '2px 8px', borderRadius: 4, fontSize: 12, fontWeight: 600,
            background: aqi_bg(current_aqi), color: aqi_color(current_aqi),
          }}>
            {aqi_label(current_aqi)}
          </span>
        </div>
      </div>

      {/* Confidence badge */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14,
        padding: '6px 10px', background: '#0f172a', borderRadius: 6,
        border: '1px solid #1e293b',
      }}>
        <span style={{ fontSize: 12, color: '#94a3b8' }}>Attribution confidence:</span>
        <ConfidenceBar value={overall_confidence || 0} />
        <span style={{ fontSize: 13, fontWeight: 700, color: conf_color(overall_confidence) }}>
          {Math.round((overall_confidence || 0) * 100)}%
        </span>
      </div>

      {/* Source breakdown */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
          POLLUTION SOURCE BREAKDOWN
        </div>
        {attributions.map((attr, i) => (
          <AttributionBar key={i} attr={attr} />
        ))}
      </div>

      {/* Explanation */}
      <div style={{
        padding: '10px 12px', background: '#0f172a',
        borderRadius: 6, border: '1px solid #1e293b',
      }}>
        <div style={{ fontSize: 11, color: '#64748b', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 0.8 }}>
          AGENT REASONING
        </div>
        <div style={{ fontSize: 12, color: '#94a3b8', lineHeight: 1.6 }}>
          {explanation}
        </div>
      </div>
    </div>
  )
}

function AttributionBar({ attr }) {
  const { source_category, contribution_fraction, primary_sources = [] } = attr
  const pct = Math.round((contribution_fraction || 0) * 100)
  const color = CAT_COLORS[source_category] || '#94a3b8'
  const icon = CAT_ICONS[source_category] || '💨'

  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 14 }}>{icon}</span>
          <span style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0', textTransform: 'capitalize' }}>
            {source_category}
          </span>
        </div>
        <span style={{ fontSize: 14, fontWeight: 700, color }}>{pct}%</span>
      </div>
      {/* Bar */}
      <div style={{ height: 6, background: '#1e293b', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{
          height: '100%', width: `${pct}%`, background: color,
          borderRadius: 3, transition: 'width 0.6s ease',
        }} />
      </div>
      {primary_sources.length > 0 && (
        <div style={{ fontSize: 11, color: '#64748b', marginTop: 3, paddingLeft: 20 }}>
          {primary_sources.join(', ')}
        </div>
      )}
    </div>
  )
}

function ConfidenceBar({ value }) {
  return (
    <div style={{ flex: 1, height: 4, background: '#1e293b', borderRadius: 2, overflow: 'hidden' }}>
      <div style={{
        height: '100%', width: `${Math.round(value * 100)}%`,
        background: conf_color(value), borderRadius: 2, transition: 'width 0.5s ease',
      }} />
    </div>
  )
}

function conf_color(v) {
  if (v >= 0.8) return '#4ade80'
  if (v >= 0.6) return '#fbbf24'
  return '#f87171'
}

function aqi_color(aqi) {
  if (aqi <= 50)  return '#4ade80'
  if (aqi <= 100) return '#60a5fa'
  if (aqi <= 200) return '#fbbf24'
  if (aqi <= 300) return '#fb923c'
  if (aqi <= 400) return '#f87171'
  return '#c084fc'
}

function aqi_bg(aqi) {
  if (aqi <= 50)  return '#14532d'
  if (aqi <= 100) return '#1e3a5f'
  if (aqi <= 200) return '#451a03'
  if (aqi <= 300) return '#431407'
  if (aqi <= 400) return '#450a0a'
  return '#2e1065'
}

function aqi_label(aqi) {
  if (aqi <= 50)  return 'Good'
  if (aqi <= 100) return 'Satisfactory'
  if (aqi <= 200) return 'Moderate'
  if (aqi <= 300) return 'Poor'
  if (aqi <= 400) return 'Very Poor'
  return 'Severe'
}
