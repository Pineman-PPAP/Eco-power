import React, { useEffect, useState } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

interface SldcData {
  sldc_ts: string;
  solar_mw: number;
  wind_mw: number;
  scraped_at: string;
}

const GenerationChart: React.FC = () => {
  const [data, setData] = useState<SldcData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8080/sldc/generation?limit=96');
        const result = await response.json();
        if (Array.isArray(result)) {
          setData(result);
        }
      } catch (error) {
        console.error('Error fetching SLDC data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 15 * 60 * 1000); // Refresh every 15 minutes
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="chart-empty-state">Syncing with SLDC...</div>;
  }

  if (data.length === 0) {
    return <div className="chart-empty-state">No generation data available for the last 24h.</div>;
  }

  return (
    <div className="generation-chart-container">
      <div className="chart-header">
        <div className="header-text">
          <span className="chart-subtitle">Real-time KPTCL SLDC Data</span>
          <h2 className="chart-title">Solar & Wind Generation</h2>
        </div>
        {data.length > 0 && (
          <div className="last-updated">
            Last Updated: {data[data.length - 1].sldc_ts}
          </div>
        )}
      </div>

      <div className="chart-body">
        <ResponsiveContainer width="100%" height={350}>
          <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorSolar" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#facc15" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#facc15" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorWind" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
            <XAxis 
              dataKey="sldc_ts" 
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#6b7280', fontSize: 11 }}
              tickFormatter={(ts) => ts.split(' ')[1] || ts} // Show only time
            />
            <YAxis 
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#6b7280', fontSize: 11 }}
              unit=" MW"
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#111827', 
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '8px',
                fontSize: '12px'
              }}
              itemStyle={{ fontSize: '12px' }}
            />
            <Legend verticalAlign="top" align="right" height={36} />
            <Area
              type="monotone"
              dataKey="solar_mw"
              name="Solar (MW)"
              stroke="#facc15"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorSolar)"
            />
            <Area
              type="monotone"
              dataKey="wind_mw"
              name="Wind (MW)"
              stroke="#3b82f6"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorWind)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <style>{`
        .generation-chart-container {
          padding: 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }
        
        .chart-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-end;
        }

        .chart-subtitle {
          font-size: 0.75rem;
          color: var(--accent-primary);
          text-transform: uppercase;
          letter-spacing: 0.1em;
          font-weight: 700;
        }

        .chart-title {
          font-size: 1.25rem;
          margin-top: 0.25rem;
        }

        .last-updated {
          font-size: 0.8rem;
          color: var(--text-muted);
          background: rgba(255, 255, 255, 0.03);
          padding: 0.4rem 0.8rem;
          border-radius: 2rem;
          border: 1px solid rgba(255, 255, 255, 0.05);
          font-family: 'Space Grotesk', sans-serif;
        }

        .chart-empty-state {
          height: 350px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--text-muted);
          font-family: 'Space Grotesk', sans-serif;
          background: rgba(255,255,255,0.02);
          border-radius: 0.5rem;
          margin-top: 1rem;
        }

        .recharts-legend-item-text {
          color: var(--text-secondary) !important;
          font-size: 0.8rem;
          font-weight: 500;
        }
      `}</style>
    </div>
  );
};

export default GenerationChart;
