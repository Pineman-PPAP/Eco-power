import React, { useEffect, useState } from 'react';

interface Asset {
  asset_id: string;
  name: string;
  asset_type: string;
  generation_mw: number;
  capacity_mw?: number;
  solar_mw?: number;
  wind_mw?: number;
  pavagada_solar_mw?: number;
  timestamp?: string;
  source: string;
}

const typeLabel: Record<string, string> = {
  solar: 'Solar',
  wind: 'Wind',
  hydro: 'Hydro',
  thermal: 'Thermal',
  other: 'Other',
  ncep_zone: 'NCEP Zone',
  conventional_plant: 'Plant',
};

const AssetList: React.FC = () => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAssets = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/sldc/assets');
        const result = await response.json();
        if (!response.ok) {
          throw new Error(result.detail || 'Unable to load SLDC assets');
        }
        setAssets(Array.isArray(result.assets) ? result.assets : []);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load SLDC assets');
      } finally {
        setLoading(false);
      }
    };

    fetchAssets();
    const interval = setInterval(fetchAssets, 60000);
    return () => clearInterval(interval);
  }, []);

  const summaryAssets = assets.filter((asset) =>
    ['solar', 'wind', 'hydro', 'thermal', 'other'].includes(asset.asset_type)
  );
  const detailAssets = assets.filter((asset) => !summaryAssets.includes(asset));

  if (loading) {
    return <div className="asset-empty glass">Syncing KPTCL SLDC assets...</div>;
  }

  if (error) {
    return <div className="asset-empty glass">{error}</div>;
  }

  return (
    <div className="asset-list-container animate-fade-in">
      <div className="asset-header">
        <h2>SLDC Asset Breakdown</h2>
        <p className="subtitle">Live values from KPTCL SLDC, refreshed every minute</p>
      </div>

      <div className="summary-grid">
        {summaryAssets.map((asset) => (
          <div key={asset.asset_id} className={`summary-card glass ${asset.asset_type}`}>
            <div className="asset-kind">{typeLabel[asset.asset_type] || asset.asset_type}</div>
            <div className="asset-value">{asset.generation_mw.toLocaleString()} MW</div>
            <div className="asset-source">{asset.source}</div>
            {asset.pavagada_solar_mw !== undefined && (
              <div className="asset-note">Pavagada: {asset.pavagada_solar_mw.toLocaleString()} MW</div>
            )}
          </div>
        ))}
      </div>

      <div className="asset-table glass">
        <div className="table-head">
          <span>Name</span>
          <span>Type</span>
          <span>Generation</span>
          <span>Detail</span>
          <span>Source</span>
        </div>
        {detailAssets.map((asset) => (
          <div key={asset.asset_id} className="table-row">
            <span className="name-cell">{asset.name}</span>
            <span>{typeLabel[asset.asset_type] || asset.asset_type}</span>
            <span>{asset.generation_mw.toLocaleString()} MW</span>
            <span>
              {asset.asset_type === 'ncep_zone'
                ? `Solar ${asset.solar_mw?.toLocaleString() || 0} / Wind ${asset.wind_mw?.toLocaleString() || 0}`
                : asset.capacity_mw
                  ? `${asset.capacity_mw.toLocaleString()} MW capacity`
                  : asset.timestamp || '-'}
            </span>
            <span>{asset.source}</span>
          </div>
        ))}
      </div>

      <style>{`
        .asset-list-container {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
          padding-bottom: 3rem;
        }

        .asset-header h2 {
          color: var(--text-primary);
          font-size: 2rem;
          margin-bottom: 0.35rem;
        }

        .subtitle {
          color: var(--text-muted);
        }

        .summary-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
          gap: 1rem;
        }

        .summary-card {
          border-radius: 0.75rem;
          padding: 1rem;
          min-height: 132px;
          display: flex;
          flex-direction: column;
          gap: 0.35rem;
        }

        .asset-kind, .asset-source, .asset-note {
          color: var(--text-muted);
          font-size: 0.74rem;
          font-weight: 700;
          letter-spacing: 0.06em;
          text-transform: uppercase;
        }

        .asset-value {
          color: var(--text-primary);
          font-family: 'Space Grotesk', sans-serif;
          font-size: 1.55rem;
          font-weight: 700;
        }

        .summary-card.solar .asset-value { color: #facc15; }
        .summary-card.wind .asset-value { color: #3b82f6; }
        .summary-card.hydro .asset-value { color: #38bdf8; }
        .summary-card.thermal .asset-value { color: #f97316; }

        .asset-table {
          border-radius: 0.75rem;
          overflow: hidden;
        }

        .table-head, .table-row {
          display: grid;
          grid-template-columns: 1.4fr 0.8fr 0.8fr 1.2fr 0.9fr;
          gap: 1rem;
          align-items: center;
          padding: 0.9rem 1rem;
        }

        .table-head {
          color: var(--text-secondary);
          background: rgba(255, 255, 255, 0.035);
          font-size: 0.75rem;
          font-weight: 800;
          letter-spacing: 0.08em;
          text-transform: uppercase;
        }

        .table-row {
          color: var(--text-secondary);
          border-top: 1px solid var(--border-subtle);
          font-size: 0.88rem;
        }

        .name-cell {
          color: var(--text-primary);
          font-weight: 700;
        }

        .asset-empty {
          border-radius: 0.75rem;
          color: var(--text-muted);
          padding: 2rem;
          text-align: center;
        }

        @media (max-width: 900px) {
          .table-head { display: none; }
          .table-row {
            grid-template-columns: 1fr;
            gap: 0.35rem;
          }
        }
      `}</style>
    </div>
  );
};

export default AssetList;
