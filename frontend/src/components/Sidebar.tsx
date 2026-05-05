import React from 'react';

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
  const menuItems = [
    { name: 'Dashboard', icon: '📊' },
    { name: 'Assets', icon: '🏭' },
    { name: 'Forecasts', icon: '📈' },
    { name: 'Analytics', icon: '🔬' },
    { name: 'Settings', icon: '⚙️' },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon">⚡</div>
        <div className="logo-text">
          <span className="brand">EcoPower</span>
          <span className="sub">Intelligence</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <button
            key={item.name}
            onClick={() => onTabChange(item.name)}
            className={`nav-link ${activeTab === item.name ? 'active' : ''}`}
            style={{ background: 'none', border: 'none', width: '100%', textAlign: 'left', cursor: 'pointer' }}
          >
            <span className="icon">{item.icon}</span>
            {item.name}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="help-card glass">
          <p>Need help?</p>
          <button className="btn-secondary">Documentation</button>
        </div>
      </div>

      <style>{`
        .sidebar {
          position: fixed;
          left: 0;
          top: 0;
          bottom: 0;
          width: 260px;
          background: var(--bg-surface);
          border-right: 1px solid var(--border-subtle);
          display: flex;
          flex-direction: column;
          padding: 2rem 1.5rem;
          z-index: 100;
        }

        .sidebar-logo {
          display: flex;
          align-items: center;
          gap: 1rem;
          margin-bottom: 3rem;
        }

        .logo-icon {
          font-size: 1.5rem;
          width: 42px;
          height: 42px;
          background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .logo-text {
          display: flex;
          flex-direction: column;
        }

        .brand {
          font-family: 'Space Grotesk', sans-serif;
          font-size: 1.25rem;
          font-weight: 700;
          letter-spacing: -0.02em;
        }

        .sub {
          font-size: 0.75rem;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.1em;
        }

        .sidebar-nav {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
          flex: 1;
        }

        .nav-link {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 0.75rem 1rem;
          border-radius: 0.75rem;
          color: var(--text-secondary);
          text-decoration: none;
          font-weight: 500;
          transition: all 0.2s ease;
        }

        .nav-link:hover {
          background: rgba(255, 255, 255, 0.05);
          color: var(--text-primary);
        }

        .nav-link.active {
          background: rgba(16, 185, 129, 0.1);
          color: var(--accent-primary);
        }

        .sidebar-footer {
          margin-top: auto;
        }

        .help-card {
          padding: 1rem;
          border-radius: 1rem;
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .help-card p {
          font-size: 0.85rem;
          color: var(--text-secondary);
        }

        .btn-secondary {
          background: transparent;
          border: 1px solid var(--border-subtle);
          color: var(--text-primary);
          padding: 0.5rem;
          border-radius: 0.5rem;
          cursor: pointer;
          font-size: 0.8rem;
          transition: border-color 0.2s;
        }

        .btn-secondary:hover {
          border-color: var(--accent-primary);
        }

        @media (max-width: 1024px) {
          .sidebar {
            transform: translateX(-100%);
          }
        }
      `}</style>
    </aside>
  );
};

export default Sidebar;
