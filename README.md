<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white" />
  <img src="https://img.shields.io/badge/FAISS-0467DF?style=for-the-badge&logo=meta&logoColor=white" />
  <img src="https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
</p>

# 📰 FinNews RAG Q&A

> **An AI-powered Retrieval-Augmented Generation (RAG) system for financial news analysis and question answering.**

FinNews RAG Q&A lets you ingest financial articles from URLs or upload PDF/TXT documents, then ask natural-language questions and get AI-generated answers grounded in the actual content — not hallucinations.

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA INGESTION                           │
│                                                                 │
│   URLs / PDFs ──► Web Scraper / Loader ──► Text Splitter        │
│                        (Chunking)                               │
│                            │                                    │
│                            ▼                                    │
│                   Embedding Model ──► FAISS Vector Database      │
│               (all-MiniLM-L6-v2)        (Persistent)            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         USER FLOW                               │
│                                                                 │
│   User Question ──► Embedding Model ──► Semantic Search (FAISS) │
│                                              │                  │
│                                              ▼                  │
│                                     Retrieve Top-K Chunks       │
│                                              │                  │
│                                              ▼                  │
│                                     Prompt Template + Context   │
│                                              │                  │
│                                              ▼                  │
│                                        LLM (Gemini)             │
│                                              │                  │
│                                              ▼                  │
│                                   Grounded AI Response          │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### Backend (Python / FastAPI)
- 🔍 **RAG Pipeline** — Full Retrieval-Augmented Generation with LangChain
- 🗄️ **FAISS Vector Store** — Persistent semantic search with data saved to disk
- 🌐 **Web Scraping** — Extract articles from any URL automatically
- 📄 **PDF & TXT Upload** — Ingest documents directly via API
- 🧠 **Embedding Cache** — Singleton pattern to avoid reloading models
- 🔒 **Rate Limiting** — Protect API from abuse
- ✅ **URL Validation** — Comprehensive input validation
- 📊 **Health & Status Monitoring** — Real-time system health endpoints
- 🐳 **Docker Ready** — Full Docker Compose support

### Frontend (React / Vite)
- 💬 **Chat Interface** — Conversational Q&A with smooth animations
- 🔗 **Multi-URL Ingestion** — Process multiple articles at once
- 📤 **File Upload** — Upload PDF/TXT files directly from the UI
- 📋 **Copy to Clipboard** — One-click copy of AI responses
- 📥 **Download Conversations** — Export chat history as text files
- 🗑️ **Clear History** — Reset conversations with confirmation
- 🟢 **Real-time Status** — Live connection indicator and document count
- 🎨 **Glassmorphism Design** — Modern dark theme with glass effects

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, Vite 8, Axios, Lucide Icons |
| **Backend** | Python 3.11+, FastAPI, Uvicorn |
| **AI/ML** | LangChain, Sentence-Transformers, FAISS |
| **LLM** | Google Gemini (via OpenRouter) |
| **Embeddings** | all-MiniLM-L6-v2 (HuggingFace) |
| **Deployment** | Docker, Docker Compose |

---

## 📋 Prerequisites

- **Python** 3.11+
- **Node.js** 18+
- **OpenRouter API Key** (or Google API Key)
- 4GB RAM minimum
- 2GB disk space

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/mstfyshrqawy520-alt/FinNews-RAG-QA.git
cd FinNews-RAG-QA
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `backend/.env` and set your API key:

```env
GOOGLE_API_KEY=your_openrouter_api_key_here
```

### 4. Frontend Setup

```bash
cd frontend
npm install
```

### 5. Run the Application

**Terminal 1 — Backend:**
```bash
cd backend
python -m uvicorn main:app --reload
```
→ Backend running at: **http://127.0.0.1:8000**

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```
→ Frontend running at: **http://localhost:5173**

### Using Docker (Alternative)

```bash
docker-compose up -d
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/status` | System status & document count |
| `POST` | `/api/ingest` | Ingest article URLs |
| `POST` | `/api/upload` | Upload PDF/TXT file |
| `POST` | `/api/ask` | Ask a question |
| `POST` | `/api/admin/clear` | Clear vector store |

### Example: Ingest URLs

```bash
curl -X POST http://127.0.0.1:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://www.reuters.com/business/finance/"]}'
```

### Example: Ask a Question

```bash
curl -X POST http://127.0.0.1:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the latest financial news?", "session_id": "default"}'
```

📖 **Interactive API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📁 Project Structure

```
FinNews-RAG-QA/
├── backend/
│   ├── main.py              # FastAPI application & routes
│   ├── rag.py               # RAG pipeline & vector store management
│   ├── scraper.py           # Web scraping module
│   ├── config.py            # Configuration management
│   ├── utils.py             # Validation & rate limiting utilities
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Environment template
│   └── data/                # Persistent vector store (auto-created)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── index.css        # Global styles & design system
│   │   └── main.jsx         # Entry point
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── Dockerfile.backend       # Backend Docker image
├── Dockerfile.frontend      # Frontend Docker image
├── docker-compose.yml       # Docker Compose orchestration
├── .gitignore
└── README.md
```

---

## 🔧 Configuration

All configuration is managed via environment variables in `backend/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | — | Your OpenRouter/Google API key |
| `LLM_MODEL` | `google/gemini-3.5-flash` | LLM model to use |
| `LLM_MAX_TOKENS` | `1000` | Max tokens per response |
| `LLM_TEMPERATURE` | `0.2` | Response creativity (0-1) |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence embedding model |
| `CHUNK_SIZE` | `1000` | Text chunk size for splitting |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `RETRIEVAL_K` | `5` | Number of chunks to retrieve |
| `RATE_LIMIT_REQUESTS` | `100` | Max requests per period |
| `RATE_LIMIT_PERIOD` | `60` | Rate limit window (seconds) |

---

## 🔐 Security

- ✅ URL validation to prevent malicious input
- ✅ Input sanitization and length limits
- ✅ Rate limiting to prevent abuse
- ✅ CORS configuration for production
- ✅ Error handling without exposing sensitive info
- ✅ Environment-based configuration (no hardcoded secrets)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

**Mostafa Ali Mohamed El-Sharqawi**

- 📍 Cairo, Egypt
- 📞 +20 127 691 3999
- 📧 [mstfyshrqawy520@gmail.com](mailto:mstfyshrqawy520@gmail.com)
- 💼 [LinkedIn](https://linkedin.com/in/mostafa-el-sharqawi-66b3a7352)
- 🐙 [GitHub](https://github.com/mstfyshrqawy520-alt)
- 🌐 [Portfolio](https://mstfyshrqawy520-alt.github.io/my-Portfolio)

---

<p align="center">
  Made with ❤️ by <strong>Mostafa El-Sharqawi</strong>
</p>
