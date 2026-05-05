import React from 'react';

interface HeaderProps {
  title: string;
}

const Header: React.FC<HeaderProps> = ({ title }) => {
  return (
    <header className="header glass">
      <div className="header-left">
        <span className="kicker">System Status</span>
        <h1>{title}</h1>
      </div>
      
      <div className="header-right">
        <div className="status-pill">
          <span className="pulse-dot"></span>
          Live: Grid Connected
        </div>
        <div className="user-profile">
          <div className="avatar">AD</div>
        </div>
      </div>

      <style>{`
        .header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 1rem 2rem;
          border-radius: 1rem;
          margin-bottom: 1rem;
        }

        .header-left .kicker {
          font-size: 0.75rem;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          color: var(--accent-primary);
          font-weight: 700;
        }

        .header-left h1 {
          font-size: 1.5rem;
          margin: 0;
        }

        .header-right {
          display: flex;
          align-items: center;
          gap: 1.5rem;
        }

        .status-pill {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem 1rem;
          background: rgba(16, 185, 129, 0.1);
          border: 1px solid rgba(16, 185, 129, 0.2);
          border-radius: 2rem;
          font-size: 0.85rem;
          font-weight: 600;
          color: var(--accent-primary);
        }

        .pulse-dot {
          width: 8px;
          height: 8px;
          background: var(--accent-primary);
          border-radius: 50%;
          box-shadow: 0 0 10px var(--accent-primary);
          animation: pulse 2s infinite;
        }

        @keyframes pulse {
          0% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(1.2); }
          100% { opacity: 1; transform: scale(1); }
        }

        .avatar {
          width: 40px;
          height: 40px;
          background: var(--accent-secondary);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 700;
          font-size: 0.9rem;
          border: 2px solid var(--border-subtle);
        }
      `}</style>
    </header>
  );
};

export default Header;
