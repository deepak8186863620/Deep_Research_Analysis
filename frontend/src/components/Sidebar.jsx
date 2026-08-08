// components/Sidebar.jsx
import '../styles/Sidebar.css';

const MenuIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
  </svg>
);
const PenIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
  </svg>
);
const SearchIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
);
const FlaskIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <path d="M9 3H15M9 3V14L4 20H20L15 14V3M9 3H15"/>
  </svg>
);
const BookIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
  </svg>
);
const SettingsIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <circle cx="12" cy="12" r="3"/>
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
  </svg>
);
const TrashIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" width="14" height="14">
    <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/>
  </svg>
);

const STATUS_DOT_CLASSES = {
  completed:  'completed',
  processing: 'processing',
  pending:    'pending',
  failed:     'failed',
};

export default function Sidebar({ isOpen, onToggle, history = [], onSelectTask, onDeleteTask, onNewResearch, activeTaskId }) {
  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      {/* Top controls */}
      <div className="sidebar-top">
        <button id="sidebar-toggle-btn" className="icon-btn" onClick={onToggle} title="Toggle sidebar">
          <MenuIcon />
        </button>
        <button id="new-research-btn" className="icon-btn" title="New research" onClick={onNewResearch}>
          <PenIcon />
        </button>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <div className="nav-item active">
          <FlaskIcon />
          <span className="nav-label">Research</span>
        </div>
        <div className="nav-item">
          <SearchIcon />
          <span className="nav-label">Explore</span>
        </div>
        <div className="nav-item">
          <BookIcon />
          <span className="nav-label">Library</span>
        </div>
      </nav>

      {/* Research history */}
      {history.length > 0 && (
        <div className="sidebar-history">
          <div className="history-label">Recent</div>
          {history.map((task) => (
            <div
              key={task.id}
              className={`history-item ${activeTaskId === task.id ? 'active' : ''}`}
              onClick={() => onSelectTask(task)}
            >
              <span className={`history-dot ${STATUS_DOT_CLASSES[task.status] || 'pending'}`} />
              <span className="history-text">{task.topic}</span>
              <button
                className="delete-btn"
                title="Delete"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteTask(task.id);
                }}
              >
                <TrashIcon />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {history.length === 0 && isOpen && (
        <div className="sidebar-empty">
          <span>No research yet</span>
          <small>Your topics will appear here</small>
        </div>
      )}

      {/* Bottom: settings + user */}
      <div className="sidebar-bottom">
        <div className="user-row">
          <button id="sidebar-settings-btn" className="icon-btn" title="Settings">
            <SettingsIcon />
          </button>
          <div className="user-avatar" title="Deepak">D</div>
          <span className="user-name">Deepak</span>
        </div>
      </div>
    </aside>
  );
}
