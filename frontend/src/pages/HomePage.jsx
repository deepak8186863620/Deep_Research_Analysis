// pages/HomePage.jsx
// PURPOSE: The main landing page — the "Let's jump in, Deepak" screen.
// This is what the user sees before submitting their first research query.
// It contains the centered heading, subtitle chips, and the research input bar.

import { useState } from 'react';
import '../styles/HomePage.css';

const MicIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" width="22" height="22">
    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/>
    <line x1="8" y1="23" x2="16" y2="23"/>
  </svg>
);

const ArrowIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" width="22" height="22">
    <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
  </svg>
);

const PlusIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" width="22" height="22">
    <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
  </svg>
);

const SUGGESTION_CHIPS = [
  { emoji: '🧬', label: 'CRISPR gene editing breakthroughs' },
  { emoji: '🤖', label: 'Large language models 2024' },
  { emoji: '🌍', label: 'Climate change mitigation strategies' },
  { emoji: '⚛️',  label: 'Quantum computing progress' },
  { emoji: '💊', label: 'mRNA vaccine technology' },
];

export default function HomePage({ onSubmit, isLoading }) {
  const [topic, setTopic] = useState('');
  const [instructions, setInstructions] = useState('');
  const [showInstructions, setShowInstructions] = useState(false);
  const [mode, setMode] = useState('quick'); // 'quick' or 'deep'

  const handleSubmit = () => {
    const trimmed = topic.trim();
    if (!trimmed || isLoading) return;
    onSubmit(trimmed, instructions.trim(), mode);
    setTopic('');
    setInstructions('');
    setShowInstructions(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleChipClick = (label) => {
    setTopic(label);
  };

  const toggleMode = () => {
    setMode(m => m === 'quick' ? 'deep' : 'quick');
  };

  return (
    <div className="home-page">
      {/* Greeting */}
      <div className="greeting fade-up">
        <h1 className="greeting-title">Let's dive in, Deepak</h1>
        <p className="greeting-subtitle">Ask anything. I'll research it across academic papers and the web.</p>
      </div>

      {/* Suggestion chips */}
      <div className="chips fade-up" style={{ animationDelay: '0.1s' }}>
        {SUGGESTION_CHIPS.map((chip) => (
          <button
            key={chip.label}
            className="chip"
            onClick={() => handleChipClick(chip.label)}
          >
            <span>{chip.emoji}</span>
            <span>{chip.label}</span>
          </button>
        ))}
      </div>

      {/* Research input */}
      <div className="input-wrapper fade-up" style={{ animationDelay: '0.2s' }}>
        <div className={`input-box ${isLoading ? 'loading' : ''}`}>
          {/* Left: attach / instructions toggle */}
          <button
            className="input-btn left-btn"
            onClick={() => setShowInstructions(!showInstructions)}
            title="Add specific instructions"
          >
            <PlusIcon />
          </button>

          {/* Main textarea */}
          <textarea
            id="research-topic-input"
            className="topic-input"
            placeholder="Ask a research question…"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={isLoading}
          />

          {/* Right controls */}
          <div className="input-right">
            <button 
              className={`model-badge ${mode === 'deep' ? 'deep-mode' : ''}`} 
              onClick={toggleMode}
              title={mode === 'deep' ? "Deep Verification Mode (~5 min)" : "Quick Research Mode (~1 min)"}
            >
              <span className={`model-dot ${mode === 'deep' ? 'deep-dot' : ''}`} />
              <span>{mode === 'deep' ? 'Deep Verification' : 'Quick Research'}</span>
              <svg viewBox="0 0 24 24" width="12" fill="currentColor" style={{ transform: mode === 'deep' ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>
                <path d="M7 10l5 5 5-5z"/>
              </svg>
            </button>
            <button
              className="input-btn mic-btn"
              title="Voice input"
            >
              <MicIcon />
            </button>
            <button
              className={`send-btn ${topic.trim() && !isLoading ? 'active' : ''}`}
              onClick={handleSubmit}
              disabled={!topic.trim() || isLoading}
              title="Start research"
            >
              {isLoading
                ? <span className="spinner" style={{ width: 16, height: 16 }} />
                : <ArrowIcon />
              }
            </button>
          </div>
        </div>

        {/* Optional instructions panel */}
        {showInstructions && (
          <div className="instructions-panel fade-up">
            <textarea
              className="instructions-input"
              placeholder="Add specific instructions (e.g. 'Focus only on 2023–2024 papers', 'Explain like I'm 5')…"
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              rows={2}
            />
          </div>
        )}
      </div>

      <p className="disclaimer fade-up" style={{ animationDelay: '0.3s' }}>
        Deep Research uses Semantic Scholar + live web search to synthesize academic and current findings.
      </p>
    </div>
  );
}
