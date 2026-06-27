import React, { useState } from 'react'
import { riskColor } from '../utils/colors'

const LANG_FLAGS = { en: '🇬🇧', kn: '🇮🇳', ta: '🇮🇳', hi: '🇮🇳', bn: '🇮🇳' }
const LANG_NAMES = { en: 'English', kn: 'ಕನ್ನಡ', ta: 'தமிழ்', hi: 'हिंदी' }

function risk_bg(risk) {
  const m = { Low:'#14532d', Moderate:'#451a03', High:'#431407', 'Very High':'#450a0a', Severe:'#2e1065' }
  return m[risk] || '#1e293b'
}

export default function AdvisoryPanel({ advisories = [], crossCityRecs = [] }) {
  const [lang, setLang] = useState('en')
  const [tab, setTab] = useState('advisories')

  const filtered = advisories.filter(a => a.language === lang)
  const langs = [...new Set(advisories.map(a => a.language))]

  return (
    <div>
      {/* Tab switcher */}
      <div style={{ display: 'flex', gap: 2, marginBottom: 14 }}>
        {['advisories','cross-city'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: '5px 12px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
            background: tab === t ? '#1e3a5f' : 'transparent',
            color: tab === t ? '#60a5fa' : '#64748b',
            border: tab === t ? '1px solid #1d4ed8' : '1px solid transparent',
          }}>
            {t === 'advisories' ? '📢 Advisories' : '🏙️ Cross-City Intel'}
          </button>
        ))}
      </div>

      {tab === 'advisories' && (
        <>
          {/* Language selector */}
          <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
            {langs.map(l => (
              <button key={l} onClick={() => setLang(l)} style={{
                padding: '3px 10px', borderRadius: 20, fontSize: 11, cursor: 'pointer',
                background: lang === l ? '#1e40af' : '#1e293b',
                color: lang === l ? '#bfdbfe' : '#94a3b8',
                border: '1px solid ' + (lang === l ? '#3b82f6' : '#334155'),
              }}>
                {LANG_FLAGS[l]} {LANG_NAMES[l] || l.toUpperCase()}
              </button>
            ))}
          </div>

          {/* Advisory cards */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {filtered.length === 0 && (
              <div style={{ color: '#475569', fontSize: 13, padding: '12px 0' }}>
                No advisories for selected language.
              </div>
            )}
            {filtered.map((a, i) => (
              <AdvisoryCard key={i} advisory={a} />
            ))}
          </div>
        </>
      )}

      {tab === 'cross-city' && (
        <CrossCityPanel recs={crossCityRecs} />
      )}
    </div>
  )
}

function AdvisoryCard({ advisory }) {
  const [expanded, setExpanded] = useState(false)
  const { ward_name, health_risk, forecast_aqi, message_short, message_full,
          recommendations = [], vulnerable_groups = [] } = advisory

  return (
    <div style={{
      padding: '10px 12px',
      background: risk_bg(health_risk),
      borderRadius: 8,
      border: `1px solid ${riskColor(health_risk)}33`,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0' }}>{ward_name}</span>
          <span style={{
            padding: '1px 7px', borderRadius: 4, fontSize: 11, fontWeight: 600,
            background: riskColor(health_risk) + '33', color: riskColor(health_risk),
          }}>
            {health_risk}
          </span>
        </div>
        <span style={{ fontSize: 14, fontWeight: 700, color: riskColor(health_risk) }}>
          AQI {forecast_aqi?.toFixed(0)}
        </span>
      </div>

      <div style={{ fontSize: 12, color: '#94a3b8', lineHeight: 1.5, marginBottom: 6 }}>
        {message_full || message_short}
      </div>

      {!expanded ? (
        <button onClick={() => setExpanded(true)} style={{
          fontSize: 11, color: '#64748b', background: 'none', border: 'none',
          cursor: 'pointer', padding: 0,
        }}>
          + Show recommendations & vulnerable groups
        </button>
      ) : (
        <div>
          {recommendations.length > 0 && (
            <div style={{ marginBottom: 6 }}>
              <div style={{ fontSize: 11, color: '#64748b', marginBottom: 3, textTransform:'uppercase', letterSpacing:0.8 }}>
                RECOMMENDATIONS
              </div>
              {recommendations.map((r, i) => (
                <div key={i} style={{ fontSize: 12, color: '#94a3b8', paddingLeft: 12, lineHeight: 1.7 }}>
                  • {r}
                </div>
              ))}
            </div>
          )}
          {vulnerable_groups.length > 0 && (
            <div>
              <div style={{ fontSize: 11, color: '#64748b', marginBottom: 3, textTransform:'uppercase', letterSpacing:0.8 }}>
                VULNERABLE POPULATIONS
              </div>
              {vulnerable_groups.map((g, i) => (
                <div key={i} style={{ fontSize: 12, color: '#f97316', paddingLeft: 12, lineHeight: 1.7 }}>
                  ⚠ {g}
                </div>
              ))}
            </div>
          )}
          <button onClick={() => setExpanded(false)} style={{
            marginTop: 6, fontSize: 11, color: '#64748b', background: 'none',
            border: 'none', cursor: 'pointer', padding: 0,
          }}>
            − Collapse
          </button>
        </div>
      )}
    </div>
  )
}

function CrossCityPanel({ recs = [] }) {
  if (!recs.length) {
    return <div style={{ color: '#475569', fontSize: 13 }}>No recommendations available.</div>
  }

  const diff_color = { Low:'#4ade80', Medium:'#fbbf24', High:'#f87171' }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {recs.map((rec, i) => (
        <div key={i} style={{
          padding: '12px 14px', background: '#0f172a',
          borderRadius: 8, border: '1px solid #1e293b',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0', flex: 1, paddingRight: 12 }}>
              {rec.recommendation}
            </span>
            <div style={{ textAlign: 'right', flexShrink: 0 }}>
              <div style={{ fontSize: 18, fontWeight: 800, color: '#4ade80' }}>
                {rec.expected_delta_aqi?.toFixed(0)} AQI
              </div>
              <div style={{ fontSize: 10, color: '#64748b' }}>expected reduction</div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <Tag label={`Difficulty: ${rec.implementation_difficulty}`}
                 color={diff_color[rec.implementation_difficulty] || '#94a3b8'} />
            <Tag label={`Evidence: ${(rec.evidence_cities || []).join(', ')}`} color="#60a5fa" />
          </div>

          {(rec.supporting_outcomes || []).map((o, j) => (
            <div key={j} style={{
              marginTop: 8, padding: '6px 10px', background: '#0a0f1a',
              borderRadius: 6, fontSize: 11, color: '#64748b',
            }}>
              📍 {o.city}: {o.policy_name} → AQI {o.aqi_before} → {o.aqi_after}
              ({o.delta_aqi > 0 ? '+' : ''}{o.delta_aqi} | {o.confidence} confidence)
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}

function Tag({ label, color }) {
  return (
    <span style={{
      padding: '2px 8px', borderRadius: 4, fontSize: 11,
      background: color + '22', color: color,
      border: '1px solid ' + color + '44',
    }}>
      {label}
    </span>
  )
}
