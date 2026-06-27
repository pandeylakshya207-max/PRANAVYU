import React, { useState } from 'react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { riskColor } from '../utils/colors'

function aqi_color(aqi) {
  if (aqi <= 50)  return '#4ade80'
  if (aqi <= 100) return '#60a5fa'
  if (aqi <= 200) return '#fbbf24'
  if (aqi <= 300) return '#fb923c'
  if (aqi <= 400) return '#f87171'
  return '#c084fc'
}

function fmt_hour(ts) {
  const d = new Date(ts)
  return `${d.getHours().toString().padStart(2,'0')}:00`
}

function fmt_day(ts) {
  const d = new Date(ts)
  const days = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']
  return `${days[d.getDay()]} ${fmt_hour(ts)}`
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  const aqi = payload[0]?.value
  return (
    <div style={{
      background: '#0f172a', border: '1px solid #334155',
      borderRadius: 8, padding: '10px 14px', fontSize: 12,
    }}>
      <div style={{ color: '#94a3b8', marginBottom: 4 }}>{label}</div>
      <div style={{ color: aqi_color(aqi), fontWeight: 700, fontSize: 18 }}>
        AQI {aqi?.toFixed(0)}
      </div>
      {payload[1] && (
        <div style={{ color: '#64748b', fontSize: 11, marginTop: 2 }}>
          Range: {payload[1]?.value?.toFixed(0)} – {payload[2]?.value?.toFixed(0)}
        </div>
      )}
    </div>
  )
}

export default function ForecastChart({ forecasts = [] }) {
  const [selectedWard, setSelectedWard] = useState(null)

  const ward = selectedWard
    ? forecasts.find(f => f.ward_id === selectedWard)
    : forecasts[0]

  const chartData = (ward?.forecast_24h || []).map(p => ({
    time: fmt_day(p.timestamp),
    aqi: Math.round(p.predicted_aqi),
    lower: Math.round(p.confidence_lower),
    upper: Math.round(p.confidence_upper),
    factor: p.dominant_factor,
  }))

  const peakAqi = ward?.peak_aqi || 0
  const lineColor = aqi_color(peakAqi)

  return (
    <div>
      {/* Ward selector */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
        {forecasts.slice(0, 8).map(f => (
          <button
            key={f.ward_id}
            onClick={() => setSelectedWard(f.ward_id)}
            style={{
              padding: '4px 10px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
              background: (ward?.ward_id === f.ward_id) ? '#1e40af' : '#1e293b',
              color: (ward?.ward_id === f.ward_id) ? '#bfdbfe' : '#94a3b8',
              border: (ward?.ward_id === f.ward_id) ? '1px solid #3b82f6' : '1px solid #334155',
              transition: 'all 0.15s',
            }}
          >
            {f.ward_name}
          </button>
        ))}
      </div>

      {ward && (
        <>
          {/* Ward summary */}
          <div style={{
            display: 'flex', gap: 16, marginBottom: 16,
            padding: '10px 14px', background: '#0f172a',
            borderRadius: 8, border: '1px solid #1e293b',
          }}>
            <div>
              <div style={{ fontSize: 11, color: '#64748b' }}>PEAK AQI (72h)</div>
              <div style={{ fontSize: 26, fontWeight: 800, color: lineColor }}>
                {peakAqi?.toFixed(0)}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: '#64748b' }}>HEALTH RISK</div>
              <div style={{ fontSize: 16, fontWeight: 700, color: riskColor(ward.health_risk) }}>
                {ward.health_risk}
              </div>
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 11, color: '#64748b', marginBottom: 4 }}>KEY DRIVERS</div>
              <div style={{ fontSize: 11, color: '#94a3b8', lineHeight: 1.5 }}>
                {(ward.key_drivers || []).slice(0, 2).join(' · ')}
              </div>
            </div>
          </div>

          {/* Chart */}
          <div style={{ height: 200 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: -10 }}>
                <defs>
                  <linearGradient id="aqiGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={lineColor} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={lineColor} stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#475569' }} interval={5} />
                <YAxis tick={{ fontSize: 10, fill: '#475569' }} domain={['auto', 'auto']} />
                <Tooltip content={<CustomTooltip />} />
                {/* Threshold lines */}
                <ReferenceLine y={200} stroke="#f97316" strokeDasharray="4 2" label={{ value:'Poor', fill:'#f97316', fontSize:10 }} />
                <ReferenceLine y={300} stroke="#ef4444" strokeDasharray="4 2" label={{ value:'Very Poor', fill:'#ef4444', fontSize:10 }} />
                {/* Confidence band */}
                <Area type="monotone" dataKey="upper" stroke="none" fill={lineColor} fillOpacity={0.08} />
                <Area type="monotone" dataKey="lower" stroke="none" fill="#0a0f1a" fillOpacity={1} />
                {/* Main line */}
                <Area
                  type="monotone" dataKey="aqi"
                  stroke={lineColor} strokeWidth={2}
                  fill="url(#aqiGrad)"
                  dot={false} activeDot={{ r: 4, fill: lineColor }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div style={{ fontSize: 11, color: '#475569', marginTop: 4, textAlign: 'right' }}>
            24-hour forecast · shaded area = confidence interval
          </div>
        </>
      )}
    </div>
  )
}
