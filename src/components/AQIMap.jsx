import React, { useEffect, useRef } from 'react'
import { aqiMapColor, aqiLabel, wardName } from '../utils/colors'

// Leaflet is loaded via CDN in index.html
// We use it via window.L

export default function AQIMap({ readings = [], attributionResults = [], selectedWard, onWardSelect }) {
  const mapRef = useRef(null)
  const leafletMap = useRef(null)
  const circlesRef = useRef([])

  useEffect(() => {
    if (!window.L) return
    if (leafletMap.current) return // already initialized

    leafletMap.current = window.L.map(mapRef.current, {
      center: [12.9716, 77.5946],
      zoom: 11,
      zoomControl: true,
    })

    window.L.tileLayer(
      'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
      {
        attribution: '© OpenStreetMap © CARTO',
        maxZoom: 18,
      }
    ).addTo(leafletMap.current)
  }, [])

  // Update circles when readings change
  useEffect(() => {
    if (!leafletMap.current || !window.L) return

    // Remove old circles
    circlesRef.current.forEach(c => c.remove())
    circlesRef.current = []

    readings.forEach(r => {
      if (!r.lat || !r.lon || !r.aqi) return
      const name = wardName(r.station_name)
      const color = aqiMapColor(r.aqi)
      const isSelected = selectedWard === r.ward_id

      const circle = window.L.circleMarker([r.lat, r.lon], {
        radius: isSelected ? 22 : 16,
        fillColor: color,
        color: isSelected ? '#fff' : color,
        weight: isSelected ? 2 : 1,
        opacity: 0.9,
        fillOpacity: isSelected ? 0.95 : 0.75,
      }).addTo(leafletMap.current)

      // Find attribution for this ward
      const attr = (attributionResults || []).find(a => a.ward_id === r.ward_id)
      const attrText = attr
        ? `<div style="margin-top:6px;font-size:11px;color:#ccc">${attr.dominant_source}: ${Math.round((attr.attributions[0]?.contribution_fraction || 0) * 100)}% | Conf: ${Math.round((attr.overall_confidence || 0) * 100)}%</div>`
        : ''

      circle.bindPopup(`
        <div style="font-family:system-ui;min-width:180px">
          <div style="font-weight:600;font-size:14px;margin-bottom:4px">${name}</div>
          <div style="font-size:22px;font-weight:700;color:${color}">${Math.round(r.aqi)}</div>
          <div style="font-size:11px;color:#aaa;margin-bottom:4px">AQI — ${aqiLabel(r.aqi)}</div>
          <div style="font-size:11px;color:#ccc">PM2.5: ${r.pm25 ? r.pm25.toFixed(1) : '—'} μg/m³</div>
          ${attrText}
        </div>
      `, { className: 'pranavyu-popup' })

      circle.on('click', () => {
        if (onWardSelect) onWardSelect(r.ward_id)
      })

      circlesRef.current.push(circle)
    })
  }, [readings, selectedWard, attributionResults])

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={mapRef} style={{ width: '100%', height: '100%', borderRadius: '8px' }} />
      {/* Legend */}
      <div style={{
        position: 'absolute', bottom: 16, left: 16, zIndex: 1000,
        background: 'rgba(10,15,26,0.92)', border: '1px solid #1e293b',
        borderRadius: 8, padding: '10px 14px',
      }}>
        <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 6, fontWeight: 600 }}>AQI SCALE</div>
        {[
          ['≤50', '#22c55e', 'Good'],
          ['≤100', '#3b82f6', 'Satisfactory'],
          ['≤200', '#eab308', 'Moderate'],
          ['≤300', '#f97316', 'Poor'],
          ['≤400', '#ef4444', 'Very Poor'],
          ['>400', '#a855f7', 'Severe'],
        ].map(([range, color, label]) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: color, flexShrink: 0 }} />
            <span style={{ fontSize: 11, color: '#94a3b8' }}>{range} — {label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
