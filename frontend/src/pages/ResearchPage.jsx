// pages/ResearchPage.jsx
// PURPOSE: The results page shown after a research task is submitted.
// It polls the backend every 3 seconds until status = "completed" or "failed",
// then renders the final markdown report.

import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { getResearchTask } from '../services/api';
import '../styles/ResearchPage.css';

const POLL_INTERVAL = 3000; // ms between status checks

const STATUS_LABELS = {
  pending:    { text: 'Queued',     color: '#9aa0b4' },
  processing: { text: 'Researching', color: '#4a90d9' },
  completed:  { text: 'Complete',   color: '#4caf8a' },
  failed:     { text: 'Failed',     color: '#e05c5c' },
};

export default function ResearchPage({ task, onNewResearch }) {
  const [result, setResult] = useState(task);
  const [elapsedTime, setElapsedTime] = useState(0);
  const timerRef = useRef(null);
  const pollRef  = useRef(null);

  // Polling: check task status every 3 seconds until done
  useEffect(() => {
    if (!task?.id) return;
    setResult(task);
    setElapsedTime(0);

    // Start elapsed time counter
    timerRef.current = setInterval(() => setElapsedTime(t => t + 1), 1000);

    // Start polling for status
    const poll = async () => {
      try {
        const updated = await getResearchTask(task.id);
        setResult(updated);
        if (updated.status === 'completed' || updated.status === 'failed') {
          clearInterval(timerRef.current);
          clearInterval(pollRef.current);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    };

    poll(); // Immediate first check
    pollRef.current = setInterval(poll, POLL_INTERVAL);

    return () => {
      clearInterval(timerRef.current);
      clearInterval(pollRef.current);
    };
  }, [task?.id]);

  const status = STATUS_LABELS[result?.status] || STATUS_LABELS.pending;
  const isProcessing = result?.status === 'pending' || result?.status === 'processing';

  const formatTime = (s) => s < 60 ? `${s}s` : `${Math.floor(s/60)}m ${s%60}s`;

  return (
    <div className="research-page">
      {/* Header bar */}
      <div className="research-header fade-up">
        <div className="topic-badge">
          <span className="topic-icon">🔬</span>
          <h2 className="topic-title">{result?.topic}</h2>
        </div>
        <div className="header-actions">
          <div className="status-pill" style={{ '--status-color': status.color }}>
            {isProcessing && <span className="spinner" style={{ width: 12, height: 12 }} />}
            <span className="status-text">{status.text}</span>
          </div>
          {isProcessing && (
            <span className="elapsed">{formatTime(elapsedTime)}</span>
          )}
          <button className="new-btn" onClick={onNewResearch}>+ New Research</button>
        </div>
      </div>

      {/* Processing state */}
      {isProcessing && (
        <div className="processing-view fade-up">
          <div className="processing-card">
            <div className="pulse-ring" />
            <div className="processing-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="36" height="36">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
              </svg>
            </div>
            <h3>Researching your topic…</h3>
            <p>Searching Semantic Scholar, fetching papers, comparing web sources.</p>
            <div className="progress-steps">
              {['Searching academic papers', 'Building FAISS index', 'Searching web sources', 'Comparing & synthesizing'].map((step, i) => (
                <div key={step} className="step-item">
                  <div className="step-dot" style={{ animationDelay: `${i * 0.3}s` }} />
                  <span>{step}</span>
                </div>
              ))}
            </div>
            <div className="typing-indicator">
              <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
            </div>
          </div>
        </div>
      )}

      {/* Failed state */}
      {result?.status === 'failed' && (
        <div className="failed-view fade-up">
          <div className="failed-card">
            <span className="failed-icon">⚠️</span>
            <h3>Research Failed</h3>
            <p>{result.results || 'An unexpected error occurred. Please try again.'}</p>
            <button className="retry-btn" onClick={onNewResearch}>Try Again</button>
          </div>
        </div>
      )}

      {/* Completed: render markdown result */}
      {result?.status === 'completed' && result?.results && (
        <div className="result-view fade-up">
          <div className="markdown-body">
            <ReactMarkdown>{result.results}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
