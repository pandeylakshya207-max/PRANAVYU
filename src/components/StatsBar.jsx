import React from 'react'

export default function StatsBar({ summary = {}, lastUpdated }) {
  const {
    avg_aqi = 0, max_aqi = 0, wards_monitored = 0,
    high_risk_wards = 0, enforcement_actions_pending = 0,
    advisories_dispatched = 0, estimated_aqi_reduction_possible = 0,
  } = summary

  const stats = [
    { label: 'AVG AQI',          value: avg_aqi?.toFixed(0),    color: aqi_color(avg_aqi),  icon: '🌫️' },
    { label: 'MAX AQI',          value: max_aqi?.toFixed(0),    color: aqi_color(max_aqi),  icon: '⚠️' },
    { label: 'WARDS MONITORED',  value: wards_monitored,        color: '#60a5fa',            icon: '📍' },
    { label: 'HIGH RISK WARDS',  value: high_risk_wards,        color: '#f87171',            icon: '🔴' },
    { label: 'ENFORCEMENT OPS',  value: enforcement_actions_pending, color: '#fb923c',       icon: '🚔' },
    { label: 'ADVISORIES SENT',  value: advisories_dispatched,  color: '#fbbf24',            icon: '📢' },
    { label: 'AQI REDUCTION',    value: `−${estimated_aqi_reduction_possible?.toFixed(0)}`, color: '#4ade80', icon: '📉' },
  ]

  return (
    <div style={{
      display: 'flex', gap: 0, flexWrap: 'nowrap', overflowX: 'auto',
      background: '#0d1424', borderBottom: '1px solid #1e293b',
      padding: '0 16px',
    }}>
      {stats.map((s, i) => (
        <div key={i} style={{
          padding: '10px 20px', flexShrink: 0,
          borderRight: '1px solid #1e293b',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: 10, color: '#475569', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 2 }}>
            {s.icon} {s.label}
          </div>
          <div style={{ fontSize: 20, fontWeight: 800, color: s.color, lineHeight: 1 }}>
            {s.value}
          </div>
        </div>
      ))}
      {lastUpdated && (
        <div style={{ padding: '10px 20px', flexShrink: 0, textAlign: 'center', marginLeft: 'auto' }}>
          <div style={{ fontSize: 10, color: '#334155', textTransform: 'uppercase', letterSpacing: 0.8 }}>LAST REFRESH</div>
          <div style={{ fontSize: 12, color: '#475569' }}>
            {lastUpdated.toLocaleTimeString()}
          </div>
        </div>
      )}
    </div>
  )
}

function aqi_color(aqi) {
  if (aqi <= 50)  return '#4ade80'
  if (aqi <= 100) return '#60a5fa'
  if (aqi <= 200) return '#fbbf24'
  if (aqi <= 300) return '#fb923c'
  if (aqi <= 400) return '#f87171'
  return '#c084fc'
}
