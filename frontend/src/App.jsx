// App.jsx
// PURPOSE: Root component. Manages global state:
//   - sidebarOpen: whether the sidebar is expanded
//   - currentTask: the active research task being viewed
//   - history: list of all tasks submitted this session

import { useState } from 'react';
import Sidebar from './components/Sidebar';
import HomePage from './pages/HomePage';
import ResearchPage from './pages/ResearchPage';
import { createResearchTask } from './services/api';
import './App.css';

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentTask, setCurrentTask] = useState(null);
  const [history, setHistory]         = useState([]);
  const [isLoading, setIsLoading]     = useState(false);

  // Called when user submits a research topic from HomePage
  const handleSubmit = async (topic, instructions) => {
    setIsLoading(true);
    try {
      const task = await createResearchTask(topic, instructions);
      // Add to sidebar history
      setHistory(prev => [task, ...prev]);
      // Navigate to results page
      setCurrentTask(task);
    } catch (err) {
      console.error('Failed to create task:', err);
      alert('Could not connect to the backend. Is the server running?');
    } finally {
      setIsLoading(false);
    }
  };

  // Called when user clicks "New Research" or sidebar item
  const handleNewResearch = () => setCurrentTask(null);

  // When history item is clicked, update sidebar's active task
  // but also update the currentTask so the result page re-renders
  const handleSelectTask = (task) => {
    setCurrentTask(task);
  };

  return (
    <div className="app-shell">
      {/* Ambient glow background */}
      <div className="glow-bg" />

      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(o => !o)}
        history={history}
        onSelectTask={handleSelectTask}
        activeTaskId={currentTask?.id}
      />

      {/* Main content area — shifts right when sidebar opens */}
      <main className={`main-content ${sidebarOpen ? 'sidebar-open' : ''}`}>
        {/* Top bar */}
        <header className="top-bar">
          <div className="top-left">
            {!sidebarOpen && (
              <button
                className="open-sidebar-btn"
                onClick={() => setSidebarOpen(true)}
              >
                Open sidebar
              </button>
            )}
          </div>
          <div className="top-right">
            <button className="upgrade-btn">
              ✦ Upgrade
            </button>
            <button className="icon-btn top-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
                <circle cx="12" cy="12" r="3"/>
                <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
              </svg>
            </button>
          </div>
        </header>

        {/* Page content */}
        {currentTask
          ? <ResearchPage task={currentTask} onNewResearch={handleNewResearch} />
          : <HomePage onSubmit={handleSubmit} isLoading={isLoading} />
        }
      </main>
    </div>
  );
}
