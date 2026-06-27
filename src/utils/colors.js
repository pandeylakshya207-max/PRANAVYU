export const AQI_COLORS = {
  Good:          { bg:'#1a5c2e', text:'#4ade80', badge:'#16a34a' },
  Satisfactory:  { bg:'#1e3a5f', text:'#60a5fa', badge:'#2563eb' },
  Moderate:      { bg:'#4a3500', text:'#fbbf24', badge:'#d97706' },
  Poor:          { bg:'#5c2500', text:'#fb923c', badge:'#ea580c' },
  'Very Poor':   { bg:'#5c0a1a', text:'#f87171', badge:'#dc2626' },
  Severe:        { bg:'#3b0070', text:'#c084fc', badge:'#9333ea' },
}

export function aqiColor(aqi) {
  if (aqi <= 50)  return AQI_COLORS['Good']
  if (aqi <= 100) return AQI_COLORS['Satisfactory']
  if (aqi <= 200) return AQI_COLORS['Moderate']
  if (aqi <= 300) return AQI_COLORS['Poor']
  if (aqi <= 400) return AQI_COLORS['Very Poor']
  return AQI_COLORS['Severe']
}

export function aqiLabel(aqi) {
  if (aqi <= 50)  return 'Good'
  if (aqi <= 100) return 'Satisfactory'
  if (aqi <= 200) return 'Moderate'
  if (aqi <= 300) return 'Poor'
  if (aqi <= 400) return 'Very Poor'
  return 'Severe'
}

export function riskColor(risk) {
  const map = { Low:'#4ade80', Moderate:'#fbbf24', High:'#fb923c', 'Very High':'#f87171', Severe:'#c084fc' }
  return map[risk] || '#888'
}

// Map AQI to Leaflet circle color for heatmap
export function aqiMapColor(aqi) {
  if (aqi <= 50)  return '#22c55e'
  if (aqi <= 100) return '#3b82f6'
  if (aqi <= 200) return '#eab308'
  if (aqi <= 300) return '#f97316'
  if (aqi <= 400) return '#ef4444'
  return '#a855f7'
}

export function wardName(stationName) {
  return stationName?.replace(' Monitoring Station', '') || 'Unknown'
}
