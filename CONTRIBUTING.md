# Contributing to Deep Research Analysis

Thank you for your interest in contributing! This guide will get you set up quickly.

---

## Ways to Contribute

- **Bug fixes** — find and fix issues
- **New features** — add capabilities from the Good First Issues list
- **Documentation** — improve READMEs, add docstrings, write tutorials
- **Tests** — increase test coverage for the ranking algorithm and agents
- **Performance** — optimize slow paths (e.g., batch cross-encoder inference)

---

## Good First Issues

| Issue | Area | Difficulty |
|---|---|---|
| Unit tests for `ranker.py` signal functions | Backend / Testing | Easy |
| Dark/light theme toggle | Frontend / CSS | Easy |
| Export results as DOCX | Frontend / Backend | Medium |
| Exponential backoff for Semantic Scholar rate limits | Backend | Medium |
| Abstract language detection | Backend / NLP | Medium |
| Streaming LLM responses via SSE | Full-stack | Hard |

---

## Development Setup

### 1. Fork and clone
```bash
git clone https://github.com/<your-username>/Deep_Research_Analysis.git
cd Deep_Research_Analysis
```

### 2. Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

Create `backend/.env` (copy from `.env.example` if available):
```env
MONGODB_URI=...
GOOGLE_API_KEY=...
TAVILY_API_KEY=...
SEMANTIC_SCHOLAR_API_KEY=...
GEMINI_MODEL=gemini-2.0-flash
```

```bash
uvicorn app.main:app --reload
```

### 3. Frontend
```bash
cd ../frontend
npm install
npm run dev
```

---

## Branching Convention

| Branch prefix | When to use |
|---|---|
| `feat/` | New feature |
| `fix/` | Bug fix |
| `docs/` | Documentation only |
| `refactor/` | Code cleanup, no behaviour change |
| `test/` | Adding or fixing tests |

Examples: `feat/docx-export`, `fix/ranker-edge-case`, `docs/api-reference`

---

## Commit Messages

Follow Conventional Commits:

```
feat(ranker): add BM25 hybrid scoring signal
fix(frontend): PDF iframe not removed after print dialog
docs(readme): add architecture mermaid diagram
test(ranker): add unit tests for citation_score()
```

---

## Pull Request Process

1. Open a PR against `main`
2. Fill in the PR template completely
3. Ensure there are no merge conflicts
4. Link the related issue using `Closes #<issue-number>`
5. A maintainer will review and merge within a few days

---

## Code Style

**Python (backend)**
- Follow PEP 8
- Use type hints for all function signatures
- Add docstrings to public functions (Google style)
- Keep functions focused — max ~50 lines

**JavaScript (frontend)**
- Use functional React components with hooks
- Keep components small and focused
- Use `useCallback` for event handlers passed as props
- CSS: keep styles in the matching `.css` file, no inline styles

---

## Project Structure Quick Reference

```
backend/app/services/ranker.py         <- ranking algorithm
backend/app/services/deep_research_agent.py  <- 5-phase pipeline
backend/app/services/research_agent.py       <- quick mode
frontend/src/pages/ResearchPage.jsx    <- main results UI
frontend/src/pages/HomePage.jsx        <- landing page
frontend/src/styles/                   <- all CSS
```

---

## Questions?

Open a [GitHub Discussion](https://github.com/deepak8186863620/Deep_Research_Analysis/discussions) or create an issue with the `question` label.