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

interface SolarData {
  timestamp: string;
  actual_mw: number;
  pred_nowcast: number;
  pred_hourly: number;
  pred_intraday: number;
  weather_clouds: number;
  simulated_mw?: number;
  contrib_ghi: number;
  contrib_clouds: number;
  contrib_temp: number;
  contrib_time: number;
}

const XAIRow = ({ label, value }: { label: string, value: number }) => (
  <div className="xai-item">
    <span className="xai-key">{label}</span>
    <span className={`xai-val ${value >= 0 ? 'pos' : 'neg'}`}>
      {value >= 0 ? '+' : ''}{value.toFixed(2)} MW
    </span>
  </div>
);

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="custom-tooltip glass">
        <p className="label">{new Date(data.timestamp).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit' })}</p>
        <div className="tooltip-grid">
          <div className="item"><span className="val">{data.actual_mw} MW</span> <span className="key">Actual</span></div>
          <div className="item"><span className="val">{data.pred_nextday} MW</span> <span className="key">Predicted</span></div>
          {data.simulated_mw !== undefined && (
            <div className="item simulated"><span className="val">{data.simulated_mw} MW</span> <span className="key">Simulated</span></div>
          )}
        </div>
        <div className="weather-features">
          <div className="feature">☀️ {data.weather_ghi} W/m²</div>
          <div className="feature">🌡️ {data.weather_temp}°C</div>
          <div className="feature">☁️ {data.weather_clouds}%</div>
        </div>

        <div className="xai-panel">
          <p className="xai-title">AI REASONING (Internal SHAP Values)</p>
          <div className="xai-list">
            <XAIRow label="Solar Intensity" value={data.contrib_ghi} />
            <XAIRow label="Cloud Cover" value={data.contrib_clouds} />
            <XAIRow label="Temperature" value={data.contrib_temp} />
            <XAIRow label="Temporal Factors" value={data.contrib_time} />
          </div>
        </div>
      </div>
    );
  }
  return null;
};

interface GenerationChartProps {
  selectedDate: string;
  onDateChange: (date: string) => void;
  onTotalCalculated: (total: number) => void;
  onForecastCalculated: (total: number) => void;
  onHoverUpdate: (total: number | null) => void;
  onAnomaliesFound: (anomalies: any[]) => void;
}

const GenerationChart: React.FC<GenerationChartProps> = ({ 
  selectedDate, 
  onDateChange, 
  onTotalCalculated,
  onForecastCalculated,
  onHoverUpdate,
  onAnomaliesFound
}) => {
  const [data, setData] = useState<SolarData[]>([]);
  const [loading, setLoading] = useState(true);
  const [cloudMultiplier, setCloudMultiplier] = useState(1.0);
  const [tempOffset, setTempOffset] = useState(0.0);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/dashboard/10-day?start_date=${selectedDate}`);
        const result = await response.json();
        if (Array.isArray(result)) {
          setData(result);
          
          // Calculate Total MWh for Day 1: sum(actual_mw) * 0.5h
          const firstDay = result.filter((_, i) => i < 48); 
          const totalMWh = firstDay.reduce((acc, row) => acc + (row.actual_mw || 0), 0) * 0.5;
          onTotalCalculated(totalMWh);

          // Calculate Forecast Potential for Day 2: sum(pred_nextday) * 0.5h
          const secondDay = result.slice(48);
          const forecastMWh = secondDay.reduce((acc, row) => acc + (Number(row.pred_nextday) || 0), 0) * 0.5;
          onForecastCalculated(forecastMWh);

          // Report Anomalies to Parent
          const foundAnomalies = result.filter(row => row.is_anomaly);
          onAnomaliesFound(foundAnomalies);
        }
      } catch (error) {
        console.error('Error fetching Solar AI data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedDate]);

  const handleSimulate = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cloud_cover_multiplier: cloudMultiplier,
          temp_offset: tempOffset,
          start_date: selectedDate,
        }),
      });
      const simResult = await response.json();
      if (Array.isArray(simResult)) {
        const updatedData = data.map((point, i) => {
          if (i < simResult.length) {
            const sim = simResult[i];
            return { 
              ...point, 
              simulated_mw: sim.simulated_mw,
              // Sync the tooltip values with the simulated weather
              weather_ghi: sim.modified_ghi ?? point.weather_ghi,
              weather_clouds: sim.modified_clouds ?? point.weather_clouds,
              weather_temp: sim.modified_temp ?? point.weather_temp,
              // Update SHAP contributions
              contrib_ghi: sim.contrib_ghi,
              contrib_clouds: sim.contrib_clouds,
              contrib_temp: sim.contrib_temp,
              contrib_time: sim.contrib_time
            };
          }
          return { ...point };
        });
        setData(updatedData);
      }
    } catch (error) {
      console.error('Simulation failed:', error);
    }
  };

  const handleMouseMove = (state: any) => {
    if (state && state.activeTooltipIndex !== undefined) {
      const index = state.activeTooltipIndex;
      
      // Reset sum for each 24h block (48 points per day)
      const dayStartIndex = index < 48 ? 0 : 48;
      
      let runningSum = 0;
      for (let i = dayStartIndex; i <= index; i++) {
        runningSum += (data[i].actual_mw || 0);
      }
      
      onHoverUpdate(runningSum * 0.5);
    }
  };

  const handleMouseLeave = () => {
    onHoverUpdate(null);
  };

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
        <div className="last-updated">
          <span className="date-label">Horizon Start:</span>
          <input 
            type="date" 
            className="date-picker" 
            value={selectedDate}
            min="2016-01-01"
            max="2020-12-20"
            onChange={(e) => onDateChange(e.target.value)}
          />
        </div>
      </div>

      <div className="chart-body">
        <ResponsiveContainer width="100%" height={380}>
          <AreaChart 
            data={data} 
            margin={{ top: 20, right: 30, left: 0, bottom: 0 }}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
          >
            <defs>
              <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#57f1db" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#57f1db" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorPred" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#fbbf24" stopOpacity={0.15} />
                <stop offset="95%" stopColor="#fbbf24" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
            <XAxis 
              dataKey="timestamp" 
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#6b7280', fontSize: 10 }}
              tickFormatter={(ts) => {
                const date = new Date(ts);
                return date.toLocaleDateString('en-IN', {
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                  hour12: false,
                }).replace(',', '');
              }}
              minTickGap={60}
            />
            <YAxis 
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#6b7280', fontSize: 11 }}
              unit=" MW"
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend verticalAlign="top" align="right" height={36} />
            
            <Area
              type="monotone"
              dataKey="actual_mw"
              name="Actual Gen"
              stroke="#57f1db"
              strokeWidth={3}
              fillOpacity={1}
              fill="url(#colorActual)"
              animationDuration={1000}
            />
            <Area
              type="monotone"
              dataKey="pred_nextday"
              name="Next-Day Pred"
              stroke="#ffb95f"
              strokeWidth={2}
              strokeDasharray="5 5"
              fill="url(#colorPred)"
              animationDuration={1500}
            />
            {data.some(d => d.simulated_mw !== undefined) && (
              <Area
                type="monotone"
                dataKey="simulated_mw"
                name="Simulated Gen"
                stroke="#3b82f6"
                strokeWidth={2}
                fill="transparent"
                animationDuration={500}
              />
            )}
            {/* Anomaly Markers (Custom dots for points with is_anomaly) */}
            <Area
              type="monotone"
              dataKey={(d) => d.is_anomaly ? d.actual_mw : null}
              stroke="transparent"
              fill="transparent"
              dot={{ r: 4, fill: '#ff776d', strokeWidth: 2, stroke: '#fff' }}
              name="Grid Curtailment"
            />
          </AreaChart>
        </ResponsiveContainer>

        <div className="simulator-sandbox glass">
          <div className="sandbox-header">
            <h3>Weather Sandbox <span className="beta">LIVE INFERENCE</span></h3>
            <button className="simulate-btn" onClick={handleSimulate}>Run Simulation</button>
          </div>
          <div className="controls-grid">
            <div className="control-group">
              <div className="control-label">
                <span>Cloud Cover Multiplier</span>
                <span className="val">{cloudMultiplier}x</span>
              </div>
              <input 
                type="range" min="0.5" max="2.0" step="0.1" 
                value={cloudMultiplier} 
                onChange={(e) => setCloudMultiplier(parseFloat(e.target.value))}
                onMouseUp={handleSimulate}
              />
            </div>
            <div className="control-group">
              <div className="control-label">
                <span>Temp Offset (°C)</span>
                <span className="val">{tempOffset > 0 ? `+${tempOffset}` : tempOffset}°</span>
              </div>
              <input 
                type="range" min="-10" max="10" step="1" 
                value={tempOffset} 
                onChange={(e) => setTempOffset(parseFloat(e.target.value))}
                onMouseUp={handleSimulate}
              />
            </div>
          </div>
        </div>
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
          color: #57f1db;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          font-weight: 700;
        }

        .chart-title {
          font-size: 1.25rem;
          margin-top: 0.25rem;
        }


        .simulator-sandbox {
          margin-top: 1.5rem;
          padding: 1.2rem;
          border-radius: 1rem;
          background: rgba(255,255,255,0.02);
        }

        .sandbox-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
        }

        .sandbox-header h3 { font-size: 0.9rem; color: #f8fbff; }
        .sandbox-header .beta { font-size: 0.6rem; background: #3b82f6; color: white; padding: 2px 6px; border-radius: 4px; margin-left: 8px; vertical-align: middle; }

        .simulate-btn {
          background: #57f1db;
          color: #00201c;
          border: none;
          padding: 0.4rem 1rem;
          border-radius: 0.5rem;
          font-size: 0.75rem;
          font-weight: 800;
          cursor: pointer;
          font-family: 'Space Grotesk', sans-serif;
        }

        .controls-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 2rem;
        }

        .control-group { display: flex; flex-direction: column; gap: 0.5rem; }
        .control-label { display: flex; justify-content: space-between; font-size: 0.75rem; color: #94a3b8; }
        .control-label .val { color: #57f1db; font-weight: 700; }

        input[type="range"] {
          accent-color: #57f1db;
          background: rgba(255,255,255,0.1);
          height: 4px;
          border-radius: 2px;
          cursor: pointer;
        }

        .custom-tooltip {
          padding: 1rem;
          border-radius: 0.75rem;
          background: rgba(11, 19, 38, 0.95) !important;
          border: 1px solid rgba(87, 241, 219, 0.2) !important;
        }

        .custom-tooltip .label { font-size: 0.75rem; color: #94a3b8; margin-bottom: 0.5rem; }
        .tooltip-grid { display: flex; gap: 1rem; margin-bottom: 0.8rem; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 0.5rem; }
        .tooltip-grid .item { display: flex; flex-direction: column; }
        .tooltip-grid .val { font-size: 1rem; font-weight: 700; color: #f8fbff; }
        .tooltip-grid .key { font-size: 0.65rem; color: #64748b; text-transform: uppercase; }
        .tooltip-grid .simulated .val { color: #3b82f6; }

        .weather-features { display: flex; gap: 0.8rem; font-size: 0.7rem; color: #cbd5e1; }

        .xai-panel {
          margin-top: 1rem;
          padding-top: 0.8rem;
          border-top: 1px solid rgba(255,255,255,0.05);
        }
        .xai-title {
          font-size: 0.6rem;
          font-weight: 800;
          color: #94a3b8;
          letter-spacing: 0.05rem;
          margin-bottom: 0.5rem;
        }
        .xai-list {
          display: flex;
          flex-direction: column;
          gap: 0.3rem;
        }
        .xai-item {
          display: flex;
          justify-content: space-between;
          font-size: 0.7rem;
        }
        .xai-key { color: #cbd5e1; }
        .xai-val.pos { color: #10b981; font-weight: 600; }
        .xai-val.neg { color: #ef4444; font-weight: 600; }

        .date-picker {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(87, 241, 219, 0.2);
          color: #57f1db;
          border-radius: 2rem;
          padding: 0.2rem 0.8rem;
          font-family: 'Space Grotesk', sans-serif;
          font-size: 0.8rem;
          outline: none;
          cursor: pointer;
        }

        .date-label {
          font-size: 0.7rem;
          color: #94a3b8;
          margin-right: 0.5rem;
          text-transform: uppercase;
        }

        .last-updated {
          display: flex;
          align-items: center;
          background: rgba(255, 255, 255, 0.03);
          padding: 0.3rem 0.8rem;
          border-radius: 2rem;
          border: 1px solid rgba(255, 255, 255, 0.05);
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
