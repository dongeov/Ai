# AI Chatbox v3.2.0

Hệ thống RAG (Retrieval-Augmented Generation) với **Cloud LLM MiMo-V2.5-free** (primary) + **LM Studio local** (fallback), ChromaDB, và Flask.
> Cloud model chính: `mimo-v2.5` qua `https://opencode.ai/zen/go/v1/chat/completions` (base `https://opencode.ai/zen/go`), dùng cùng API key với `mimo-v2.5`. Khi gặp `CreditsError`/`Insufficient balance` sẽ **lập tức fallback** sang local.

## Kiến trúc

```
Flask UI (HTML5 + CSS3 + Vanilla JS)
    |
RAGChatbot (app.py)
    |
    |-- LLM Router (priority strategy)
    |     |-- Cloud: MiMo-V2.5-free via opencode.ai/zen API (priority=1, primary, 8 replicas)
    |     |-- Local: LM Studio qwen/qwen3.5-9b (priority=2, fallback với circuit breaker + instant billing fallback)
    |     |-- Vision/Image: always local LM Studio
    |
    |-- Embeddings: LM Studio local (bge-m3)
    |-- Vector DB: ChromaDB + BM25 + Hybrid Search
    |-- Advanced RAG: Reranker, RelevanceJudge, MMR, HyDE
    |-- SAG: Structured Augmented Generation
    ```

## Tính năng

### 1. Chat với Streaming
- Gửi câu hỏi, nhận phản hồi real-time qua SSE
- Hỗ trợ Markdown + KaTeX (công thức toán học)
- Lịch sử hội thoại (tối đa 20 tin nhắn)
- Hiển thị nguồn tham khảo kèm độ tương đồng

### 2. Xử lý dữ liệu (dataraw/ -> Chroma)
- Đọc file từ `data/` (PDF, DOCX, PPTX, TXT, MD, CSV, image)
- Chuyển đổi thành Markdown, lưu vào `dataraw/`
- Chia chunk: Recursive (mặc định) hoặc Semantic Chunking
- Phân tích chunk bằng LLM (tùy chọn): tóm tắt, keywords, topic, connections
- Embed song song với `ThreadPoolExecutor`
- Lưu vào ChromaDB với dedup bằng MD5 hash

### 3. Tìm kiếm đa chế độ
| Chế độ | Mô tả |
|--------|-------|
| `vector` | Cosine similarity trên ChromaDB |
| `hybrid` | Vector + BM25, kết hợp bằng Reciprocal Rank Fusion |

- **MMR**: Giảm trùng lặp, đa dạng hóa kết quả (lambda=0.5)
- **BM25**: OKapi BM25, tokenize regex, tự động khởi tạo từ Chroma
- **Hybrid search**: Weighted fusion hoặc RRF (k=60)

### 4. Quản lý Obsidian Vault
- Đọc tất cả notes `.md` từ vault (bỏ qua `.obsidian`, `.git`, `node_modules`)
- Parse frontmatter, tags (`#tag`), wiki links (`[[link]]`)
- Sync notes vào ChromaDB
- Export tri thức từ Chroma sang Obsidian:
  - `Chunks/`: mỗi chunk là một file `.md` với metadata
  - `Knowledge Graph/`: đồ thị tri thức, index, liên kết

### 5. Upload file
- Kéo thả hoặc chọn file (txt, md, pdf, docx, pptx, code, csv, json...)
- Xử lý: classify -> clean -> split -> embed -> lưu Chroma

### 6. Research Agent
- Lập kế hoạch nghiên cứu tự động bằng LLM
- Tìm kiếm DuckDuckGo, fetch trang, phân tích nội dung
- Lọc kết quả bằng embedding similarity (threshold 0.15)
- Phát hiện lỗ hổng kiến thức, lặp lại tối đa 2 vòng
- Tổng hợp thành bài viết, lưu vào ChromaDB

### 7. Quản lý Database
- Xem thông tin collection (name, vectors count, status, path)
- Xóa toàn bộ collection

### 8. Offline hoàn toàn (LM Studio)
- Không phụ thuộc cloud API (đã loại bỏ Gemini, Google GenAI)
- Tất cả LLM + Embedding qua LM Studio local (port 1234)
- Đồng bộ streaming qua `httpx.Client.stream()` với SSE

## API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/` | Trang chủ |
| GET | `/api/status` | Trạng thái LM Studio + Chroma |
| GET | `/api/stats` | Số messages + số vectors |
| POST | `/api/clear` | Xóa hội thoại |
| POST | `/api/chat` | Chat streaming (SSE) |
| POST | `/api/process/dataraw` | Xử lý data/ -> Chroma |
| POST | `/api/process/obsidian` | Sync Obsidian -> Chroma |
| POST | `/api/process/upload` | Upload file -> Chroma |
| POST | `/api/research` | Research Agent |
| GET | `/api/db/info` | Thông tin Chroma |
| POST | `/api/db/clear` | Xóa Chroma |
| GET | `/api/obsidian/info` | Thông tin Obsidian vault |
| POST | `/api/export` | Export Chroma -> Obsidian |

## Cấu hình (.env)

```
# Cloud LLM (primary) — mimo-v2.5 via Zen
# Base URL https://opencode.ai/zen → client tự nối /v1/chat/completions
# Nếu bạn điền full https://opencode.ai/zen/v1/chat/completions sẽ được normalize về base
LLM_CLOUD_ENABLED=true
LLM_CLOUD_URL=https://opencode.ai/zen
LLM_CLOUD_MODEL=mimo-v2.5
LLM_CLOUD_API_KEY=<your-api-key>
LLM_CLOUD_REPLICAS=8
LLM_STRATEGY=priority              # cloud=1 > local=2; billing error → instant open circuit 300s → fallback

# Local fallback (LM Studio)
LM_STUDIO_HOST=http://localhost:1234/v1
LLM_ENDPOINTS=http://localhost:1234|qwen/qwen3.5-9b|8

# Embedding (local only)
EMBEDDING_MODEL=text-embedding-bge-m3
EMBEDDING_DIM=1024

# RAG accuracy
RETRIEVAL_TOP_K=12
MAX_CONTEXT_CHARS=60000
USE_RERANKER=true
USE_RELEVANCE_JUDGE=true
```

## Cấu trúc thư mục

```
ai-chatbox/
├── app.py                    # Flask app (RAGChatbot + REST API)
├── run.py                    # Launcher (check LM Studio + start Flask)
├── requirements.txt          # Dependencies
├── pyproject.toml            # Ruff, pytest, mypy config
├── .pre-commit-config.yaml   # Pre-commit hooks
├── data/                     # Data gốc + Obsidian vault
│   ├── *.md, *.pdf, *.docx  # Source knowledge files
│   └── obsidian_vault/       # Obsidian vault mẫu
├── dataraw/                  # Markdown đã convert từ data/
├── models/chroma_db/         # ChromaDB persistent storage
├── scripts/
│   ├── master.bat            # Menu tổng (Flask, test, lint, data pipeline)
│   ├── clean.bat             # Dọn dẹp (cache, data, chroma)
│   ├── process_knowledge.py  # data/ -> dataraw/
│   ├── process_data.py       # dataraw/ -> Chroma
│   └── watch.py              # File watcher (auto-process)
├── docs/                     # Documentation
│   ├── CAC_DH_DOWNLOAD_MODEL_GEMMA.md
│   └── SYSTEM_STATUS.md
├── templates/
│   └── index.html            # Flask Jinja2 template
├── static/
│   ├── style.css             # CSS dark theme
│   └── script.js             # Vanilla JS frontend
├── src/
│   ├── __init__.py
│   ├── config.py             # Pydantic settings
│   ├── embeddings/
│   │   ├── __init__.py
│   │   └── embedding_manager.py
│   ├── chroma_pipeline/
│   │   ├── __init__.py
│   │   ├── chroma_store.py
│   │   ├── bm25_retriever.py
│   │   └── hybrid_search.py
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   ├── classifier.py
│   │   ├── cleaner.py
│   │   ├── file_reader.py
│   │   ├── splitter.py
│   │   └── semantic_chunker.py
│   ├── search/
│   │   ├── __init__.py
│   │   ├── reranker.py
│   │   └── query_transformer.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── research_agent.py
│   │   └── conversation_memory.py
│   ├── data_pipeline/
│   │   ├── __init__.py
│   │   └── knowledge_pipeline.py
│   ├── obsidian/
│   │   ├── __init__.py
│   │   └── obsidian_reader.py
│   └── utils/
│       ├── __init__.py
│       ├── hybrid_llm.py
│       ├── cache.py
│       ├── helpers.py
│       ├── monitoring.py
│       ├── logging_setup.py
│       └── exceptions.py
└── tests/
    ├── test_preprocessing.py
    ├── test_embeddings.py
    ├── test_chroma.py
    ├── test_search.py
    └── test_utils.py
```

## Nâng cấp gần đây

### v3.1 — Flask migration (2026-05)
| Thay đổi | Chi tiết |
|----------|----------|
| Streamlit -> Flask | `app.py` chuyển từ Streamlit sang Flask + REST API |
| Server-side sessions | `flask-session` filesystem-based sessions |
| SSE streaming | Chat streaming qua Server-Sent Events (fetch + ReadableStream) |
| Frontend mới | HTML5 + CSS3 + Vanilla JS (~1500 dòng tổng), không framework |
| KaTeX + Chart.js | Render toán học và biểu đồ trực tiếp |
| Dark theme | CSS variables, responsive layout |
| File upload UI | Drag & drop, file list, progress |
| Database modal | Xem thông tin Chroma, xóa từ UI |
| Status polling | Tự động kiểm tra LM Studio + Chroma mỗi 15s |

### v3.0 — Offline-only (2026-05)
| Thay đổi | Chi tiết |
|----------|----------|
| Loại bỏ Gemini | Xóa `google-genai`, fallback, `check_connection` Gemini |
| Đồng bộ streaming | `stream_generate()` dùng `httpx.Client` thay vì async |
| Đơn giản hóa client | HybridLLMClient chỉ còn LM Studio methods |
| Loại bỏ async | Xóa `stream_generate_async`, `generate_async`, `check_connection_async` |

### v2.0 (trước đó)
- Hợp nhất codebase, chỉ ChromaDB, một model embedding + một model LLM
- Embedding refactor: `concurrent.futures.ThreadPoolExecutor`
- Unit tests + static analysis (ruff, mypy)
- Pre-commit hooks

## Chạy

```bash
# Yêu cầu: LM Studio đang chạy local port 1234

# Cài đặt
pip install -r requirements.txt

# Chạy Flask app
python app.py
# -> http://localhost:5000

# Hoặc dùng menu
scripts\master.bat
# Chọn [1] Flask UI

# Test
pytest tests/ -v
```
