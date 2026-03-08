import { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, ScatterChart, Scatter, ZAxis,
  LineChart, Line
} from 'recharts'

const COLORS = ['#2563eb', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316']
const TIER_COLORS = { budget: '#10b981', mid: '#2563eb', upper_mid: '#f59e0b', premium: '#ef4444' }
const TIER_LABELS = { budget: 'Budget', mid: 'Mid-Range', upper_mid: 'Upper Mid', premium: 'Premium' }
const formatRM = (v) => v ? `RM ${Number(v).toLocaleString()}` : 'N/A'
const formatPSF = (v) => v ? `RM ${Number(v).toFixed(0)} psf` : 'N/A'
const formatRentPSF = (v) => v ? `RM ${Number(v).toFixed(2)} psf` : 'N/A'

// Amenity icons (emoji-based for simplicity)
const AMENITY_ICONS = {
  'MRT/LRT': '\u{1F688}', KTM: '\u{1F686}', Bus: '\u{1F68C}',
  Supermarket: '\u{1F6D2}', 'Food Court': '\u{1F35C}',
  'Shopping Mall': '\u{1F6CD}\uFE0F', School: '\u{1F3EB}', Hospital: '\u{1F3E5}'
}

export default function Dashboard({ data }) {
  const [activeTab, setActiveTab] = useState('overview')
  const properties = data.properties || {}
  const regions = data.regions || {}

  // Separate targets from comparables
  const targets = Object.entries(properties).filter(([, p]) => p.info?.is_target)
  const comparables = Object.entries(properties).filter(([, p]) => !p.info?.is_target)

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>Klang Valley Property Analysis</h1>
          <p className="subtitle">Bamboo Hills & Old Klang Road Investment Dashboard</p>
          <span className="last-updated">
            Last updated: {new Date(data.last_updated).toLocaleString()}
          </span>
        </div>
      </header>

      <nav className="tabs">
        {[
          { id: 'overview', label: 'Overview' },
          { id: 'bamboo', label: 'Bamboo Hills' },
          { id: 'okr', label: 'Old Klang Road' },
          { id: 'compare', label: 'Compare' },
          { id: 'trends', label: 'Trends' },
          { id: 'transactions', label: 'Transactions' },
          { id: 'market', label: 'Market Data' },
        ].map(tab => (
          <button
            key={tab.id}
            className={`tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="dashboard-content">
        {activeTab === 'overview' && <OverviewTab data={data} />}
        {activeTab === 'bamboo' && <RegionTab data={data} regionName="Bamboo Hills" />}
        {activeTab === 'okr' && <RegionTab data={data} regionName="Old Klang Road" />}
        {activeTab === 'compare' && <CompareTab data={data} />}
        {activeTab === 'trends' && <TrendsTab />}
        {activeTab === 'transactions' && <TransactionsTab data={data} />}
        {activeTab === 'market' && <MarketTab data={data} />}
      </main>

      <footer className="dashboard-footer">
        <p>Data sourced from EdgeProp, iProperty, PropertyGuru, Brickz.my, and NAPIC</p>
        <p>Scraped daily — not financial advice</p>
      </footer>
    </div>
  )
}

// ==============================
// OVERVIEW TAB
// ==============================
function OverviewTab({ data }) {
  const { properties, regions } = data

  // Group properties by price tier
  const tierGroups = {}
  for (const [name, prop] of Object.entries(properties)) {
    const tier = prop.info?.price_tier || 'mid'
    if (!tierGroups[tier]) tierGroups[tier] = []
    tierGroups[tier].push({ name, ...prop })
  }

  // PSF comparison data for all properties
  const psfCompare = Object.entries(properties)
    .filter(([, p]) => p.stats?.sale_psf_median || p.stats?.sale_psf_avg)
    .map(([name, p]) => ({
      name: name.length > 18 ? name.substring(0, 18) + '...' : name,
      fullName: name,
      PSF: p.stats?.sale_psf_median || p.stats?.sale_psf_avg || 0,
      isTarget: p.info?.is_target,
      tier: p.info?.price_tier || 'mid',
    }))
    .sort((a, b) => b.PSF - a.PSF)

  return (
    <div className="tab-content">
      {/* Target Properties */}
      <h2 className="section-title">Your Investment Properties</h2>
      <div className="card-grid">
        {Object.entries(properties)
          .filter(([, p]) => p.info?.is_target)
          .map(([name, prop]) => (
            <PropertyCard key={name} name={name} prop={prop} isTarget />
          ))}
      </div>

      {/* Price Tier Overview */}
      <div className="chart-section">
        <h2>Properties by Price Tier</h2>
        <div className="tier-grid">
          {Object.entries(TIER_LABELS).map(([tier, label]) => {
            const props = tierGroups[tier] || []
            if (props.length === 0) return null
            return (
              <div key={tier} className="tier-card" style={{ borderColor: TIER_COLORS[tier] }}>
                <div className="tier-header" style={{ background: TIER_COLORS[tier] }}>
                  <span>{label}</span>
                  <span>{data.price_tiers?.[tier]?.label || ''}</span>
                </div>
                <div className="tier-body">
                  {props.map(p => (
                    <div key={p.name} className="tier-property">
                      <span className={`prop-name ${p.info?.is_target ? 'target' : ''}`}>
                        {p.info?.is_target ? '\u2B50 ' : ''}{p.name}
                      </span>
                      <span className="prop-psf">
                        {p.stats?.sale_psf_median ? formatPSF(p.stats.sale_psf_median) : '-'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* PSF Comparison Chart */}
      {psfCompare.length > 0 && (
        <div className="chart-section">
          <h2>PSF Comparison — All Properties</h2>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={Math.max(300, psfCompare.length * 40)}>
              <BarChart data={psfCompare} layout="vertical" margin={{ left: 10, right: 30 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis type="number" tick={{ fontSize: 12 }} />
                <YAxis dataKey="name" type="category" width={160} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => formatPSF(v)} />
                <Bar dataKey="PSF" radius={[0, 4, 4, 0]}>
                  {psfCompare.map((entry, i) => (
                    <Cell
                      key={i}
                      fill={entry.isTarget ? '#ef4444' : TIER_COLORS[entry.tier] || '#94a3b8'}
                      stroke={entry.isTarget ? '#b91c1c' : 'none'}
                      strokeWidth={entry.isTarget ? 2 : 0}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="legend-custom">
            <span className="legend-item"><span className="dot" style={{ background: '#ef4444' }}></span> Your Properties</span>
            {Object.entries(TIER_COLORS).map(([tier, color]) => (
              <span key={tier} className="legend-item"><span className="dot" style={{ background: color }}></span> {TIER_LABELS[tier]}</span>
            ))}
          </div>
        </div>
      )}

      {/* Rental PSF Comparison Chart */}
      {(() => {
        const rentPsfCompare = Object.entries(properties)
          .filter(([, p]) => p.stats?.rent_psf_median)
          .map(([name, p]) => ({
            name: name.length > 18 ? name.substring(0, 18) + '...' : name,
            fullName: name,
            'Rent PSF': p.stats.rent_psf_median,
            'Rent (Median)': p.stats.rent_price_median || 0,
            Yield: p.stats.estimated_yield || 0,
            isTarget: p.info?.is_target,
            tier: p.info?.price_tier || 'mid',
          }))
          .sort((a, b) => b['Rent PSF'] - a['Rent PSF'])

        return rentPsfCompare.length > 0 ? (
          <div className="chart-section">
            <h2>Rental PSF Comparison — All Properties</h2>
            <p className="section-desc">Monthly rental price per square foot (higher = better rental income per sqft)</p>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={Math.max(280, rentPsfCompare.length * 40)}>
                <BarChart data={rentPsfCompare} layout="vertical" margin={{ left: 10, right: 30 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis type="number" tick={{ fontSize: 12 }} tickFormatter={v => `RM ${v.toFixed(1)}`} />
                  <YAxis dataKey="name" type="category" width={160} tick={{ fontSize: 11 }} />
                  <Tooltip
                    content={({ payload }) => {
                      if (!payload?.length) return null
                      const d = payload[0]?.payload
                      return (
                        <div className="custom-tooltip">
                          <p className="tooltip-name">{d?.isTarget ? '\u2B50 ' : ''}{d?.fullName}</p>
                          <p>Rent PSF: {formatRentPSF(d?.['Rent PSF'])}</p>
                          <p>Median Rent: {formatRM(d?.['Rent (Median)'])}/mo</p>
                          {d?.Yield > 0 && <p>Est. Yield: {d.Yield}%</p>}
                        </div>
                      )
                    }}
                  />
                  <Bar dataKey="Rent PSF" radius={[0, 4, 4, 0]}>
                    {rentPsfCompare.map((entry, i) => (
                      <Cell
                        key={i}
                        fill={entry.isTarget ? '#ef4444' : '#10b981'}
                        stroke={entry.isTarget ? '#b91c1c' : 'none'}
                        strokeWidth={entry.isTarget ? 2 : 0}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="legend-custom">
              <span className="legend-item"><span className="dot" style={{ background: '#ef4444' }}></span> Your Properties</span>
              <span className="legend-item"><span className="dot" style={{ background: '#10b981' }}></span> Comparables</span>
            </div>
          </div>
        ) : null
      })()}

      {/* Region Stats */}
      <div className="chart-section">
        <h2>Regional Overview</h2>
        <div className="stats-grid">
          {Object.entries(regions).map(([name, r]) => {
            const s = r.stats || {}
            return (
              <div key={name} className="region-card">
                <h3>{name}</h3>
                <div className="region-stats">
                  <StatBox label="Properties Tracked" value={r.properties?.length || 0} />
                  <StatBox label="Active Listings" value={r.total_sale_listings || 0} />
                  <StatBox label="Transactions" value={r.total_transactions || 0} />
                  <StatBox label="Median PSF" value={formatPSF(s.txn_psf_median || s.sale_psf_median)} />
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ==============================
// REGION TAB (Bamboo Hills / OKR)
// ==============================
function RegionTab({ data, regionName }) {
  const { properties, regions } = data
  const regionProps = Object.entries(properties).filter(
    ([, p]) => p.info?.region === regionName
  )
  const regionData = regions[regionName] || {}

  return (
    <div className="tab-content">
      <h2>{regionName} — All Properties</h2>

      {/* Target property first */}
      {regionProps
        .sort(([, a], [, b]) => (b.info?.is_target ? 1 : 0) - (a.info?.is_target ? 1 : 0))
        .map(([name, prop]) => (
          <PropertyDetail key={name} name={name} prop={prop} regionStats={regionData.stats} />
        ))}

      {regionProps.length === 0 && (
        <div className="empty-state">
          <h3>No properties in this region yet</h3>
          <p>Data will appear after the next scrape run.</p>
        </div>
      )}
    </div>
  )
}

// ==============================
// COMPARE TAB
// ==============================
function CompareTab({ data }) {
  const { properties } = data
  const [selectedRegion, setSelectedRegion] = useState('all')

  const allProps = Object.entries(properties)
  const filteredProps = selectedRegion === 'all'
    ? allProps
    : allProps.filter(([, p]) => p.info?.region === selectedRegion)

  // Amenity comparison
  const amenityTypes = data.amenity_types || ['MRT/LRT', 'KTM', 'Bus', 'Supermarket', 'Food Court', 'Shopping Mall', 'School', 'Hospital']

  // Price scatter data
  const scatterData = filteredProps
    .filter(([, p]) => p.stats?.sale_psf_median || p.stats?.sale_psf_avg)
    .map(([name, p]) => ({
      name,
      x: p.stats?.sale_price_median || p.stats?.sale_price_avg || 0,
      y: p.stats?.sale_psf_median || p.stats?.sale_psf_avg || 0,
      z: p.stats?.total_sale_listings || 1,
      isTarget: p.info?.is_target,
    }))

  const regionOptions = [...new Set(allProps.map(([, p]) => p.info?.region).filter(Boolean))]

  return (
    <div className="tab-content">
      <h2>Property Comparison</h2>

      {/* Region Filter */}
      <div className="filter-bar">
        <label>Region:</label>
        <select value={selectedRegion} onChange={e => setSelectedRegion(e.target.value)}>
          <option value="all">All Regions</option>
          {regionOptions.map(r => <option key={r} value={r}>{r}</option>)}
        </select>
      </div>

      {/* Comparison Table */}
      <div className="chart-section">
        <h3>Side-by-Side Comparison</h3>
        <div className="table-container">
          <table className="compare-table">
            <thead>
              <tr>
                <th>Property</th>
                <th>Tier</th>
                <th>Sale PSF</th>
                <th>Median Price</th>
                <th>Rent PSF</th>
                <th>Median Rent</th>
                <th>Yield</th>
                <th>Listings</th>
              </tr>
            </thead>
            <tbody>
              {filteredProps
                .sort(([, a], [, b]) => (b.info?.is_target ? 1 : 0) - (a.info?.is_target ? 1 : 0))
                .map(([name, p]) => {
                  const s = p.stats || {}
                  const info = p.info || {}
                  return (
                    <tr key={name} className={info.is_target ? 'target-row' : ''}>
                      <td>
                        {info.is_target && <span className="target-badge">\u2B50</span>}
                        {name}
                      </td>
                      <td>
                        <span className="tier-badge" style={{ background: TIER_COLORS[info.price_tier] || '#94a3b8' }}>
                          {TIER_LABELS[info.price_tier] || info.price_tier}
                        </span>
                      </td>
                      <td className="number">{formatPSF(s.sale_psf_median)}</td>
                      <td className="number">{formatRM(s.sale_price_median)}</td>
                      <td className="number">{s.rent_psf_median ? formatRentPSF(s.rent_psf_median) : '-'}</td>
                      <td className="number">{s.rent_price_median ? `${formatRM(s.rent_price_median)}/mo` : '-'}</td>
                      <td className="number">{s.estimated_yield ? `${s.estimated_yield}%` : '-'}</td>
                      <td className="center">{(s.total_sale_listings || 0) + (s.total_rent_listings || 0)}</td>
                    </tr>
                  )
                })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Amenity Comparison */}
      <div className="chart-section">
        <h3>Amenity Access</h3>
        <div className="table-container">
          <table className="amenity-table">
            <thead>
              <tr>
                <th>Property</th>
                {amenityTypes.map(a => (
                  <th key={a} className="amenity-header" title={a}>
                    <span className="amenity-icon">{AMENITY_ICONS[a] || ''}</span>
                    <span className="amenity-name">{a}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredProps
                .sort(([, a], [, b]) => (b.info?.is_target ? 1 : 0) - (a.info?.is_target ? 1 : 0))
                .map(([name, p]) => {
                  const amenities = p.info?.amenities || {}
                  return (
                    <tr key={name} className={p.info?.is_target ? 'target-row' : ''}>
                      <td>
                        {p.info?.is_target && <span className="target-badge">\u2B50</span>}
                        {name.length > 22 ? name.substring(0, 22) + '...' : name}
                      </td>
                      {amenityTypes.map(a => {
                        const am = amenities[a]
                        return (
                          <td key={a} className="amenity-cell" title={am ? `${am.name} — ${am.distance}` : 'Not available'}>
                            {am ? (
                              <span className="amenity-available">
                                {am.distance === 'On-site' || am.distance === 'Covered link bridge'
                                  ? <span className="amenity-onsite">{am.distance}</span>
                                  : <span className="amenity-distance">{am.distance}</span>
                                }
                              </span>
                            ) : (
                              <span className="amenity-none">—</span>
                            )}
                          </td>
                        )
                      })}
                    </tr>
                  )
                })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Price vs PSF Scatter */}
      {scatterData.length > 0 && (
        <div className="chart-section">
          <h3>Price vs PSF</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={400}>
              <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" dataKey="x" name="Median Price" tickFormatter={v => `RM ${(v/1000).toFixed(0)}k`} />
                <YAxis type="number" dataKey="y" name="Median PSF" tickFormatter={v => `${v}`} />
                <ZAxis type="number" dataKey="z" range={[100, 500]} />
                <Tooltip
                  formatter={(v, name) => name === 'Median Price' ? formatRM(v) : name === 'Median PSF' ? formatPSF(v) : v}
                  labelFormatter={(v) => ''}
                  content={({ payload }) => {
                    if (!payload?.length) return null
                    const d = payload[0]?.payload
                    return (
                      <div className="custom-tooltip">
                        <p className="tooltip-name">{d?.isTarget ? '\u2B50 ' : ''}{d?.name}</p>
                        <p>Price: {formatRM(d?.x)}</p>
                        <p>PSF: {formatPSF(d?.y)}</p>
                      </div>
                    )
                  }}
                />
                <Scatter data={scatterData.filter(d => d.isTarget)} fill="#ef4444" shape="star" />
                <Scatter data={scatterData.filter(d => !d.isTarget)} fill="#2563eb" shape="circle" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          <div className="legend-custom">
            <span className="legend-item"><span className="dot" style={{ background: '#ef4444' }}></span> Your Properties</span>
            <span className="legend-item"><span className="dot" style={{ background: '#2563eb' }}></span> Comparables</span>
          </div>
        </div>
      )}
    </div>
  )
}

// ==============================
// TRENDS TAB
// ==============================
const TREND_COLORS = ['#ef4444', '#2563eb', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1', '#14b8a6', '#f43f5e']

function TrendsTab() {
  const [trends, setTrends] = useState(null)
  const [selectedRegion, setSelectedRegion] = useState('all')
  const [metric, setMetric] = useState('sale_psf')

  useEffect(() => {
    fetch('./data/trends.json')
      .then(r => r.json())
      .then(d => setTrends(d))
      .catch(() => {})
  }, [])

  if (!trends) {
    return (
      <div className="tab-content">
        <div className="empty-state">
          <h3>Loading trend data...</h3>
          <p>Trend data is generated from daily scrape snapshots. Run the scraper to build trends.</p>
        </div>
      </div>
    )
  }

  const properties = trends.properties || {}
  const regions = [...new Set(Object.values(properties).map(p => p.region).filter(Boolean))]

  // Filter properties by region
  const filteredProps = selectedRegion === 'all'
    ? Object.entries(properties)
    : Object.entries(properties).filter(([, p]) => p.region === selectedRegion)

  // Build combined chart data: one data point per month, with each property as a series
  const allMonths = new Set()
  filteredProps.forEach(([, p]) => {
    (p.monthly || []).forEach(m => allMonths.add(m.month))
  })
  const sortedMonths = [...allMonths].sort()

  const metricKey = metric === 'sale_psf' ? 'sale_psf_avg' : 'rent_psf_avg'
  const metricLabel = metric === 'sale_psf' ? 'Sale PSF (RM)' : 'Rent PSF (RM/sqft/mo)'

  // Properties that have data for this metric
  const propsWithData = filteredProps.filter(([, p]) =>
    (p.monthly || []).some(m => m[metricKey] != null)
  )

  // Build chart data
  const chartData = sortedMonths.map(month => {
    const point = { month, label: formatMonth(month) }
    propsWithData.forEach(([name, p]) => {
      const mData = (p.monthly || []).find(m => m.month === month)
      if (mData && mData[metricKey] != null) {
        point[name] = mData[metricKey]
      }
    })
    return point
  })

  // Region summary chart
  const summaryData = selectedRegion !== 'all' && trends.summary?.[selectedRegion]
    ? (trends.summary[selectedRegion].monthly || []).map(m => ({
        month: m.month,
        label: formatMonth(m.month),
        'Sale PSF': m.sale_psf_avg,
        'Rent PSF': m.rent_psf_avg,
      }))
    : null

  // All-region summary
  const allRegionSummary = selectedRegion === 'all'
    ? sortedMonths.map(month => {
        const point = { month, label: formatMonth(month) }
        Object.entries(trends.summary || {}).forEach(([region, rData]) => {
          const mData = (rData.monthly || []).find(m => m.month === month)
          if (mData) {
            point[`${region} Sale`] = mData.sale_psf_avg
            point[`${region} Rent`] = mData.rent_psf_avg
          }
        })
        return point
      })
    : null

  return (
    <div className="tab-content">
      <h2>PSF Trends Over Time</h2>
      <p className="section-desc">
        Monthly average price per square foot tracked from daily scrape snapshots.
        More data points accumulate as the scraper runs daily.
      </p>

      {/* Filters */}
      <div className="filter-bar">
        <label>Region:</label>
        <select value={selectedRegion} onChange={e => setSelectedRegion(e.target.value)}>
          <option value="all">All Regions</option>
          {regions.map(r => <option key={r} value={r}>{r}</option>)}
        </select>
        <label style={{ marginLeft: '16px' }}>Metric:</label>
        <select value={metric} onChange={e => setMetric(e.target.value)}>
          <option value="sale_psf">Sale PSF</option>
          <option value="rent_psf">Rental PSF</option>
        </select>
      </div>

      {/* Main trend chart - individual properties */}
      {chartData.length > 0 && propsWithData.length > 0 ? (
        <div className="chart-section">
          <h3>{metricLabel} — By Property</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={chartData} margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 12 }} tickFormatter={v => `${v}`} />
                <Tooltip
                  formatter={(v, name) => [
                    metric === 'sale_psf' ? formatPSF(v) : formatRentPSF(v),
                    name
                  ]}
                />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                {propsWithData.map(([name, p], i) => (
                  <Line
                    key={name}
                    type="monotone"
                    dataKey={name}
                    stroke={p.is_target ? '#ef4444' : TREND_COLORS[i % TREND_COLORS.length]}
                    strokeWidth={p.is_target ? 3 : 1.5}
                    dot={{ r: p.is_target ? 5 : 3 }}
                    connectNulls
                    name={name.length > 20 ? name.substring(0, 20) + '...' : name}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : (
        <div className="empty-state small">
          <p>No {metric === 'sale_psf' ? 'sale' : 'rental'} PSF data available for the selected region.</p>
        </div>
      )}

      {/* Region average summary */}
      {summaryData && summaryData.length > 0 && (
        <div className="chart-section">
          <h3>{selectedRegion} — Region Average</h3>
          <p className="section-desc">Average across all tracked properties in this region</p>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={summaryData} margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip formatter={(v, name) => [
                  name.includes('Rent') ? formatRentPSF(v) : formatPSF(v),
                  name
                ]} />
                <Legend />
                <Line type="monotone" dataKey="Sale PSF" stroke="#2563eb" strokeWidth={2} dot={{ r: 4 }} connectNulls />
                <Line type="monotone" dataKey="Rent PSF" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} connectNulls />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* All-region comparison */}
      {allRegionSummary && allRegionSummary.length > 0 && (
        <div className="chart-section">
          <h3>Region Comparison — Sale PSF Trend</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={allRegionSummary} margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip formatter={(v, name) => [
                  name.includes('Rent') ? formatRentPSF(v) : formatPSF(v),
                  name
                ]} />
                <Legend />
                {regions.map((region, i) => (
                  <Line
                    key={region}
                    type="monotone"
                    dataKey={`${region} Sale`}
                    stroke={TREND_COLORS[i * 2]}
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    connectNulls
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {allRegionSummary && allRegionSummary.length > 0 && (
        <div className="chart-section">
          <h3>Region Comparison — Rental PSF Trend</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={allRegionSummary} margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip formatter={(v, name) => [formatRentPSF(v), name]} />
                <Legend />
                {regions.map((region, i) => (
                  <Line
                    key={region}
                    type="monotone"
                    dataKey={`${region} Rent`}
                    stroke={TREND_COLORS[i * 2 + 1]}
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    connectNulls
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Data table */}
      {propsWithData.length > 0 && (
        <div className="chart-section">
          <h3>Monthly Data Table</h3>
          <div className="table-container">
            <table className="compare-table">
              <thead>
                <tr>
                  <th>Month</th>
                  {propsWithData.map(([name, p]) => (
                    <th key={name}>
                      {p.is_target && <span className="target-badge">⭐</span>}
                      {name.length > 15 ? name.substring(0, 15) + '...' : name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sortedMonths.map(month => {
                  const hasData = propsWithData.some(([name]) => chartData.find(d => d.month === month)?.[name])
                  if (!hasData) return null
                  return (
                    <tr key={month}>
                      <td>{formatMonth(month)}</td>
                      {propsWithData.map(([name, p]) => {
                        const mData = (p.monthly || []).find(m => m.month === month)
                        const val = mData?.[metricKey]
                        return (
                          <td key={name} className="number">
                            {val != null
                              ? metric === 'sale_psf' ? formatPSF(val) : formatRentPSF(val)
                              : '-'}
                            {mData && (metric === 'sale_psf' ? mData.sale_count : mData.rent_count) && (
                              <span className="count-badge">
                                n={metric === 'sale_psf' ? mData.sale_count : mData.rent_count}
                              </span>
                            )}
                          </td>
                        )
                      })}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="trends-note">
        <p>
          <strong>Note:</strong> Trend data accumulates over time as the scraper runs daily.
          Early months may have limited data points. Historical listings are backdated
          based on "listed X days ago" metadata when available.
        </p>
        {trends.generated_at && (
          <p className="meta">Trends generated: {new Date(trends.generated_at).toLocaleString()}</p>
        )}
      </div>
    </div>
  )
}

function formatMonth(monthStr) {
  const [year, month] = monthStr.split('-')
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return `${months[parseInt(month) - 1]} ${year}`
}

// ==============================
// TRANSACTIONS TAB
// ==============================
function TransactionsTab({ data }) {
  const [rawTxns, setRawTxns] = useState([])

  useEffect(() => {
    fetch('./data/transactions.json')
      .then(r => r.json())
      .then(d => setRawTxns(d.filter(t => t.type !== 'area_summary')))
      .catch(() => {})
  }, [])

  const displayTxns = rawTxns.length > 0
    ? rawTxns
    : Object.values(data.properties || {}).flatMap(p => p.transactions || [])

  const chartData = displayTxns
    .filter(t => t.price_psf)
    .map(t => ({
      name: t.property?.substring(0, 22) || 'Unknown',
      PSF: t.price_psf,
      region: t.region || '',
    }))

  return (
    <div className="tab-content">
      <h2>Recent Transactions in Target Areas</h2>
      <p className="section-desc">Subsale transaction data from JPPH via Brickz.my</p>

      {chartData.length > 0 && (
        <div className="chart-section">
          <h3>Transaction PSF by Property</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={Math.max(300, chartData.length * 30)}>
              <BarChart data={chartData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis type="number" tick={{ fontSize: 12 }} />
                <YAxis dataKey="name" type="category" width={170} tick={{ fontSize: 10 }} />
                <Tooltip formatter={(v) => formatPSF(v)} />
                <Bar dataKey="PSF" radius={[0, 4, 4, 0]}>
                  {chartData.map((entry, i) => (
                    <Cell key={i} fill={entry.region.includes('Segambut') || entry.region.includes('Bamboo') ? '#2563eb' : '#f59e0b'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="legend-custom">
            <span className="legend-item"><span className="dot" style={{ background: '#2563eb' }}></span> Segambut / Bamboo Hills</span>
            <span className="legend-item"><span className="dot" style={{ background: '#f59e0b' }}></span> Old Klang Road</span>
          </div>
        </div>
      )}

      <div className="chart-section">
        <h3>All Transactions ({displayTxns.length})</h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Property</th>
                <th>Region</th>
                <th>Price</th>
                <th>PSF</th>
                <th>Type</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {displayTxns.map((t, i) => (
                <tr key={i}>
                  <td>{t.property || 'N/A'}</td>
                  <td>{t.region}</td>
                  <td className="number">{formatRM(t.price)}</td>
                  <td className="number">{formatPSF(t.price_psf)}</td>
                  <td>{t.unit_type || '-'}</td>
                  <td>{t.source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// ==============================
// MARKET TAB
// ==============================
function MarketTab({ data }) {
  const market = data.market_overview || []
  const details = data.property_details || []
  const news = data.news || []

  const brickzSummaries = market.filter(m => m.source === 'brickz' && m.type === 'area_summary')
  const napicData = market.filter(m => m.source === 'napic')

  return (
    <div className="tab-content">
      <h2>Market Overview</h2>

      {brickzSummaries.length > 0 && (
        <div className="chart-section">
          <h3>Area Statistics (Brickz.my)</h3>
          <div className="stats-grid">
            {brickzSummaries.map((s, i) => (
              <div key={i} className="region-card">
                <h4>{s.region}</h4>
                <div className="region-stats">
                  {s.total_transactions && <StatBox label="Total Transactions" value={s.total_transactions} />}
                  {s.median_psf && <StatBox label="Median PSF" value={formatPSF(s.median_psf)} />}
                  {s.total_projects && <StatBox label="Projects" value={s.total_projects} />}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {napicData.length > 0 && (
        <div className="chart-section">
          <h3>NAPIC Publications & Data</h3>
          <div className="napic-list">
            {napicData.map((n, i) => (
              <div key={i} className="napic-item">
                <span className="napic-type">{n.type || 'data'}</span>
                <span className="napic-title">{n.title || 'NAPIC Data'}</span>
                {n.url && <a href={n.url} target="_blank" rel="noopener noreferrer" className="napic-link">View Source</a>}
              </div>
            ))}
          </div>
        </div>
      )}

      {details.length > 0 && (
        <div className="chart-section">
          <h3>Property Insights</h3>
          {details.map((d, i) => (
            <div key={i} className="detail-card">
              <h4>{d.property || 'Market Insight'}</h4>
              <p className="source-tag">Source: {d.source}</p>
              {d.transactions?.length > 0 && <p>{d.transactions.length} historical transactions found</p>}
              {d.median_psf && <p>Median PSF: {formatPSF(d.median_psf)}</p>}
              {d.url && <a href={d.url} target="_blank" rel="noopener noreferrer">View on {d.source}</a>}
            </div>
          ))}
        </div>
      )}

      {news.length > 0 && (
        <div className="chart-section">
          <h3>Related News</h3>
          {news.map((n, i) => (
            <div key={i} className="news-item">
              <h4>{n.title}</h4>
              {n.date && <span className="news-date">{n.date}</span>}
              {n.url && <a href={n.url} target="_blank" rel="noopener noreferrer">Read more</a>}
            </div>
          ))}
        </div>
      )}

      {market.length === 0 && details.length === 0 && news.length === 0 && (
        <div className="empty-state">
          <h3>Market data will appear here</h3>
          <p>Run the scraper to collect data from NAPIC, Brickz.my, and news sources.</p>
        </div>
      )}
    </div>
  )
}

// ==============================
// SHARED COMPONENTS
// ==============================

function PropertyCard({ name, prop, isTarget }) {
  const s = prop.stats || {}
  const info = prop.info || {}
  const amenities = info.amenities || {}
  const amenityCount = Object.keys(amenities).length

  return (
    <div className={`summary-card ${isTarget ? 'target' : ''}`}>
      <div className="card-header">
        <h3>{isTarget && '\u2B50 '}{name}</h3>
        <div className="badges">
          <span className="badge">{info.tenure}</span>
          <span className="tier-badge" style={{ background: TIER_COLORS[info.price_tier] || '#94a3b8' }}>
            {TIER_LABELS[info.price_tier] || 'Mid'}
          </span>
        </div>
      </div>
      <div className="card-body">
        <div className="stat-row">
          <span className="stat-label">Developer</span>
          <span className="stat-value">{info.developer || 'N/A'}</span>
        </div>
        <div className="stat-row">
          <span className="stat-label">Region</span>
          <span className="stat-value">{info.region}</span>
        </div>
        <div className="stat-row">
          <span className="stat-label">Completion</span>
          <span className="stat-value">{info.completion || 'N/A'}</span>
        </div>
        <div className="stat-row highlight">
          <span className="stat-label">Asking Price (Median)</span>
          <span className="stat-value">{formatRM(s.sale_price_median)}</span>
        </div>
        <div className="stat-row">
          <span className="stat-label">Sale PSF (Median)</span>
          <span className="stat-value">{formatPSF(s.sale_psf_median)}</span>
        </div>
        {s.rent_psf_median && (
          <div className="stat-row">
            <span className="stat-label">Rent PSF (Median)</span>
            <span className="stat-value">{formatRentPSF(s.rent_psf_median)}</span>
          </div>
        )}
        {s.rent_price_median && (
          <div className="stat-row">
            <span className="stat-label">Median Rent</span>
            <span className="stat-value">{formatRM(s.rent_price_median)}/mo</span>
          </div>
        )}
        {s.estimated_yield && (
          <div className="stat-row highlight">
            <span className="stat-label">Est. Yield</span>
            <span className="stat-value">{s.estimated_yield}%</span>
          </div>
        )}
        <div className="stat-row">
          <span className="stat-label">Amenities Nearby</span>
          <span className="stat-value amenity-icons">
            {Object.keys(amenities).map(a => (
              <span key={a} title={`${a}: ${amenities[a].name} (${amenities[a].distance})`} className="amenity-dot">
                {AMENITY_ICONS[a] || '\u2022'}
              </span>
            ))}
          </span>
        </div>
      </div>
    </div>
  )
}

function PropertyDetail({ name, prop, regionStats }) {
  const { info, sale_listings, rent_listings, stats } = prop

  const saleData = (sale_listings || [])
    .filter(l => l.price && l.type !== 'building_info')
    .sort((a, b) => (a.price || 0) - (b.price || 0))

  // Filter rentals: exclude misclassified sales (price > RM 20k or PSF > RM 10)
  const rentData = (rent_listings || [])
    .filter(l => l.price && l.price < 20000 && l.type !== 'building_info')
    .sort((a, b) => (a.price || 0) - (b.price || 0))

  const psfDistribution = saleData
    .filter(l => l.price_psf)
    .map(l => ({
      name: l.title?.substring(0, 20) || 'Unit',
      PSF: l.price_psf,
      size: l.size_sqft || 0,
    }))

  const amenities = info?.amenities || {}

  return (
    <div className={`property-section ${info?.is_target ? 'target-section' : ''}`}>
      <div className="property-header">
        <div>
          <h3>
            {info?.is_target && <span className="target-badge">\u2B50</span>}
            {name}
            <span className="tier-badge small" style={{ background: TIER_COLORS[info?.price_tier] || '#94a3b8', marginLeft: '8px' }}>
              {TIER_LABELS[info?.price_tier] || 'Mid'}
            </span>
          </h3>
          <p className="property-meta">
            {info?.property_type} · {info?.tenure} · {info?.completion ? `Completion: ${info.completion}` : ''}
            {info?.total_units ? ` · ${info.total_units} units` : ''}
          </p>
          <p className="property-meta">Developer: {info?.developer}</p>
        </div>
        <div className="key-stats">
          {stats?.sale_price_median && (
            <div className="key-stat">
              <span className="key-stat-value">{formatRM(stats.sale_price_median)}</span>
              <span className="key-stat-label">Median Asking</span>
            </div>
          )}
          {stats?.sale_psf_median && (
            <div className="key-stat">
              <span className="key-stat-value">{formatPSF(stats.sale_psf_median)}</span>
              <span className="key-stat-label">Sale PSF</span>
            </div>
          )}
          {stats?.rent_psf_median && (
            <div className="key-stat rent">
              <span className="key-stat-value">{formatRentPSF(stats.rent_psf_median)}</span>
              <span className="key-stat-label">Rent PSF</span>
            </div>
          )}
          {stats?.rent_price_median && (
            <div className="key-stat rent">
              <span className="key-stat-value">{formatRM(stats.rent_price_median)}</span>
              <span className="key-stat-label">Median Rent/mo</span>
            </div>
          )}
          {stats?.estimated_yield && (
            <div className="key-stat">
              <span className="key-stat-value">{stats.estimated_yield}%</span>
              <span className="key-stat-label">Est. Yield</span>
            </div>
          )}
        </div>
      </div>

      {/* Amenities */}
      {Object.keys(amenities).length > 0 && (
        <div className="amenity-bar">
          {Object.entries(amenities).map(([type, am]) => (
            <span key={type} className="amenity-chip" title={`${am.name} — ${am.distance}`}>
              {AMENITY_ICONS[type] || ''} {type}: {am.distance}
            </span>
          ))}
        </div>
      )}

      {/* Sale Listings Table */}
      {saleData.length > 0 && (
        <div className="chart-section">
          <h4>Sale Listings ({saleData.length})</h4>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Price</th>
                  <th>PSF</th>
                  <th>Size</th>
                  <th>Bed</th>
                  <th>Bath</th>
                  <th>Link</th>
                </tr>
              </thead>
              <tbody>
                {saleData.slice(0, 10).map((l, i) => (
                  <tr key={i}>
                    <td>{l.title || 'N/A'}</td>
                    <td className="number">{formatRM(l.price)}</td>
                    <td className="number">{formatPSF(l.price_psf)}</td>
                    <td className="number">{l.size_sqft ? `${l.size_sqft} sqft` : '-'}</td>
                    <td className="center">{l.bedrooms || '-'}</td>
                    <td className="center">{l.bathrooms || '-'}</td>
                    <td>{l.url ? <a href={l.url} target="_blank" rel="noopener noreferrer">View</a> : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {saleData.length > 10 && <p className="more-text">... and {saleData.length - 10} more listings</p>}
          </div>
        </div>
      )}

      {/* Rent Listings Table */}
      {rentData.length > 0 && (
        <div className="chart-section">
          <h4 className="rent-heading">Rental Listings ({rentData.length})</h4>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Rent/mo</th>
                  <th>Rent PSF</th>
                  <th>Size</th>
                  <th>Bed</th>
                  <th>Bath</th>
                  <th>Link</th>
                </tr>
              </thead>
              <tbody>
                {rentData.slice(0, 10).map((l, i) => (
                  <tr key={i}>
                    <td>{l.title || 'N/A'}</td>
                    <td className="number">{formatRM(l.price)}/mo</td>
                    <td className="number">{l.price_psf && l.price_psf < 10 ? formatRentPSF(l.price_psf) : '-'}</td>
                    <td className="number">{l.size_sqft ? `${l.size_sqft} sqft` : '-'}</td>
                    <td className="center">{l.bedrooms || '-'}</td>
                    <td className="center">{l.bathrooms || '-'}</td>
                    <td>{l.url ? <a href={l.url} target="_blank" rel="noopener noreferrer">View</a> : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {rentData.length > 10 && <p className="more-text">... and {rentData.length - 10} more rental listings</p>}
          </div>
        </div>
      )}

      {/* PSF Chart */}
      {psfDistribution.length > 1 && (
        <div className="chart-section">
          <h4>PSF Distribution</h4>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={psfDistribution}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-15} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip formatter={(v, name) => name === 'PSF' ? formatPSF(v) : `${v} sqft`} />
                <Bar dataKey="PSF" fill={info?.is_target ? '#ef4444' : '#2563eb'} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {saleData.length === 0 && (
        <div className="empty-state small">
          <p>No listings found yet. Data will appear after the next scrape.</p>
        </div>
      )}
    </div>
  )
}

function StatBox({ label, value }) {
  return (
    <div className="stat-box compact">
      <span className="stat-number">{value}</span>
      <span className="stat-desc">{label}</span>
    </div>
  )
}
