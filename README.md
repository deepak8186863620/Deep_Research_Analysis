# Deep Research Analysis

An advanced, AI-powered research assistant and synthesis pipeline that intelligently retrieves, ranks, and analyzes information from academic papers and web sources. This project provides a sophisticated web interface paired with a powerful LangGraph-based backend to automate complex research workflows.

**Created by: Deepak Prajapati & Nishanth**

---

## 🌟 Key Features

### Intelligent Backend (RAG & Multi-Agent)
- **Multi-Agent Research Pipeline:** Utilizes **LangGraph** to coordinate search, retrieval, synthesis, and fact-checking workflows.
- **Academic & Web Search:** Integrates with **Arxiv** for academic papers and **Tavily** for real-time web search.
- **Custom Reranking & Retrieval:** Employs a hybrid search strategy (BM25 + dense embeddings via FAISS & Sentence Transformers) along with custom multi-signal ranking algorithms to ensure top relevance.
- **AI Synthesis:** Powered by **Google Gemini** (via `langchain-google-genai`) to synthesize research and generate comprehensive insights.

### Modern, Premium Frontend
- **High-Performance UI:** Built with **React 19** and **Vite** for blazing fast performance.
- **Dynamic Animations:** Features smooth transitions and sophisticated UI elements using **Framer Motion**.
- **Interactive Data Visualization:** Includes interactive particle network backgrounds to visualize AI data processing.
- **Rich Text Rendering:** Uses **React Markdown** to beautifully format generated research reports and analysis.

---

## 🛠️ Technology Stack

**Frontend:**
- React (v19)
- Vite
- Framer Motion
- React Router DOM
- React Markdown

**Backend:**
- Python & FastAPI
- LangChain & LangGraph
- Google Gemini API (`langchain-google-genai`)
- FAISS & Sentence Transformers
- Tavily API & Arxiv API

---

## 🚀 Getting Started

### Prerequisites
- Node.js (v18+)
- Python (3.9+)
- API Keys for Google Gemini and Tavily Search.

### 1. Clone the Repository
```bash
git clone https://github.com/deepak8186863620/Deep_Research_Analysis.git
cd Deep_Research_Analysis
```

### 2. Backend Setup
Navigate to the backend directory, create a virtual environment, and install dependencies:
```bash
cd backend
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

**Environment Variables (`backend/.env`):**
Create a `.env` file in the `backend` directory and add your API keys:
```env
GOOGLE_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key
# Add any other required environment variables here
```

**Run the Backend Server:**
```bash
uvicorn app.main:app --reload
```
The backend API will run at `http://localhost:8000`.

### 3. Frontend Setup
Open a new terminal, navigate to the frontend directory, and install dependencies:
```bash
cd frontend
npm install
```

**Run the Development Server:**
```bash
npm run dev
```
The frontend will be available at `http://localhost:5173`.

---

## 📂 Project Structure

```text
Deep_Research_Analysis/
├── backend/                # FastAPI application, LangGraph agents, and API endpoints
│   ├── app/                # Core application logic (routers, services, prompts, etc.)
│   ├── requirements.txt    # Python dependencies
│   └── test_*.py           # Backend test scripts
├── frontend/               # React + Vite frontend application
│   ├── src/                # React components, pages, styles, and utilities
│   ├── package.json        # Node dependencies and scripts
│   └── vite.config.js      # Vite configuration
└── docs/                   # Additional documentation
```

---

## 📝 License
This project is proprietary and confidential. All rights reserved.
