// pages/ResearchPage.jsx
// PURPOSE: The results page shown after a research task is submitted.
// It polls the backend every 3 seconds until status = "completed" or "failed",
// then renders the final markdown report with copy, export, and share features.

import { useState, useEffect, useRef, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { getResearchTask } from '../services/api';
import '../styles/ResearchPage.css';

const POLL_INTERVAL = 3000; // ms between status checks

const STATUS_CONFIG = {
  pending:    { text: 'Queued',      color: '#9aa0b4', icon: '⏳' },
  processing: { text: 'Researching', color: '#4a90d9', icon: '🔍' },
  completed:  { text: 'Complete',    color: '#4caf8a', icon: '✓'  },
  failed:     { text: 'Failed',      color: '#e05c5c', icon: '✕'  },
};

const PROCESSING_STEPS = [
  { label: 'Searching academic papers', icon: '📚' },
  { label: 'Building semantic index',   icon: '🧠' },
  { label: 'Fetching web sources',      icon: '🌐' },
  { label: 'Comparing & synthesizing',  icon: '⚗️'  },
];

function CopyIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
      <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
    </svg>
  );
}
function CheckIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width="16" height="16">
      <polyline points="20 6 9 17 4 12"/>
    </svg>
  );
}
function DownloadIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
    </svg>
  );
}
function PdfIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
      <line x1="9" y1="13" x2="15" y2="13"/>
      <line x1="9" y1="17" x2="15" y2="17"/>
      <line x1="9" y1="9" x2="11" y2="9"/>
    </svg>
  );
}

export default function ResearchPage({ task, onNewResearch, onTaskUpdate }) {
  const [result, setResult]       = useState(task);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [copied, setCopied]       = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const timerRef = useRef(null);
  const pollRef  = useRef(null);
  const stepRef  = useRef(null);

  // Polling: check task status every 3 seconds until done
  useEffect(() => {
    if (!task?.id) return;
    setResult(task);
    setElapsedTime(0);
    setActiveStep(0);

    // Start elapsed time counter
    timerRef.current = setInterval(() => setElapsedTime(t => t + 1), 1000);

    // Animate progress steps while processing
    stepRef.current = setInterval(() => {
      setActiveStep(s => (s + 1) % PROCESSING_STEPS.length);
    }, 3000);

    const poll = async () => {
      try {
        const updated = await getResearchTask(task.id);
        setResult(updated);
        if (onTaskUpdate) onTaskUpdate(updated);
        if (updated.status === 'completed' || updated.status === 'failed') {
          clearInterval(timerRef.current);
          clearInterval(pollRef.current);
          clearInterval(stepRef.current);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    };

    poll();
    pollRef.current = setInterval(poll, POLL_INTERVAL);

    return () => {
      clearInterval(timerRef.current);
      clearInterval(pollRef.current);
      clearInterval(stepRef.current);
    };
  }, [task?.id]);

  const handleCopy = useCallback(() => {
    if (result?.results) {
      navigator.clipboard.writeText(result.results).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      });
    }
  }, [result?.results]);

  const handleDownload = useCallback(() => {
    if (!result?.results) return;
    const blob = new Blob([result.results], { type: 'text/markdown' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `research-${result.topic?.slice(0, 30).replace(/\s+/g, '-')}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }, [result]);

  const handleDownloadPDF = useCallback(() => {
    if (!result?.results) return;

    // Grab the already-rendered markdown HTML from the DOM
    const markdownEl = document.querySelector('.markdown-body');
    if (!markdownEl) return;

    const topicSafe = result.topic?.slice(0, 60) || 'Research Report';
    const dateStr   = new Date().toLocaleDateString('en-US', {
      year: 'numeric', month: 'long', day: 'numeric',
    });

    // Build a self-contained HTML document for the print iframe
    const printHTML = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>${topicSafe}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Inter', system-ui, sans-serif;
      font-size: 11pt;
      line-height: 1.75;
      color: #1a1d27;
      background: #fff;
      padding: 0;
    }

    /* Cover strip */
    .pdf-cover {
      background: linear-gradient(135deg, #1e2235 0%, #252a3d 100%);
      color: #fff;
      padding: 36px 48px 28px;
      margin-bottom: 32px;
    }
    .pdf-cover .label {
      font-size: 9pt;
      font-weight: 600;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: #6b9bd2;
      margin-bottom: 10px;
    }
    .pdf-cover h1 {
      font-size: 20pt;
      font-weight: 700;
      line-height: 1.3;
      color: #fff;
      margin-bottom: 12px;
    }
    .pdf-cover .meta {
      font-size: 9pt;
      color: #8a90a8;
    }

    /* Content area */
    .pdf-body {
      padding: 0 48px 48px;
    }

    h1 { font-size: 18pt; font-weight: 700; margin: 28px 0 12px; color: #1a1d27; }
    h2 {
      font-size: 13pt; font-weight: 700;
      margin: 28px 0 10px;
      color: #1a1d27;
      padding-bottom: 6px;
      border-bottom: 2px solid #e2e5ef;
    }
    h3 { font-size: 11pt; font-weight: 600; margin: 18px 0 8px; color: #3a6ea8; }
    h4 { font-size: 10pt; font-weight: 600; margin: 12px 0 6px; color: #555; }

    p  { margin-bottom: 12px; color: #2d3148; }
    strong { font-weight: 600; color: #1a1d27; }
    em { font-style: italic; color: #6a5acd; }

    ul, ol { margin: 0 0 12px 24px; color: #2d3148; }
    li { margin-bottom: 5px; }
    li::marker { color: #4a90d9; }

    code {
      background: #f3f4f8;
      border: 1px solid #dde0ec;
      padding: 1px 5px;
      border-radius: 4px;
      font-size: 9pt;
      color: #6a5acd;
      font-family: 'Fira Code', 'Consolas', monospace;
    }
    pre {
      background: #f3f4f8;
      border: 1px solid #dde0ec;
      border-radius: 8px;
      padding: 14px 16px;
      overflow: hidden;
      margin: 0 0 12px;
      page-break-inside: avoid;
    }
    pre code { background: none; border: none; padding: 0; color: #1a1d27; }

    blockquote {
      border-left: 3px solid #4a90d9;
      padding: 6px 14px;
      margin: 0 0 12px;
      color: #444;
      font-style: italic;
      background: rgba(74,144,217,0.05);
      border-radius: 0 6px 6px 0;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      margin: 0 0 16px;
      font-size: 9.5pt;
      page-break-inside: avoid;
    }
    th {
      background: #f3f4f8;
      border: 1px solid #dde0ec;
      padding: 7px 10px;
      text-align: left;
      font-weight: 600;
      color: #1a1d27;
    }
    td {
      border: 1px solid #dde0ec;
      padding: 7px 10px;
      color: #2d3148;
    }
    tr:nth-child(even) td { background: #fafbfd; }

    hr { border: none; border-top: 1px solid #e2e5ef; margin: 20px 0; }
    a  { color: #4a90d9; text-decoration: underline; }

    @page {
      margin: 14mm 0;
      size: A4;
    }
    h2, h3 { page-break-after: avoid; }
  </style>
</head>
<body>
  <div class="pdf-cover">
    <div class="label">Deep Research Analysis</div>
    <h1>${topicSafe}</h1>
    <div class="meta">Generated on ${dateStr}</div>
  </div>
  <div class="pdf-body">
    ${markdownEl.innerHTML}
  </div>
</body>
</html>`;

    // Inject into a hidden iframe and trigger print
    const iframe = document.createElement('iframe');
    iframe.style.cssText = 'position:fixed;top:-9999px;left:-9999px;width:0;height:0;border:none;';
    document.body.appendChild(iframe);

    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
    iframeDoc.open();
    iframeDoc.write(printHTML);
    iframeDoc.close();

    // Wait for fonts/images to load before printing
    iframe.onload = () => {
      setTimeout(() => {
        iframe.contentWindow.focus();
        iframe.contentWindow.print();
        // Remove the iframe after the print dialog closes
        setTimeout(() => document.body.removeChild(iframe), 1000);
      }, 400);
    };
  }, [result]);

  const status = STATUS_CONFIG[result?.status] || STATUS_CONFIG.pending;
  const isProcessing = result?.status === 'pending' || result?.status === 'processing';

  const formatTime = (s) => s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`;

  return (
    <div className="research-page">
      {/* ── Header ── */}
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
          {result?.status === 'completed' && (
            <>
              <button id="copy-report-btn" className="action-btn" onClick={handleCopy} title="Copy markdown">
                {copied ? <CheckIcon /> : <CopyIcon />}
                <span>{copied ? 'Copied!' : 'Copy'}</span>
              </button>
              <button id="download-md-btn" className="action-btn" onClick={handleDownload} title="Download as .md">
                <DownloadIcon />
                <span>.md</span>
              </button>
              <button id="download-pdf-btn" className="action-btn action-btn--pdf" onClick={handleDownloadPDF} title="Download as PDF">
                <PdfIcon />
                <span>PDF</span>
              </button>
            </>
          )}
          <button id="new-research-page-btn" className="new-btn" onClick={onNewResearch}>
            + New Research
          </button>
        </div>
      </div>

      {/* ── Processing State ── */}
      {isProcessing && (
        <div className="processing-view fade-up">
          <div className="processing-card">
            <div className="pulse-ring" />
            <div className="processing-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="36" height="36">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
              </svg>
            </div>
            <h3>{result?.mode === 'deep' ? 'Deep Verification in Progress…' : 'Researching your topic…'}</h3>
            
            <div className="progress-dynamic" style={{ margin: '16px 0', padding: '12px 20px', background: 'rgba(74, 144, 217, 0.05)', borderRadius: '12px', width: '100%' }}>
              <p style={{ margin: 0, fontWeight: 500, color: 'var(--text-primary)' }}>
                {result?.progress_step || 'Initializing agents...'}
              </p>
              
              {/* Show live stats if available from deep mode */}
              {result?.progress_details && Object.keys(result.progress_details).length > 0 && (
                <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', marginTop: '12px', fontSize: '12px', color: 'var(--text-muted)' }}>
                  {result.progress_details.semantic_scholar !== undefined && <span>📚 {result.progress_details.semantic_scholar} papers</span>}
                  {result.progress_details.arxiv !== undefined && <span>🔬 {result.progress_details.arxiv} preprints</span>}
                  {result.progress_details.web_fetching !== undefined && <span>🌐 {result.progress_details.web_fetching} urls</span>}
                </div>
              )}
            </div>

            <div className="typing-indicator">
              <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
            </div>
          </div>
        </div>
      )}

      {/* ── Failed State ── */}
      {result?.status === 'failed' && (
        <div className="failed-view fade-up">
          <div className="failed-card">
            <span className="failed-icon">⚠️</span>
            <h3>Research Failed</h3>
            <p>{result.results || 'An unexpected error occurred. Please try again.'}</p>
            <button id="retry-btn" className="retry-btn" onClick={onNewResearch}>Try Again</button>
          </div>
        </div>
      )}

      {/* ── Completed: Render Markdown ── */}
      {result?.status === 'completed' && result?.results && (
        <div className="result-view fade-up">
          <div className="result-meta">
            <div className="result-meta-left">
              <span className="result-badge">
                ✅ Research Complete {result?.mode === 'deep' && '(Deep Verified)'}
              </span>
              {result.instructions && (
                <span className="result-instructions-badge" title={result.instructions}>
                  📋 Custom instructions applied
                </span>
              )}
            </div>
            <span className="result-time">Completed in {formatTime(elapsedTime)}</span>
          </div>
          <div className="markdown-body">
            <ReactMarkdown>{result.results}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
