import React, { useState } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import GridStatus from './components/GridStatus';
import GenerationChart from './components/GenerationChart';
import AssetsTab from './components/AssetsTab';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [selectedDate, setSelectedDate] = useState('2020-07-01');
  const [dailyTotal, setDailyTotal] = useState<number | null>(null);
  const [hoverTotal, setHoverTotal] = useState<number | null>(null);
  const [forecastTotal, setForecastTotal] = useState<number | null>(null);
  const [anomalies, setAnomalies] = useState<any[]>([]);

  return (
    <div className="app-container">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="main-content">
        <Header title={activeTab === 'Dashboard' ? 'Control Center' : activeTab} />
        <div className="content-inner animate-fade-in">
          {activeTab === 'Dashboard' && (
            <>
              <GridStatus 
                solarTotal={hoverTotal ?? dailyTotal} 
                isHovering={hoverTotal !== null} 
                forecastTotal={forecastTotal}
              />
              <section className="dashboard-grid main-layout">
                <div className="card glass chart-card">
                  <GenerationChart 
                    selectedDate={selectedDate} 
                    onDateChange={setSelectedDate}
                    onTotalCalculated={setDailyTotal}
                    onForecastCalculated={setForecastTotal}
                    onHoverUpdate={setHoverTotal}
                    onAnomaliesFound={setAnomalies}
                  />
                </div>
                
                <div className="card glass alerts-panel">
                  <div className="card-header">
                    <h3 className="card-title">Grid Intelligence</h3>
                    <span className="badge-alert">{anomalies.length} Alerts</span>
                  </div>
                  <div className="alerts-list">
                    {anomalies.length === 0 ? (
                      <div className="no-alerts">
                        <div className="check-icon">✓</div>
                        <p>No anomalies detected for this period.</p>
                      </div>
                    ) : (
                      anomalies.map((a, i) => (
                        <div key={i} className="alert-item">
                          <div className="alert-indicator"></div>
                          <div className="alert-content">
                            <div className="alert-top">
                              <span className="alert-label">CURTAILMENT</span>
                              <span className="alert-time">
                                {new Date(a.timestamp).toLocaleString('en-IN', { hour: '2-digit', minute: '2-digit' })}
                              </span>
                            </div>
                            <div className="alert-val">
                              Delta: {(a.pred_nextday - a.actual_mw).toFixed(1)} MW
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </section>
            </>
          )}

          {activeTab === 'Assets' && <AssetsTab />}

          {(activeTab !== 'Dashboard' && activeTab !== 'Assets') && (
            <div className="placeholder-view glass">
              <h2>{activeTab} Module</h2>
              <p>This module is currently being optimized. Check back soon.</p>
            </div>
          )}
        </div>
      </main>

      <style>{`
        .app-container {
          display: flex;
          min-height: 100vh;
          background: radial-gradient(circle at top right, rgba(16, 185, 129, 0.05), transparent 40%),
                      radial-gradient(circle at bottom left, rgba(59, 130, 246, 0.05), transparent 40%);
        }

        .main-content {
          flex: 1;
          display: flex;
          flex-direction: column;
          padding: 2rem;
          gap: 2rem;
          margin-left: 260px; /* Width of Sidebar */
        }

        .content-inner {
          display: flex;
          flex-direction: column;
          gap: 2rem;
          max-width: 1400px;
          width: 100%;
          margin: 0 auto;
        }

        .main-layout {
          display: grid;
          grid-template-columns: 3fr 1fr !important;
          gap: 1.5rem;
          margin-top: 1.5rem;
          align-items: start;
        }

        .alerts-panel {
          height: 520px;
          display: flex;
          flex-direction: column;
          padding: 1.5rem;
          background: rgba(15, 23, 42, 0.6) !important;
        }

        .badge-alert {
          background: rgba(239, 68, 68, 0.15);
          color: #ef4444;
          padding: 0.2rem 0.6rem;
          border-radius: 2rem;
          font-size: 0.7rem;
          font-weight: 700;
          border: 1px solid rgba(239, 68, 68, 0.2);
        }

        .alerts-list {
          margin-top: 1.5rem;
          overflow-y: auto;
          flex: 1;
          padding-right: 0.5rem;
        }

        .alerts-list::-webkit-scrollbar { width: 4px; }
        .alerts-list::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }

        .alert-item {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.05);
          border-radius: 0.75rem;
          padding: 1rem;
          margin-bottom: 0.75rem;
          display: flex;
          gap: 1rem;
          transition: all 0.2s;
        }

        .alert-item:hover {
          background: rgba(255, 255, 255, 0.05);
          border-color: rgba(239, 68, 68, 0.3);
          transform: translateX(4px);
        }

        .alert-indicator {
          width: 4px;
          background: #ef4444;
          border-radius: 10px;
          box-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
        }

        .alert-content { flex: 1; }
        .alert-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem; }
        .alert-label { font-size: 0.6rem; font-weight: 800; color: #ef4444; letter-spacing: 0.05rem; }
        .alert-time { font-size: 0.7rem; color: #94a3b8; }
        .alert-val { font-size: 0.9rem; font-weight: 500; color: #f1f5f9; }

        .no-alerts {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100%;
          color: #64748b;
          text-align: center;
          opacity: 0.6;
        }

        .check-icon {
          font-size: 2rem;
          color: #10b981;
          margin-bottom: 1rem;
          background: rgba(16, 185, 129, 0.1);
          width: 50px;
          height: 50px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
        }

        @media (max-width: 1024px) {
          .main-content {
            margin-left: 0;
            padding: 1rem;
          }
          .main-layout {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
};

export default App;
