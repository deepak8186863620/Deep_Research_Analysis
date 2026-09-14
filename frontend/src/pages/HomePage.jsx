// pages/HomePage.jsx
// PURPOSE: Beautiful dynamic home page powered by Unicorn Studio-style design.
// Features: animated typewriter heading, glowing CTA input, floating chip badges,
// stats ticker, feature cards, and a floating "status" badge.

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "../styles/HomePage.css";

// ── Icon Components ──────────────────────────────────────────────────
const SearchIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" width="20" height="20">
    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
);

const ArrowIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" width="20" height="20">
    <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
  </svg>
);

const PlusIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" width="18" height="18">
    <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
  </svg>
);

const SparkleIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14">
    <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z"/>
  </svg>
);

const AtomIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="22" height="22">
    <circle cx="12" cy="12" r="2.5"/>
    <ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(0 12 12)"/>
    <ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(60 12 12)"/>
    <ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(120 12 12)"/>
  </svg>
);

const BrainIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="22" height="22">
    <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-1.99-3.05A3 3 0 0 1 4 13a3 3 0 0 1 2-2.83v-.67a2.5 2.5 0 0 1 1.5-2.3V6.5A2.5 2.5 0 0 1 9.5 2"/>
    <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.46 2.5 2.5 0 0 0 1.99-3.05A3 3 0 0 0 20 13a3 3 0 0 0-2-2.83v-.67a2.5 2.5 0 0 0-1.5-2.3V6.5A2.5 2.5 0 0 0 14.5 2"/>
  </svg>
);

const DatabaseIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="22" height="22">
    <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5"/><path d="M3 12c0 1.66 4.03 3 9 3s9-1.34 9-3"/>
  </svg>
);

const GlobeIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="22" height="22">
    <circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/>
    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
  </svg>
);

// ── Typewriter hook ───────────────────────────────────────────────────
const WORDS = ["Research", "Discover", "Analyze", "Synthesize", "Explore"];

function useTypewriter(words, typingSpeed = 90, pauseMs = 1800, deleteSpeed = 50) {
  const [display, setDisplay] = useState("");
  const [wordIdx, setWordIdx] = useState(0);
  const [phase, setPhase]     = useState("typing");
  const [charIdx, setCharIdx] = useState(0);

  useEffect(() => {
    const word = words[wordIdx];
    if (phase === "typing") {
      if (charIdx < word.length) {
        const t = setTimeout(() => setCharIdx(i => i + 1), typingSpeed);
        return () => clearTimeout(t);
      } else {
        const t = setTimeout(() => setPhase("pause"), pauseMs);
        return () => clearTimeout(t);
      }
    }
    if (phase === "pause") {
      setPhase("deleting");
    }
    if (phase === "deleting") {
      if (charIdx > 0) {
        const t = setTimeout(() => setCharIdx(i => i - 1), deleteSpeed);
        return () => clearTimeout(t);
      } else {
        setWordIdx(i => (i + 1) % words.length);
        setPhase("typing");
      }
    }
  }, [phase, charIdx, wordIdx, words, typingSpeed, pauseMs, deleteSpeed]);

  useEffect(() => {
    setDisplay(words[wordIdx].slice(0, charIdx));
  }, [charIdx, wordIdx, words]);

  return display;
}

// ── Data ──────────────────────────────────────────────────────────────
const CHIPS = [
  { emoji: "🧬", label: "CRISPR gene editing breakthroughs" },
  { emoji: "🤖", label: "Large language models 2025" },
  { emoji: "🌍", label: "Climate change mitigation strategies" },
  { emoji: "⚛️", label: "Quantum computing progress" },
  { emoji: "💊", label: "mRNA vaccine technology" },
  { emoji: "🧠", label: "Neuroplasticity and memory" },
];

const FEATURES = [
  {
    icon: <AtomIcon />,
    title: "Semantic Scholar",
    desc: "Searches 200M+ academic papers with FAISS vector embeddings for precision retrieval.",
    color: "#6d4cff",
    delay: 0,
  },
  {
    icon: <BrainIcon />,
    title: "AI Synthesis",
    desc: "Gemini Pro distills complex findings into clear, structured research reports.",
    color: "#a855f7",
    delay: 0.1,
  },
  {
    icon: <DatabaseIcon />,
    title: "FAISS Index",
    desc: "Lightning-fast nearest-neighbor search over 50K+ paper embeddings.",
    color: "#06b6d4",
    delay: 0.2,
  },
  {
    icon: <GlobeIcon />,
    title: "Live Web Search",
    desc: "Augments academic papers with real-time web context for up-to-date insights.",
    color: "#f472b6",
    delay: 0.3,
  },
];

const STATS = [
  { value: "200M+", label: "Papers indexed" },
  { value: "50K+",  label: "Vector embeddings" },
  { value: "<2s",   label: "Retrieval speed" },
  { value: "98%",   label: "Citation accuracy" },
];

// ── Main Component ────────────────────────────────────────────────────
export default function HomePage({ onSubmit, isLoading }) {
  const [topic, setTopic]                 = useState("");
  const [instructions, setInstructions]   = useState("");
  const [showInstructions, setShowInstructions] = useState(false);
  const [focused, setFocused]             = useState(false);
  const typewriterText                    = useTypewriter(WORDS);
  const textareaRef                       = useRef(null);

  const handleSubmit = () => {
    const trimmed = topic.trim();
    if (!trimmed || isLoading) return;
    onSubmit(trimmed, instructions.trim());
    setTopic("");
    setInstructions("");
    setShowInstructions(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleChipClick = (label) => {
    setTopic(label);
    textareaRef.current?.focus();
  };

  return (
    <div className="home-page">

      {/* ── Status badge ── */}
      <motion.div
        className="status-badge"
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
      >
        <span className="status-dot" />
        <SparkleIcon />
        <span>Powered by Unicorn Studio + Gemini Pro</span>
      </motion.div>

      {/* ── Hero heading ── */}
      <motion.div
        className="hero"
        initial={{ opacity: 0, y: 28 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.2 }}
      >
        <h1 className="hero-title">
          <span className="hero-gradient">
            {typewriterText}
            <span className="cursor" aria-hidden="true">|</span>
          </span>
          <br />
          <span className="hero-plain">Anything. Instantly.</span>
        </h1>
        <p className="hero-subtitle">
          Ask a question. I'll search 200M+ papers, synthesize insights with AI,
          and generate a comprehensive, cited report in seconds.
        </p>
      </motion.div>

      {/* ── Stats ticker ── */}
      <motion.div
        className="stats-row"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.35 }}
      >
        {STATS.map((s, i) => (
          <div key={i} className="stat-item">
            <span className="stat-value">{s.value}</span>
            <span className="stat-label">{s.label}</span>
          </div>
        ))}
      </motion.div>

      {/* ── Research input ── */}
      <motion.div
        className="input-wrapper"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.45 }}
      >
        <div className={`input-box ${focused ? "focused" : ""} ${isLoading ? "loading" : ""}`}>
          <div className="input-icon"><SearchIcon /></div>
          <textarea
            id="research-topic-input"
            ref={textareaRef}
            className="topic-input"
            placeholder="Ask a research question… (e.g. 'What are the latest breakthroughs in mRNA technology?')"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            rows={1}
            disabled={isLoading}
          />
          <div className="input-right">
            <button
              className="add-btn"
              onClick={() => setShowInstructions(!showInstructions)}
              title="Add instructions"
            >
              <PlusIcon />
            </button>
            <button
              id="submit-research-btn"
              className={`send-btn ${topic.trim() && !isLoading ? "active" : ""}`}
              onClick={handleSubmit}
              disabled={!topic.trim() || isLoading}
              title="Start deep research"
            >
              {isLoading
                ? <span className="spinner" style={{ width: 18, height: 18 }} />
                : <ArrowIcon />
              }
            </button>
          </div>
        </div>

        <AnimatePresence>
          {showInstructions && (
            <motion.div
              className="instructions-panel"
              initial={{ opacity: 0, height: 0, marginTop: 0 }}
              animate={{ opacity: 1, height: "auto", marginTop: 8 }}
              exit={{ opacity: 0, height: 0, marginTop: 0 }}
            >
              <textarea
                className="instructions-input"
                placeholder="Custom instructions (e.g. 'Focus on 2024–2025 papers only', 'Explain like I'm 5')…"
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                rows={2}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* ── Suggestion chips ── */}
      <motion.div
        className="chips"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.55 }}
      >
        {CHIPS.map((chip) => (
          <button
            key={chip.label}
            className="chip"
            onClick={() => handleChipClick(chip.label)}
          >
            <span className="chip-emoji">{chip.emoji}</span>
            <span>{chip.label}</span>
          </button>
        ))}
      </motion.div>

      {/* ── Feature cards ── */}
      <motion.div
        className="features-row"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.65 }}
      >
        {FEATURES.map((f, i) => (
          <motion.div
            key={i}
            className="feature-card"
            whileHover={{ scale: 1.04, y: -4 }}
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
            style={{ "--card-color": f.color }}
          >
            <div className="feature-icon" style={{ color: f.color }}>{f.icon}</div>
            <h3 className="feature-title">{f.title}</h3>
            <p className="feature-desc">{f.desc}</p>
          </motion.div>
        ))}
      </motion.div>

      {/* ── Footer disclaimer ── */}
      <motion.p
        className="disclaimer"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.8 }}
      >
        Deep Research uses Semantic Scholar + arXiv + Live Web Search to synthesize academic and current findings. Results include citations.
      </motion.p>
    </div>
  );
}
