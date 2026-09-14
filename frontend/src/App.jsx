// App.jsx
// PURPOSE: Root component. Manages global state:
//   - sidebarOpen: whether the sidebar is expanded
//   - currentTask: the active research task being viewed
//   - history: list of all tasks submitted this session
//   - backendOk: whether the backend is reachable

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from './components/Sidebar';
import UnicornBackground from './components/UnicornBackground';
import HomePage from './pages/HomePage';
import ResearchPage from './pages/ResearchPage';
import { createResearchTask, listResearchTasks, deleteResearchTask, checkHealth } from './services/api';
import './App.css';

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentTask, setCurrentTask] = useState(null);
  const [history, setHistory]         = useState([]);
  const [isLoading, setIsLoading]     = useState(false);
  const [backendOk, setBackendOk]     = useState(true);

  // Load history from backend on first render
  useEffect(() => {
    checkHealth()
      .then(ok => {
        setBackendOk(ok);
        if (ok) return listResearchTasks(30);
        return [];
      })
      .then(tasks => setHistory(tasks || []))
      .catch(() => setBackendOk(false));
  }, []);

  // Called when user submits a research topic from HomePage
  const handleSubmit = async (topic, instructions, mode) => {
    setIsLoading(true);
    try {
      const task = await createResearchTask(topic, instructions, mode);
      setHistory(prev => [task, ...prev]);
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

  // When history item is clicked, update sidebar active task
  const handleSelectTask = (task) => {
    setCurrentTask(task);
  };

  // Delete a task from history
  const handleDeleteTask = async (taskId) => {
    try {
      await deleteResearchTask(taskId);
      setHistory(prev => prev.filter(t => t.id !== taskId));
      if (currentTask?.id === taskId) setCurrentTask(null);
    } catch (err) {
      console.error('Failed to delete task:', err);
    }
  };

  // Update a task in the history list (e.g., when it completes)
  const handleTaskUpdate = (updatedTask) => {
    setHistory(prev =>
      prev.map(t => t.id === updatedTask.id ? { ...t, ...updatedTask } : t)
    );
  };

  return (
    <div className="app-shell">
      {/* Unicorn Studio-style animated background */}
      <UnicornBackground />

      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(o => !o)}
        history={history}
        onSelectTask={handleSelectTask}
        onDeleteTask={handleDeleteTask}
        onNewResearch={handleNewResearch}
        activeTaskId={currentTask?.id}
      />

      {/* Main content area — shifts right when sidebar opens */}
      <main className={`main-content ${sidebarOpen ? 'sidebar-open' : ''}`}>
        {/* Top bar */}
        <header className="top-bar">
          <div className="top-left">
            {!sidebarOpen && (
              <button
                id="open-sidebar-btn"
                className="open-sidebar-btn"
                onClick={() => setSidebarOpen(true)}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
                  <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
                </svg>
                Open sidebar
              </button>
            )}
          </div>
          <div className="top-right">
            {!backendOk && (
              <span className="backend-badge offline" title="Backend is not reachable">⚠ Backend offline</span>
            )}
            <button id="upgrade-btn" className="upgrade-btn">✦ Upgrade</button>
            <button id="settings-icon-btn" className="icon-btn top-icon" title="Settings">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
                <circle cx="12" cy="12" r="3"/>
                <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
              </svg>
            </button>
          </div>
        </header>

        {/* Page content */}
        <AnimatePresence mode="wait">
          {currentTask ? (
            <motion.div
              key="research"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
              style={{ width: '100%', height: '100%' }}
            >
              <ResearchPage task={currentTask} onNewResearch={handleNewResearch} onTaskUpdate={handleTaskUpdate} />
            </motion.div>
          ) : (
            <motion.div
              key="home"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
              style={{ width: '100%', height: '100%' }}
            >
              <HomePage onSubmit={handleSubmit} isLoading={isLoading} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
