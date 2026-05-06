import React, { useEffect, useState } from 'react';

interface GridStatusData {
  timestamp: string;
  frequency: number;
  solar_mw: number;
  wind_mw: number;
  live_generation_mw: number;
  ncep_mw: number;
  is_stale: boolean;
}

interface GridStatusProps {
  solarTotal?: number | null;
  forecastTotal?: number | null;
  isHovering?: boolean;
}

const GridStatus: React.FC<GridStatusProps> = ({ solarTotal, forecastTotal, isHovering }) => {
  const [data, setData] = useState<GridStatusData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/sldc/status');
        const result = await response.json();
        if (result && !result.detail) {
          setData(result);
        }
      } catch (error) {
        console.error('Error fetching grid status:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return <div className="status-loading">Loading Grid Metrics...</div>;
  }

  const formatValue = (val: number | undefined) => {
    if (val === undefined || val === null) return '0 MW';
    return `${val.toLocaleString()} MW`;
  };

  return (
    <div className="status-grid">
      <StatusCard 
        title="Total Renewable" 
        value={formatValue(data?.ncep_mw)} 
        trend="+2.4%" 
        color="teal" 
        subtitle={`Live SLDC: ${data?.timestamp || 'Syncing...'}`}
      />
      <StatusCard 
        title="Solar Component" 
        value={solarTotal !== null && solarTotal !== undefined ? `${solarTotal.toLocaleString(undefined, { maximumFractionDigits: 1 })} MWh` : '0 MWh'} 
        trend={isHovering ? "Live Meter" : "Daily Total"} 
        color="amber" 
        subtitle={isHovering ? "Cumulative Generated" : "Selected Day Energy"}
      />
      <StatusCard 
        title="Forecast Potential" 
        value={forecastTotal !== null && forecastTotal !== undefined ? `${forecastTotal.toLocaleString(undefined, { maximumFractionDigits: 1 })} MWh` : '0 MWh'} 
        trend="Next-Day" 
        color="purple" 
        subtitle="Predicted Tomorrow"
      />
      <StatusCard 
        title="Wind Component" 
        value={formatValue(data?.wind_mw)} 
        trend="+1.2%" 
        color="blue" 
      />
      <StatusCard 
        title="Grid Frequency" 
        value={`${data?.frequency?.toFixed(2) || '50.00'} Hz`} 
        trend="Stable" 
        color={data?.is_stale ? "red" : "green"} 
        subtitle={data?.is_stale ? "⚠️ Data Stale (>30m)" : "⚡ Normal Operation"}
      />

      <style>{`
        .status-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
          gap: 1.5rem;
          margin-bottom: 2rem;
        }

        .status-card {
          padding: 1.5rem;
          border-radius: 1rem;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
          transition: transform 0.2s;
        }

        .status-card:hover {
          transform: translateY(-4px);
        }

        .status-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .status-title {
          font-size: 0.875rem;
          color: var(--text-secondary);
          font-weight: 500;
        }

        .status-trend {
          font-size: 0.75rem;
          padding: 0.25rem 0.5rem;
          border-radius: 2rem;
          background: rgba(255,255,255,0.05);
        }

        .status-value {
          font-size: 1.5rem;
          font-weight: 700;
          font-family: 'Space Grotesk', sans-serif;
        }

        .status-subtitle {
          font-size: 0.7rem;
          color: var(--text-muted);
          margin-top: 0.25rem;
        }

        .status-loading {
          padding: 2rem;
          text-align: center;
          color: var(--text-muted);
        }

        .color-teal .status-value { color: var(--accent-primary); }
        .color-amber .status-value { color: #facc15; }
        .color-blue .status-value { color: #3b82f6; }
        .color-green .status-value { color: #4ade80; }
        .color-red .status-value { color: #f87171; }
      `}</style>
    </div>
  );
};

const StatusCard: React.FC<{ 
  title: string; 
  value: string; 
  trend: string; 
  color: string;
  subtitle?: string;
}> = ({ title, value, trend, color, subtitle }) => (
  <div className={`status-card glass color-${color}`}>
    <div className="status-header">
      <span className="status-title">{title}</span>
      <span className="status-trend">{trend}</span>
    </div>
    <div className="status-value">{value}</div>
    {subtitle && <div className="status-subtitle">{subtitle}</div>}
  </div>
);

export default GridStatus;
