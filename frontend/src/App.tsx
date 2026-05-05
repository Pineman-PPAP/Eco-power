import React, { useState } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import GridStatus from './components/GridStatus';
import GenerationChart from './components/GenerationChart';
import AssetsTab from './components/AssetsTab';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('Dashboard');

  return (
    <div className="app-container">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="main-content">
        <Header title={activeTab === 'Dashboard' ? 'Control Center' : activeTab} />
        <div className="content-inner animate-fade-in">
          {activeTab === 'Dashboard' && (
            <>
              <GridStatus />
              <section className="dashboard-grid">
                <div className="card glass full-width">
                  <GenerationChart />
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

        .dashboard-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
          gap: 1.5rem;
        }

        .card.full-width {
          grid-column: 1 / -1;
          min-height: auto;
          padding: 0;
        }

        .card {
          padding: 1.5rem;
          border-radius: 1rem;
          min-height: 300px;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .card h3 {
          font-size: 1.1rem;
          color: var(--text-secondary);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .placeholder-chart, .placeholder-view {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          background: rgba(255, 255, 255, 0.03);
          border-radius: 1rem;
          border: 1px dashed var(--border-subtle);
          color: var(--text-muted);
          padding: 4rem;
          text-align: center;
          gap: 1rem;
        }

        @media (max-width: 1024px) {
          .main-content {
            margin-left: 0;
            padding: 1rem;
          }
        }
      `}</style>
    </div>
  );
};

export default App;
