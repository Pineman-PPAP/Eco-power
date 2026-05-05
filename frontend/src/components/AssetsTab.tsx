import React, { useEffect, useState } from 'react';

interface Asset {
  asset_id: string;
  name: string;
  asset_type: string;
  generation_mw: number;
  capacity_mw?: number;
  status: 'green' | 'yellow' | 'red';
  timestamp?: string;
  source: string;
}

const AssetsTab: React.FC = () => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [filter, setFilter] = useState<'all' | 'solar' | 'wind'>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAssets = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8080/sldc/assets');
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || 'Failed to fetch assets');
        setAssets(result.assets || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error loading assets');
      } finally {
        setLoading(false);
      }
    };
    fetchAssets();
    const interval = setInterval(fetchAssets, 60000);
    return () => clearInterval(interval);
  }, []);

  const filteredAssets = assets.filter(a => {
    if (filter === 'all') return ['solar', 'wind'].includes(a.asset_type);
    return a.asset_type === filter;
  });

  const stats = {
    green: assets.filter(a => a.status === 'green').length,
    yellow: assets.filter(a => a.status === 'yellow').length,
    red: assets.filter(a => a.status === 'red').length,
  };

  if (loading) return <div className="loading-state">Syncing Renewable Assets...</div>;

  return (
    <div className="assets-tab">
      <div className="assets-controls">
        <div className="status-summary">
          <div className="stat-item green">
            <span className="dot"></span>
            <span className="count">{stats.green}</span>
            <span className="label">Healthy</span>
          </div>
          <div className="stat-item yellow">
            <span className="dot"></span>
            <span className="count">{stats.yellow}</span>
            <span className="label">Warning</span>
          </div>
          <div className="stat-item red">
            <span className="dot"></span>
            <span className="count">{stats.red}</span>
            <span className="label">Critical</span>
          </div>
        </div>

        <div className="filter-group">
          <button 
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >All Assets</button>
          <button 
            className={`filter-btn ${filter === 'solar' ? 'active' : ''}`}
            onClick={() => setFilter('solar')}
          >Solar</button>
          <button 
            className={`filter-btn ${filter === 'wind' ? 'active' : ''}`}
            onClick={() => setFilter('wind')}
          >Wind</button>
        </div>
      </div>

      <div className="assets-grid">
        {filteredAssets.map(asset => (
          <div key={asset.asset_id} className={`asset-card glass status-${asset.status}`}>
            <div className="card-header">
              <div className="asset-type-badge">{asset.asset_type}</div>
              <div className={`status-indicator ${asset.status}`}></div>
            </div>
            <div className="asset-name">{asset.name}</div>
            <div className="asset-metrics">
              <div className="metric">
                <span className="m-label">Generation</span>
                <span className="m-value">{asset.generation_mw.toFixed(1)} MW</span>
              </div>
              {asset.capacity_mw && (
                <div className="metric">
                  <span className="m-label">Capacity</span>
                  <span className="m-value">{asset.capacity_mw} MW</span>
                </div>
              )}
            </div>
            <div className="card-footer">
              <span className="time">{asset.timestamp || 'Live'}</span>
              <span className="source">{asset.source}</span>
            </div>
          </div>
        ))}
      </div>

      <style>{`
        .assets-tab {
          display: flex;
          flex-direction: column;
          gap: 2rem;
        }

        .assets-controls {
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: rgba(255, 255, 255, 0.02);
          padding: 1.25rem;
          border-radius: 1rem;
          border: 1px solid var(--border-subtle);
        }

        .status-summary {
          display: flex;
          gap: 2rem;
        }

        .stat-item {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .stat-item .dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
        }

        .stat-item.green .dot { background: #10b981; box-shadow: 0 0 10px #10b981; }
        .stat-item.yellow .dot { background: #f59e0b; box-shadow: 0 0 10px #f59e0b; }
        .stat-item.red .dot { background: #ef4444; box-shadow: 0 0 10px #ef4444; }

        .stat-item .count {
          font-family: 'Space Grotesk', sans-serif;
          font-size: 1.25rem;
          font-weight: 700;
          color: var(--text-primary);
        }

        .stat-item .label {
          font-size: 0.85rem;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .filter-group {
          display: flex;
          background: rgba(0,0,0,0.2);
          padding: 0.25rem;
          border-radius: 0.75rem;
          border: 1px solid var(--border-subtle);
        }

        .filter-btn {
          padding: 0.5rem 1.25rem;
          border-radius: 0.6rem;
          border: none;
          background: transparent;
          color: var(--text-muted);
          font-size: 0.9rem;
          cursor: pointer;
          transition: all 0.2s;
        }

        .filter-btn.active {
          background: var(--accent-primary);
          color: white;
          box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
        }

        .assets-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 1.5rem;
        }

        .asset-card {
          padding: 1.5rem;
          border-radius: 1.25rem;
          transition: transform 0.2s, border-color 0.2s;
          position: relative;
          overflow: hidden;
        }

        .asset-card:hover {
          transform: translateY(-5px);
          border-color: rgba(255,255,255,0.2);
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.25rem;
        }

        .asset-type-badge {
          font-size: 0.7rem;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          padding: 0.25rem 0.75rem;
          border-radius: 20px;
          background: rgba(255,255,255,0.05);
          color: var(--text-muted);
        }

        .status-indicator {
          width: 12px;
          height: 12px;
          border-radius: 50%;
        }

        .status-indicator.green { background: #10b981; box-shadow: 0 0 12px #10b981; }
        .status-indicator.yellow { background: #f59e0b; box-shadow: 0 0 12px #f59e0b; }
        .status-indicator.red { background: #ef4444; box-shadow: 0 0 12px #ef4444; }

        .asset-name {
          font-size: 1.25rem;
          font-weight: 700;
          color: var(--text-primary);
          margin-bottom: 1.5rem;
          font-family: 'Space Grotesk', sans-serif;
        }

        .asset-metrics {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1rem;
          margin-bottom: 1.5rem;
        }

        .metric {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }

        .m-label {
          font-size: 0.7rem;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .m-value {
          font-size: 1.1rem;
          font-weight: 700;
          color: var(--text-primary);
        }

        .card-footer {
          display: flex;
          justify-content: space-between;
          font-size: 0.75rem;
          color: var(--text-muted);
          padding-top: 1rem;
          border-top: 1px solid var(--border-subtle);
        }

        .loading-state {
          text-align: center;
          padding: 4rem;
          color: var(--text-muted);
          font-size: 1.2rem;
        }

        @media (max-width: 600px) {
          .assets-controls {
            flex-direction: column;
            gap: 1.5rem;
            align-items: flex-start;
          }
        }
      `}</style>
    </div>
  );
};

export default AssetsTab;
