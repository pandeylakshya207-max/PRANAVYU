import { useState, useEffect, useCallback } from 'react'

const BASE = import.meta.env.DEV ? '' : ''

export function useDashboard(city = 'Bengaluru') {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)

  const fetch_data = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${BASE}/api/dashboard/${encodeURIComponent(city)}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      setData(json)
      setLastUpdated(new Date())
    } catch (e) {
      setError(e.message)
      // Load demo data so UI still works
      setData(DEMO_DATA)
    } finally {
      setLoading(false)
    }
  }, [city])

  useEffect(() => {
    fetch_data()
    const interval = setInterval(fetch_data, 60000) // refresh every 60s
    return () => clearInterval(interval)
  }, [fetch_data])

  return { data, loading, error, lastUpdated, refresh: fetch_data }
}

export function useTrace(city = 'Bengaluru') {
  const [trace, setTrace] = useState([])
  useEffect(() => {
    fetch(`${BASE}/api/trace/${encodeURIComponent(city)}`)
      .then(r => r.json())
      .then(d => setTrace(d.trace || []))
      .catch(() => {})
  }, [city])
  return trace
}

// ─── Demo data for offline/demo mode ────────────────────────────────────────

export const DEMO_DATA = {
  city: 'Bengaluru',
  generated_at: new Date().toISOString(),
  summary: {
    avg_aqi: 162,
    max_aqi: 247,
    wards_monitored: 12,
    high_risk_wards: 8,
    enforcement_actions_pending: 7,
    advisories_dispatched: 12,
    estimated_aqi_reduction_possible: 67,
  },
  readings: [
    { ward_id:'BLR_001', station_name:'Whitefield Monitoring Station',      lat:12.9698, lon:77.7499, aqi:187, aqi_category:'Poor',      pm25:78.5 },
    { ward_id:'BLR_002', station_name:'HSR Layout Monitoring Station',      lat:12.9116, lon:77.6389, aqi:310, aqi_category:'Very Poor', pm25:130.2 },
    { ward_id:'BLR_003', station_name:'Peenya Monitoring Station',          lat:13.0284, lon:77.5194, aqi:247, aqi_category:'Very Poor', pm25:103.7 },
    { ward_id:'BLR_004', station_name:'Marathahalli Monitoring Station',    lat:12.9591, lon:77.6974, aqi:155, aqi_category:'Moderate',  pm25:65.1 },
    { ward_id:'BLR_005', station_name:'Koramangala Monitoring Station',     lat:12.9352, lon:77.6245, aqi:118, aqi_category:'Moderate',  pm25:49.6 },
    { ward_id:'BLR_006', station_name:'Yelahanka Monitoring Station',       lat:13.1005, lon:77.5963, aqi:98,  aqi_category:'Satisfactory', pm25:41.2 },
    { ward_id:'BLR_007', station_name:'Bellandur Monitoring Station',       lat:12.9259, lon:77.6746, aqi:142, aqi_category:'Moderate',  pm25:59.6 },
    { ward_id:'BLR_008', station_name:'Rajajinagar Monitoring Station',     lat:12.9954, lon:77.5568, aqi:195, aqi_category:'Poor',      pm25:81.9 },
    { ward_id:'BLR_009', station_name:'Electronic City Monitoring Station', lat:12.8399, lon:77.6770, aqi:105, aqi_category:'Moderate',  pm25:44.1 },
    { ward_id:'BLR_010', station_name:'Hebbal Monitoring Station',          lat:13.0358, lon:77.5970, aqi:138, aqi_category:'Moderate',  pm25:57.9 },
    { ward_id:'BLR_011', station_name:'Indiranagar Monitoring Station',     lat:12.9784, lon:77.6408, aqi:112, aqi_category:'Moderate',  pm25:47.0 },
    { ward_id:'BLR_012', station_name:'Kadugodi Monitoring Station',        lat:12.9935, lon:77.7571, aqi:168, aqi_category:'Poor',      pm25:70.6 },
  ],
  attribution_results: [
    {
      ward_id:'BLR_002', ward_name:'HSR Layout', current_aqi:310, dominant_source:'construction',
      overall_confidence:0.81,
      explanation:'HSR Layout AQI is 310 (Very Poor). Morning rush with 4.2 m/s NE winds: 61% construction dust from HSR Layout Apartment Complex, 24% traffic from Marathahalli Junction, 15% industrial from Rajajinagar Foundry.',
      attributions:[
        {source_category:'construction', contribution_fraction:0.61, confidence:0.81, primary_sources:['HSR Layout Apartment Complex']},
        {source_category:'traffic',      contribution_fraction:0.24, confidence:0.74, primary_sources:['Marathahalli Junction']},
        {source_category:'industrial',   contribution_fraction:0.15, confidence:0.68, primary_sources:['Rajajinagar Foundry']},
      ]
    },
    {
      ward_id:'BLR_003', ward_name:'Peenya', current_aqi:247, dominant_source:'industrial',
      overall_confidence:0.88,
      explanation:'Peenya AQI is 247 (Very Poor). Night-time with 2.1 m/s SW winds: 72% industrial from Peenya Cement Plant A and Steel Rolling Mill, 18% traffic from Tumkur Road Corridor, 10% other.',
      attributions:[
        {source_category:'industrial',   contribution_fraction:0.72, confidence:0.88, primary_sources:['Peenya Cement Batching Plant A','Peenya Steel Rolling Mill']},
        {source_category:'traffic',      contribution_fraction:0.18, confidence:0.75, primary_sources:['Tumkur Road Corridor']},
        {source_category:'other',        contribution_fraction:0.10, confidence:0.60, primary_sources:[]},
      ]
    },
  ],
  enforcement_plan: {
    city:'Bengaluru',
    total_estimated_aqi_reduction:67,
    actions:[
      {
        action_id:'ACT_001', priority_rank:1,
        violation_probability:0.91, optimal_inspection_start:22, optimal_inspection_end:3,
        contributing_aqi_ward:'Peenya', estimated_aqi_impact:42.1, dispatched:false,
        evidence_summary:'Source: Rajajinagar Foundry (Industrial) | Permit status: EXPIRED | Contribution to Peenya: 15% of AQI 247 | Historical violation rate: 85% | Typical violation window: 21:00–02:00 | Violation probability NOW: 91%',
        source:{ name:'Rajajinagar Foundry', category:'industrial', lat:12.9960, lon:77.5560, ward_id:'BLR_008', permit_status:'expired' }
      },
      {
        action_id:'ACT_002', priority_rank:2,
        violation_probability:0.78, optimal_inspection_start:22, optimal_inspection_end:3,
        contributing_aqi_ward:'Peenya', estimated_aqi_impact:31.4, dispatched:false,
        evidence_summary:'Source: Peenya Cement Batching Plant A (Industrial) | Permit status: VALID | Historical violation rate: 72% | Violation probability: 78%',
        source:{ name:'Peenya Cement Batching Plant A', category:'industrial', lat:13.0290, lon:77.5185, ward_id:'BLR_003', permit_status:'valid' }
      },
      {
        action_id:'ACT_003', priority_rank:3,
        violation_probability:0.64, optimal_inspection_start:22, optimal_inspection_end:4,
        contributing_aqi_ward:'Kadugodi', estimated_aqi_impact:28.8, dispatched:false,
        evidence_summary:'Source: Kadugodi Landfill (Burning) | Permit status: NONE | Historical violation rate: 90% | Violation probability: 64%',
        source:{ name:'Kadugodi Landfill', category:'burning', lat:12.9940, lon:77.7560, ward_id:'BLR_012', permit_status:'none' }
      },
    ]
  },
  advisories_en:[
    { ward_id:'BLR_002', ward_name:'HSR Layout', health_risk:'Very High', language:'en', forecast_aqi:310,
      message_short:'PRANAVYU Alert — HSR Layout: AQI forecast 310 (Very High risk). Stay indoors with windows closed. Wear N95 mask if going out.',
      message_full:'Air quality is Very Poor. Stay indoors with windows closed. Wear N95 mask if going outside. Postpone school sports activities.',
      recommendations:['Stay indoors with windows closed','Wear N95 mask if going out','Postpone school sports','Seek medical care for breathing issues'],
      vulnerable_groups:['8 schools at risk — advise indoor activities','4 hospitals nearby — alert respiratory patients'] },
    { ward_id:'BLR_003', ward_name:'Peenya', health_risk:'Very High', language:'en', forecast_aqi:247,
      message_short:'PRANAVYU Alert — Peenya: AQI forecast 247 (Very High risk). Industrial emissions high. Avoid outdoor exercise.',
      message_full:'Air quality is Very Poor. Industrial emissions elevated. Stay indoors with windows closed.',
      recommendations:['Avoid outdoor exercise','Keep windows closed','N95 mask mandatory outdoors'],
      vulnerable_groups:['6 schools at risk','High density of outdoor workers — distribute N95 masks'] },
  ],
  ward_forecasts:[
    { ward_id:'BLR_002', ward_name:'HSR Layout', peak_aqi:310, health_risk:'Very High',
      key_drivers:['Active construction activity in ward','Morning traffic peak','Low wind speed reducing dispersal','Nocturnal boundary layer compression'],
      forecast_24h: Array.from({length:24},(_,i)=>({
        timestamp: new Date(Date.now()+i*3600000).toISOString(),
        predicted_aqi: 280 + Math.sin(i*0.4)*40 + Math.random()*15,
        pm25_forecast: 120 + Math.sin(i*0.4)*20,
        confidence_lower: 250, confidence_upper: 340,
        dominant_factor: i<6?'nighttime stability':i<10?'morning traffic':'mixed urban'
      }))
    },
    { ward_id:'BLR_003', ward_name:'Peenya', peak_aqi:247, health_risk:'High',
      key_drivers:['Proximity to Peenya industrial cluster','Night-time industrial operations','Low mixing height'],
      forecast_24h: Array.from({length:24},(_,i)=>({
        timestamp: new Date(Date.now()+i*3600000).toISOString(),
        predicted_aqi: 200 + (i>20||i<4?40:0) + Math.random()*20,
        pm25_forecast: 85 + Math.sin(i*0.3)*15,
        confidence_lower: 175, confidence_upper: 280,
        dominant_factor: i>=21||i<=3?'industrial night operations':'mixed urban'
      }))
    },
  ],
  cross_city_recommendations:[
    { recommendation:'Mandatory anti-dust measures for construction sites (mist cannons, debris netting, wheel washers)',
      policy_type:'construction_dust', expected_delta_aqi:-27, implementation_difficulty:'Medium',
      evidence_cities:['Pune','Chennai'],
      supporting_outcomes:[
        {city:'Pune', policy_name:'Mandatory mist cannon on construction sites', aqi_before:175, aqi_after:148, delta_aqi:-27, confidence:'High'},
        {city:'Chennai', policy_name:'Construction activity ban 6AM-10AM', aqi_before:155, aqi_after:132, delta_aqi:-23, confidence:'High'},
      ]},
    { recommendation:'Real-time CCTV + continuous emission monitoring at industrial units',
      policy_type:'industrial_monitoring', expected_delta_aqi:-33, implementation_difficulty:'Low',
      evidence_cities:['Hyderabad'],
      supporting_outcomes:[
        {city:'Hyderabad', policy_name:'Real-time CCTV monitoring at industrial units', aqi_before:185, aqi_after:152, delta_aqi:-33, confidence:'High'},
      ]},
  ],
  agent_trace:[
    {agent:'data_ingestion',        timestamp:new Date(Date.now()-5000).toISOString(), readings_count:12, mode:'synthetic'},
    {agent:'attribution_agent',     timestamp:new Date(Date.now()-4500).toISOString(), wards_processed:12},
    {agent:'forecast_agent',        timestamp:new Date(Date.now()-4000).toISOString(), wards_forecasted:12, forecast_hours:72},
    {agent:'enforcement_agent',     timestamp:new Date(Date.now()-3500).toISOString(), actions_generated:7},
    {agent:'citizen_advisory_agent',timestamp:new Date(Date.now()-3000).toISOString(), advisories_generated:28},
    {agent:'cross_city_agent',      timestamp:new Date(Date.now()-2500).toISOString(), recommendations_generated:2},
    {agent:'synthesizer',           timestamp:new Date(Date.now()-2000).toISOString(), agents_completed:6},
  ]
}
