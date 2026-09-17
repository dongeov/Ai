# BÁO CÁO KỸ THUẬT — AI CHATBOX v3.2.0

**Ngày:** 19 tháng 8, 2026  
**Phiên bản:** 3.2.0  
**Tác giả:** Explora AI  
**Mã dự án:** ai-chatbox  
**Đường dẫn:** `C:\Users\dongeov\Documents\ai-chatbox`

---

## MỤC LỤC

1. [Tổng quan dự án](#1-tổng-quan-dự-án)
2. [Kiến trúc hệ thống](#2-kiến-trúc-hệ-thống)
3. [Cấu trúc thư mục](#3-cấu-trúc-thư-mục)
4. [Phân tích từng module](#4-phân-tích-từng-module)
5. [Load Balancing & Auto-Failover](#5-load-balancing--auto-failover)
6. [Advanced RAG Pipeline](#6-advanced-rag-pipeline)
7. [Auto-RAG System](#7-auto-rag-system)
8. [SAG — Structured Augmented Generation](#8-sag--structured-augmented-generation)
9. [Cấu hình & Môi trường](#9-cấu-hình--môi-trường)
10. [Kiểm thử](#10-kiểm-thử)
11. [Vấn đề đã biết & Lộ trình](#11-vấn-đã-biết--lộ-trình)

---

## 1. Tổng quan dự án

**AI Chatbox** là chatbot RAG (Retrieval-Augmented Generation) tiếng Việt phục vụ Explora AI, sử dụng Cloud LLM (MiMo-V2.5) làm backend inference chính và LM Studio làm fallback local cho embedding + vision.

### Thông số kỹ thuật

| Chỉ số | Giá trị |
|--------|---------|
| Phiên bản | 3.2.0 |
| Python | 3.10+ |
| Framework | Flask 3.0+ |
| Cloud LLM | MiMo-V2.5 (opencode.ai) |
| Local LLM | LM Studio (llama.cpp) — dự phòng |
| Embedding Model | `text-embedding-bge-m3` |
| Vector DB | ChromaDB (embedded) |
| Knowledge Graph | SQLite + SQLAlchemy (SAG) |
| BM25 | underthesea (regex fallback) |
| Số file nguồn | 66 file |
| Dòng mã nguồn | 12.135 dòng |
| Dòng kiểm thử | 1.183 dòng |
| Tổng dung lượng src/ | 538.3 KB |

### Tính năng chính

- **Cloud-first LLM**: MiMo-V2.5 qua opencode.ai, LM Studio làm fallback local
- **RAG Pipeline**: Vector search + BM25 hybrid retrieval
- **Advanced RAG**: HyDE, Query Decomposition, Context Compression, Reranking
- **Self-RAG**: Relevance Judge + Faithfulness Check + Iterative Refinement
- **Auto-RAG**: Tự động kích hoạt tính năng theo độ phức tạp query
- **SAG**: Structured Augmented Generation — knowledge graph + event-entity extraction
- **Load Balancing**: Round-robin, random, least-latency, priority, least-connections
- **Model Discovery**: Tự phát hiện model đang chạy trên LM Studio
- **Auto-Failover**: Tự chuyển endpoint khi gặp lỗi network/model
- **Circuit Breaker**: Tự ngắt endpoint lỗi, tự phục hồi
- **Conversation Memory**: Token-based truncation + summary buffer
- **Persistent Chat History**: Lưu trữ conversation dài hạn bằng SQLite
- **Rate Limiting**: Token bucket — giới hạn request theo key
- **Smart Image Filter**: Phân loại ảnh đa tầng (ảnh/chứng khoán/biểu đồ/icon/logo)
- **Image Description**: Tạo mô tả ảnh bằng Vision LLM cho việc index
- **Index Checkpoint**: Khôi phục lỗi + tiếp tục indexing khi bị gián đoạn
- **SSE Progress**: Streaming tiến trình real-time khi indexing

---

## 2. Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT (Web UI)                        │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/SSE
┌───────────────────────────▼─────────────────────────────────┐
│                    Flask App (app.py)                        │
│  ┌──────────────┐  ┌────────────────┐  ┌────────────────┐  │
│  │ Rate Limiter │  │ Security       │  │ Flask-Session  │  │
│  │ (token bucket)│  │ (API key auth) │  │ (filesystem)   │  │
│  └──────────────┘  └────────────────┘  └────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│               API Routes (api.py — 1017 dòng)               │
│  /api/chat, /api/ask, /api/process/*, /api/db/*, /api/admin│
├─────────────────────────────────────────────────────────────┤
│               SAG Routes (sag_api.py — 393 dòng)            │
│  /sag/sources, /sag/search, /sag/graph, /sag/citations     │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                  RAG Chatbot Engine                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Auto-RAG (auto_rag.py)                               │   │
│  │  compute_complexity_score → Level 0-3                │   │
│  │  Level 0: baseline | Level 1: HyDE+ConvAware        │   │
│  │  Level 2: +Decompose+Rerank | Level 3: tất cả       │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Pre-Retrieval (trước khi tìm kiếm)                   │   │
│  │  QueryRouter → QueryTransformer → HyDE               │   │
│  │  → QueryDecomposition → ConversationAwareQuery       │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Retrieval (tìm kiếm)                                 │   │
│  │  Vector Search (ChromaDB) + BM25 (underthesea)      │   │
│  │  → MMR → HybridSearch                               │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Post-Retrieval (sau khi tìm kiếm)                    │   │
│  │  CrossEncoderReranker → ContextCompressor            │   │
│  │  → Lost-in-the-Middle mitigation                     │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Self-RAG                                             │   │
│  │  RelevanceJudge → FaithfulnessChecker                │   │
│  │  → Iterative Refinement (tối đa 2 lần)               │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│               Load Balancing Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Model        │  │ Service      │  │ HybridLLMClient  │  │
│  │ Discovery    │→ │ Router       │→ │ (retry+failover) │  │
│  │ (poll 10s)   │  │ (circuit brk)│  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│               SAG Engine (Structured Augmented Generation)  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Event-Entity │  │ Hybrid       │  │ Citation         │  │
│  │ Extraction   │→ │ Retriever    │→ │ Builder          │  │
│  │ (LLM-based)  │  │ (RRF merge)  │  │ (truy vết nguồn)│  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│               Cloud LLM (CHÍNH)                              │
│  MiMo-V2.5 — https://opencode.ai/zen/go (8 replicas)       │
├─────────────────────────────────────────────────────────────┤
│               LM Studio (DỰ PHƯƠNG — Embedding + Vision)    │
│  localhost:1234 — Chỉ dùng cho embedding + vision           │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Cấu trúc thư mục

```
C:\Users\dongeov\Documents\ai-chatbox\
├── app.py                      # Flask entry point
├── run.py                      # Launcher: dev + gunicorn prod
├── gunicorn.conf.py            # Production WSGI config
├── .env                        # Cấu hình (138 dòng)
├── pyproject.toml              # Metadata dự án (v3.2.0)
├── requirements.txt            # Dependencies (35 packages)
│
├── src/
│   ├── __init__.py             # Package init, version
│   ├── config.py               # pydantic-settings (368 dòng)
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── api.py              # Routes API chính (1017 dòng)
│   │   └── sag_api.py          # Routes SAG API (393 dòng)
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── rag_chatbot.py      # RAG engine chính (2618 dòng)
│   │   ├── conversation_store.py # Lưu trữ conversation (152 dòng)
│   │   ├── index_checkpoint.py # Khôi phục indexing (122 dòng)
│   │   └── index_progress.py   # SSE progress tracking (55 dòng)
│   │
│   ├── search/
│   │   ├── __init__.py
│   │   ├── auto_rag.py         # Đánh giá độ phức tạp
│   │   ├── query_router.py     # Phân loại ý định query
│   │   ├── query_transformer.py # HyDE + decomposition
│   │   ├── cross_encoder_reranker.py # BGE-reranker
│   │   ├── context_compressor.py # Nén ngữ cảnh
│   │   ├── relevance_judge.py  # Đánh giá relevance
│   │   ├── faithfulness_checker.py # Kiểm tra faithfulness
│   │   └── reranker.py         # BM25 reranker
│   │
│   ├── sag/                    # Module SAG (MỚI)
│   │   ├── __init__.py         # Package init (55 dòng)
│   │   ├── models.py           # SQLAlchemy ORM (141 dòng)
│   │   ├── database.py         # SQLite engine (58 dòng)
│   │   ├── engine_adapter.py   # Adapter SAG thống nhất (490 dòng)
│   │   ├── extraction_pipeline.py # Trích xuất event-entity (142 dòng)
│   │   ├── event_extractor.py  # Trích xuất bằng LLM (295 dòng)
│   │   ├── entity_types.py     # Hằng số loại entity (46 dòng)
│   │   ├── retrieval.py        # Thuật toán retrieval SAG (306 dòng)
│   │   ├── hybrid_retriever.py # Tổng hợp RRF (257 dòng)
│   │   ├── graph_service.py    # Hiển thị graph (236 dòng)
│   │   ├── citation.py         # Hệ thống citation (195 dòng)
│   │   └── source_manager.py   # CRUD nguồn (135 dòng)
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── conversation_memory.py # Bộ nhớ thread-safe
│   │   └── research_agent.py   # Research agent chuyên sâu
│   │
│   ├── embeddings/
│   │   ├── __init__.py
│   │   └── embedding_manager.py # Cache + failover
│   │
│   ├── chroma_pipeline/
│   │   ├── __init__.py
│   │   ├── chroma_store.py     # ChromaDB wrapper
│   │   ├── bm25_retriever.py   # BM25 tiếng Việt
│   │   └── hybrid_search.py    # Vector + BM25
│   │
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   ├── file_reader.py      # Đọc đa định dạng
│   │   ├── cleaner.py          # Làm sạch văn bản
│   │   ├── splitter.py         # Chia chunk
│   │   ├── classifier.py       # Phân loại nội dung
│   │   └── semantic_chunker.py # Chia chunk theo ngữ nghĩa
│   │
│   ├── data_pipeline/
│   │   ├── __init__.py
│   │   ├── knowledge_pipeline.py # Knowledge ingestion
│   │   ├── image_filter.py     # Lọc ảnh thông minh (461 dòng)
│   │   └── image_describer.py  # Mô tả ảnh bằng Vision LLM (270 dòng)
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── service_router.py   # Load balancing core
│   │   ├── model_discovery.py  # Phát hiện model trên LM Studio
│   │   ├── hybrid_llm.py       # LLM client + failover (460 dòng)
│   │   ├── llm_router.py       # LLM router wrapper
│   │   ├── embedding_router.py # Embedding router wrapper
│   │   ├── cache.py            # Memory + Disk cache
│   │   ├── performance.py      # Theo dõi hiệu năng
│   │   ├── exceptions.py       # Exception tùy chỉnh
│   │   ├── logging_setup.py    # Cấu hình Loguru
│   │   ├── helpers.py          # Các hàm tiện ích
│   │   ├── monitoring.py       # Giám sát hệ thống
│   │   ├── rate_limiter.py     # Token bucket rate limiter (77 dòng)
│   │   └── security.py         # Xác thực API key (39 dòng)
│   │
│   └── obsidian/
│       ├── __init__.py
│       └── obsidian_reader.py  # Đọc Obsidian vault
│
├── admin/
│   └── __init__.py             # Admin panel blueprint
│
├── tests/                      # 17 file test, 1183 dòng
│   ├── conftest.py
│   ├── test_admin.py
│   ├── test_agent.py
│   ├── test_app.py
│   ├── test_cache.py
│   ├── test_chroma.py
│   ├── test_config.py
│   ├── test_embeddings.py
│   ├── test_language_helpers.py
│   ├── test_preprocessing.py
│   ├── test_routes.py
│   ├── test_schedule.py
│   ├── test_search.py
│   ├── test_security.py
│   ├── test_service_router.py
│   └── test_utils.py
│
├── scripts/
│   ├── master.bat              # Batch orchestrator
│   ├── process_data.py         # Xử lý dữ liệu
│   ├── process_knowledge.py    # Xử lý knowledge
│   ├── ingest_sag.py           # Ingestion dữ liệu SAG
│   ├── reindex.py              # Reindex ChromaDB
│   ├── reindex_sag_to_chroma.py # Reindex SAG → ChromaDB
│   ├── hash_password.py        # Hash mật khẩu
│   ├── loadtest.py             # Kiểm thử tải
│   └── watch.py                # Theo dõi file
│
├── data/                       # Thư mục dữ liệu
├── dataraw/                    # Dữ liệu thô
├── models/                     # Lưu model + ChromaDB + SAG DB
├── static/                     # Frontend assets
└── templates/                  # HTML templates
```

---

## 4. Phân tích từng module

### 4.1 Configuration (`src/config.py` — 368 dòng)

**Framework:** pydantic-settings v2  
**Pattern:** Singleton `settings` + hằng số module backward-compatible

**Các nhóm config:**

| Nhóm | Fields | Ví dụ |
|-------|--------|---------|
| Đường dẫn | `base_dir`, `data_dir`, `dataraw_dir`, `models_dir` | `C:\...\ai-chatbox` |
| Cloud LLM | `llm_cloud_enabled`, `llm_cloud_url`, `llm_cloud_model`, `llm_cloud_api_key` | `true`, `https://opencode.ai/zen/go`, `mimo-v2.5` |
| LM Studio | `lm_studio_host`, `lm_studio_embedding_url` | `http://localhost:1234/v1` |
| LLM | `llm_model`, `llm_endpoints`, `llm_strategy` | `mimo-v2.5`, `priority` |
| LLM Load Balancing | `llm_health_check_interval`, `llm_circuit_breaker_threshold/timeout` | 30, 20, 10 |
| Embedding | `embedding_model`, `embedding_dim`, `embedding_batch_size` | `text-embedding-bge-m3`, 1024, 32 |
| Embedding LB | `embedding_endpoints`, `embedding_strategy` | `least_connections` |
| RAG | `collection_name`, `score_threshold`, `mmr_lambda` | `chatbot_docs`, 0.3, 0.5 |
| Advanced RAG | `use_reranker`, `use_context_compression`, v.v. | mặc định đều false |
| Self-RAG | `use_relevance_judge`, `use_faithfulness_check` | false, false |
| SAG | `sag_chat_enabled`, `sag_search_strategy` | true, `multi` |
| Image Filter | `image_filter_min_width/height`, `image_filter_min_entropy` | 64, 64, 3.0 |
| Model Discovery | `model_discovery_enabled`, `model_discovery_poll_interval` | false, 10 |
| App | `app_port`, `app_host`, `secret_key`, `api_key` | 5000, 0.0.0.0 |
| Workers | `relevance_judge_workers`, `chunk_analyzer_workers`, v.v. | 24, 8 |

### 4.2 Load Balancing Core (`src/utils/service_router.py`)

**Các class:**
- `ServiceEndpoint`: Trạng thái health, circuit breaker, theo dõi latency
- `ServiceRouter`: Chọn chiến lược, health check, routing model-aware

**Tính năng chính:**
- **5 chiến lược:** `round_robin`, `random`, `least_latency` (EWMA), `priority`, `least_connections`
- **Circuit breaker:** Mở sau N lỗi, tự đóng sau timeout, half-open probing
- **Health check:** Background thread poll `/v1/models` theo khoảng thời gian cấu hình
- **Model-aware select():** 4 giai đoạn chọn candidate:
  1. Healthy + circuit closed + model match
  2. ModelDiscovery xác nhận model đã load
  3. Half-open endpoints (circuit hết hạn)
  4. Bất kỳ endpoint nào có thể truy cập (biện pháp cuối cùng)

### 4.3 Model Discovery (`src/utils/model_discovery.py`)

**Mục đích:** Liên tục poll LM Studio để phát hiện model nào đang được load trên mỗi endpoint.

**Tính năng chính:**
- Background daemon thread poll `GET /v1/models` mỗi 10s
- Thread-safe với `threading.Lock`
- Kiểm tra ngay khi khởi động (thread riêng)
- Query API: `get_loaded_models()`, `is_model_available()`, `get_healthy_endpoints()`
- Thêm/xóa endpoint động: `add_endpoint()`, `remove_endpoint()`

### 4.4 LLM Client (`src/utils/hybrid_llm.py` — 460 dòng)

**Class:** `HybridLLMClient`

**Các phương thức:**

| Phương thức | Số lần retry | Failover | Ghi chú |
|--------|---------|----------|-------|
| `generate()` | 3 | Cross-endpoint | Model-aware select, exponential backoff+jitter |
| `stream_generate()` | 3 | Cross-endpoint | Ghi nhận latency token đầu tiên |
| `generate_async()` | 3 | Qua generate() | ThreadPoolExecutor wrapper |
| `stream_generate_async()` | 3 | Cross-endpoint | Retry đầy đủ với httpx.AsyncClient |

**Tính năng chính:**
- Thread-local sessions cho an toàn song song
- httpx cho HTTP async-capable
- Hằng số: tối đa 3 retry, exponential backoff (0.5-4.0s), pool maxsize 24
- Cloud LLM chính + LM Studio local fallback routing

### 4.5 Embedding Manager (`src/embeddings/embedding_manager.py`)

**Class:** `EmbeddingClient`

**Tính năng chính:**
- Thread-safe với `threading.local()` sessions
- Cache layer: MD5-keyed `embedding_cache` (DiskCache, 1000 entries)
- Xử lý batch: `ThreadPoolExecutor` với số workers tùy chỉnh (mặc định 9)
- Cross-endpoint failover với retry loop + exponential backoff
- `_select_url_with_failover(exclude)`: Bỏ qua các endpoint đã fail trước đó

### 4.6 RAG Chatbot Engine (`src/services/rag_chatbot.py` — 2618 dòng)

**Class:** `RAGChatbot`

**Luồng query (streaming):**
1. Tạo/lấy `ConversationMemory` cho session
2. Thêm tin nhắn user vào memory
3. Phân tích độ phức tạp Auto-RAG → kích hoạt tính năng
4. Biến đổi query (HyDE, conversation-aware)
5. Tạo embedding
6. Kiểm tra decomposition
7. Tìm kiếm (vector/hybrid)
8. Đánh giá relevance (tùy chọn)
9. Nén ngữ cảnh (tùy chọn)
10. Xây prompt (tiếng Việt)
11. Stream qua `llm_client.stream_generate()`
12. Thêm response assistant vào memory

**Self-RAG refinement:**
- Kiểm tra faithfulness → nếu thấp, tạo lại với hướng dẫn mạnh hơn
- Kiểm tra relevance → nếu thấp, thử lại với ngữ cảnh khác
- Tối đa 2 lần lặp

### 4.7 Auto-RAG (`src/search/auto_rag.py`)

**Mục đích:** Tự động kích hoạt các tính năng Advanced RAG dựa trên độ phức tạp của query.

**Đánh giá độ phức tạp (0-3):**

| Level | Điểm | Tính năng được kích hoạt |
|-------|-------|-----------------|
| 0 | 0-20 | Không có (baseline) |
| 1 | 21-50 | HyDE + Conversation-aware query |
| 2 | 51-80 | + Query Decomposition + Reranking |
| 3 | 81-100 | + Context Compression + Relevance Judge + Faithfulness Check |

### 4.8 Conversation Memory (`src/agent/conversation_memory.py`)

**Class:** `ConversationMemory` (dataclass thread-safe)

**Tính năng chính:**
- Thread-safe với `threading.Lock` trên tất cả thao tác
- Token-based truncation: `_estimate_tokens()` dùng `len(content) // 4`
- Summary buffer: phương thức `summarize()` (async, gọi khi tokens > 3000)
- Định dạng ngữ cảnh: Nhãn tiếng Việt
- Cách ly session: Instances riêng cho mỗi session với LRU eviction (tối đa 1000)

### 4.9 Persistent Conversation Store (`src/services/conversation_store.py` — 152 dòng) — MỚI

**Mục đích:** Lưu trữ conversation dài hạn bằng SQLite.

**Các hàm:**
- `init_db()` — Tạo bảng conversations
- `save_message()` — Lưu tin nhắn user/assistant
- `load_conversation()` — Lấy toàn bộ conversation theo ID
- `list_conversations()` — Liệt kê tất cả conversations
- `delete_conversation()` — Xóa conversation

**Tính năng chính:**
- Hàm tạo title tiếng Việt (`_generate_title()`) tự động bỏ các tiền tố câu hỏi phổ biến
- Thread-safe truy cập SQLite
- Tạo conversation ID tự động

### 4.10 Rate Limiter (`src/utils/rate_limiter.py` — 77 dòng) — MỚI

**Class:** `TokenBucket`, `RateLimiter`

**Tính năng chính:**
- Token bucket implementation thread-safe
- `acquire()` blocking/non-blocking với timeout tùy chọn
- Giới hạn rate theo key (ví dụ: theo IP address)
- Dictionary các bucket với tự động dọn dẹp

### 4.11 Security (`src/utils/security.py` — 39 dòng) — MỚI

**Các hàm:**
- `verify_password()` — Xác thực hash PBKDF2 của Werkzeug với so sánh plaintext backward-compatible
- `api_key_required` — Flask decorator bắt buộc header `X-API-Key`

### 4.12 Smart Image Filter (`src/data_pipeline/image_filter.py` — 461 dòng) — MỚI

**Mục đích:** Phân loại ảnh đa tầng trong quá trình indexing.

**Các loại phân loại:** ảnh, biểu đồ, diagram, icon, logo, trang trí

**Pipeline:**
1. Kiểm tra kích thước (tối thiểu 64x64)
2. Độ phức tạp màu sắc qua numpy
3. Phân tích entropy/edge
4. Phân loại LLM vision tùy chọn cho các trường hợp biên

**Ngưỡng tùy chỉnh:** entropy tối thiểu, tỷ lệ trắng tối đa, số màu tối thiểu

### 4.13 Image Describer (`src/data_pipeline/image_describer.py` — 270 dòng) — MỚI

**Mục đích:** Tạo mô tả ảnh bằng Vision LLM cho semantic search indexing.

**Tính năng chính:**
- Gọi model Gemma 4 Vision qua LM Studio endpoint
- Mô tả tiếng Việt (2-3 câu)
- Prompt template riêng cho từng loại ảnh:
  - Phòng/trưng bày
  - Sự kiện
  - Sản phẩm
- Thread-safe với ThreadPoolExecutor

### 4.14 Index Checkpoint (`src/services/index_checkpoint.py` — 122 dòng) — MỚI

**Mục đích:** Khôi phục lỗi + tiếp tục indexing khi bị gián đoạn.

**Tính năng chính:**
- Lưu tiến trình indexing vào file JSON (`index_progress.json`, `llm_cache.json`)
- Theo dõi các file đã index qua content hash
- Cache kết quả LLM (mô tả ảnh, phân tích chunk)
- Tránh gọi API redundantly khi resume

### 4.15 Index Progress (`src/services/index_progress.py` — 55 dòng) — MỚI

**Mục đích:** Theo dõi tiến trình SSE thread-safe cho các thao tác indexing.

**Cấu trúc dữ liệu:** `IndexProgress` dataclass với phase, total, current, file, timestamps, error

**Các hàm:** `get_progress()`, `update_progress()`, `reset_progress()`, `request_cancel()`, `is_cancelled()`

### 4.16 API Routes (`src/routes/api.py` — 1017 dòng)

**Các endpoint theo danh mục:**

| Danh mục | Endpoints | Xác thực |
|----------|-----------|------|
| Chat | `/api/chat`, `/api/ask`, `/api/ask-with-image` | API key |
| Xử lý | `/api/process/upload`, `/api/process/dataraw`, `/api/process/obsidian` | API key |
| Database | `/api/db/info`, `/api/db/clear` | API key |
| Trạng thái | `/api/status`, `/api/llm/status`, `/api/embedding/status`, `/api/performance` | Không |
| Admin | `/api/admin/*` | Session auth |
| Khác | `/api/export`, `/api/research`, `/api/settings`, `/api/schedule/*` | Linh hoạt |

### 4.17 SAG API Routes (`src/routes/sag_api.py` — 393 dòng) — MỚI

**Các endpoint:**

| Danh mục | Endpoints | Xác thực |
|----------|-----------|------|
| Nguồn | `/sag/sources` (GET/POST), `/sag/sources/<id>` (GET/PUT/DELETE) | API key |
| Tìm kiếm | `/sag/search` | API key |
| Graph | `/sag/graph/<source_id>` | API key |
| Trích dẫn | `/sag/citations` | API key |

---

## 5. Load Balancing & Auto-Failover

### 5.1 Kiến trúc

```
Request → ModelDiscovery.is_model_available(model)?
  → Có → ServiceRouter.select(model_filter=model)
    → Lọc: healthy + circuit closed + model match
    → Chiến lược: priority / least_connections / least_latency / round_robin / random
    → Gửi request
    → Thành công: record_success (reset failure_count, cập nhật EWMA)
    → Thất bại: record_failure (tăng failure_count, mở circuit nếu đủ ngưỡng)
  → Không → Thử bất kỳ endpoint nào có thể truy cập (biện pháp cuối cùng)
  → Tất cả down → raise LLMError
```

### 5.2 Trạng thái Circuit Breaker

```
CLOSED (bình thường) ──[failures >= threshold]──► OPEN (bị chặn)
    ▲                                              │
    │                                       [timeout hết hạn]
    │                                              │
    └────────[success]──────── HALF-OPEN (probing)
                                    │
                              [failure] → quay lại OPEN
```

**Cấu hình hiện tại:**
- LLM: threshold=20, timeout=10s, health_check=30s
- Embedding: threshold=10, timeout=30s, health_check=30s

### 5.3 Luồng Failover (LLM)

```
Lần 1: chọn endpoint A → fail → record_failure(A)
Lần 2: chọn endpoint B → fail → record_failure(B)
Lần 3: chọn endpoint C → fail → record_failure(C)
→ raise LLMError("Tất cả LLM endpoint đều fail")
```

**Backoff:** Exponential `0.5 * 2^attempt` giây với jitter `(0.5 + random * 0.5)`

### 5.4 Luồng Failover (Embedding)

```
Lần 1: chọn URL 1 → fail → record_failure, thêm vào tried_urls
Lần 2: chọn URL 2 (loại đã thử) → fail → record_failure
Lần 3: chọn URL 3 (loại đã thử) → fail → record_failure
→ raise EmbeddingError("Tất cả embedding endpoint đều fail")
```

### 5.5 Model Discovery

**Polling:**
- Interval: 10s (tùy chỉnh qua `MODEL_DISCOVERY_POLL_INTERVAL`)
- Endpoint: `GET /v1/models` trên mỗi URL cấu hình
- Kiểm tra ngay khi app khởi động

**Theo dõi trạng thái:**
- `is_reachable`: Server phản hồi HTTP 200
- `models`: Danh sách `ModelInfo(model_id, loaded_at)`
- `last_check`: Thời gian kiểm tra thành công cuối cùng

---

## 6. Advanced RAG Pipeline

### 6.1 Pre-Retrieval (trước khi tìm kiếm)

| Thành phần | File | Mô tả |
|-----------|------|---------|
| QueryRouter | `query_router.py` | Phân loại ý định query (factual/exploratory/comparative/conversational) |
| HyDE | `query_transformer.py` | Tạo câu trả lời giả định, embed câu đó thay vì query gốc |
| QueryDecomposition | `query_transformer.py` | Chia query phức tạp thành các câu hỏi con |
| ConversationAwareQuery | `rag_chatbot.py` | Viết lại query với ngữ cảnh hội thoại |

### 6.2 Retrieval (tìm kiếm)

| Thành phần | File | Mô tả |
|-----------|------|---------|
| Vector Search | `chroma_store.py` | ChromaDB cosine similarity |
| BM25 | `bm25_retriever.py` | Tokenization tiếng Việt (underthesea/regex) |
| Hybrid Search | `hybrid_search.py` | Kết hợp điểm vector + BM25 |
| MMR | `chroma_store.py` | Maximal Marginal Relevance cho tính đa dạng |

### 6.3 Post-Retrieval (sau khi tìm kiếm)

| Thành phần | File | Mô tả |
|-----------|------|---------|
| CrossEncoderReranker | `cross_encoder_reranker.py` | Reranking bằng BAAI/bge-reranker-v2-m3 |
| ContextCompressor | `context_compressor.py` | Nén bằng LLM + giảm thiểu lost-in-the-middle |

### 6.4 Self-RAG

| Thành phần | File | Mô tả |
|-----------|------|---------|
| RelevanceJudge | `relevance_judge.py` | LLM đánh giá ngữ cảnh có liên quan không |
| FaithfulnessChecker | `faithfulness_checker.py` | LLM kiểm tra câu trả lời có grounded trong ngữ cảnh không |
| Iterative Refinement | `rag_chatbot.py` | Tạo lại nếu faithfulness/relevance thấp |

---

## 7. Auto-RAG System

### 7.1 Đánh giá độ phức tạp

```python
score = 0
score += length_score        # 0-25 (câu hỏi dài hơn = phức tạp hơn)
score += comparison_score    # 0-20 (chứa "so sánh", "khác biệt")
score += analysis_score      # 0-20 (chứa "phân tích", "đánh giá")
score += summary_score       # 0-15 (chứa "tóm tắt")
score += question_score      # 0-10 (chứa "tại sao", "làm thế nào")
score += multi_part_score    # 0-10 (chứa "và", "còn")
```

### 7.2 Kích hoạt tính năng

| Level | Khoảng điểm | Tính năng |
|-------|-------------|----------|
| 0 | 0-20 | Baseline (không có tính năng nâng cao) |
| 1 | 21-50 | HyDE + Conversation-aware query |
| 2 | 51-80 | + Query Decomposition + Reranking |
| 3 | 81-100 | + Context Compression + Relevance Judge + Faithfulness Check |

### 7.3 Ghi đè cấu hình

Auto-RAG tự động kích hoạt tính năng bằng cách sửa đổi `AutoRAGConfig`:
- Các tính năng **bị tắt** trong `.env` sẽ **không bao giờ** được Auto-RAG bật
- Các tính năng **được bật** trong `.env` sẽ **luôn** được bật bất kể độ phức tạp
- Auto-RAG chỉ **thêm** tính năng, **không bao giờ** gỡ bỏ

---

## 8. SAG — Structured Augmented Generation

### 8.1 Tổng quan

SAG (Structured Augmented Generation) là module mới, mở rộng RAG truyền thống bằng knowledge graph/event-entity extraction. Thay vì chỉ tìm kiếm vectors, SAG trích xuất sự kiện (events) và thực thể (entities) từ documents, lưu vào SQLite knowledge graph, và sử dụng graph traversal để mở rộng kết quả tìm kiếm.

### 8.2 Kiến trúc

```
Document Chunks
      │
      ▼
┌─────────────────────────────────────────────┐
│ SAGExtractionPipeline                       │
│  EventEntityExtractor (LLM-based)           │
│  → Trích xuất events + entities mỗi chunk  │
│  → Lưu vào SQLite (SagEvent, SagEntity)     │
│  → Xây dựng associations event-entity       │
└─────────────────────┬───────────────────────┘
                      │
┌─────────────────────▼───────────────────────┐
│ SQLite Knowledge Graph                      │
│  SagSource → SagChunk → SagEvent            │
│                    ↓                        │
│              SagEntity ← SagEventEntity     │
└─────────────────────┬───────────────────────┘
                      │
┌─────────────────────▼───────────────────────┐
│ HybridRetriever (RRF merge)                 │
│  SAGRetriever: seed → expand → rank         │
│  ChromaDB: vector similarity search         │
│  → Reciprocal Rank Fusion                   │
└─────────────────────────────────────────────┘
```

### 8.3 Database Schema (SQLAlchemy ORM)

| Bảng | Mô tả | Fields chính |
|-------|---------|------------|
| `SagSource` | Metadata nguồn knowledge | id, name, description, created_at |
| `SagChunk` | Các chunk văn bản từ nguồn | id, source_id, content, chunk_index |
| `SagEvent` | Events đã trích xuất | id, source_id, chunk_id, content, category, confidence |
| `SagEntity` | Các entity nhẹ | id, name, entity_type, description |
| `SagEventEntity` | Associations event-entity | event_id, entity_id, weight, role |

### 8.4 Loại Entity

| Loại | Tiếng Việt | English |
|------|-----------|---------|
| PERSON | Người | person |
| ORGANIZATION | Tổ chức | organization |
| LOCATION | Địa điểm | location |
| CONCEPT | Khái niệm | concept |
| EVENT | Sự kiện | event |
| PRODUCT | Sản phẩm | product |
| DATE | Ngày tháng | date |
| NUMBER | Số liệu | number |
| MATERIAL | Vật liệu | material |
| PROCESS | Quy trình | process |

### 8.5 Danh mục Event

| Danh mục | Mô tả |
|----------|-------------|
| factual | Sự kiện thực tế |
| definition | Định nghĩa |
| process | Quy trình |
| comparison | So sánh |
| opinion | Ý kiến |
| causal | Nguyên nhân-kết quả |
| temporal | Thời gian |
| other | Khác |

### 8.6 Thuật toán Retrieval

1. **Trích xuất seed**: Tìm entities/events khớp với từ khóa query
2. **Mở rộng**: SQL JOIN trên entity_id để tìm events liên quan
3. **Xây hyperedge**: Hyper động kết nối các events liên quan
4. **Ranking**: Chấm điểm candidates dựa trên relevance và entity overlap
5. **RRF merge**: Kết hợp kết quả SAG với ChromaDB dùng Reciprocal Rank Fusion

### 8.7 Hệ thống Citation

- `CitationBuilder`: Xây citations từ kết quả retrieval
- `CitationParser`: Xử lý post-process câu trả lời LLM, trích xuất citation markers [1], [2], v.v.
- `Citation`: Truy vết nguồn với tên document, trang, chunk reference
- `CitationContext`: Ngữ cảnh đã định dạng với citation metadata

### 8.8 Cấu hình

```ini
SAG_CHAT_ENABLED=true
SAG_DEFAULT_SOURCE_ID=
SAG_SEARCH_STRATEGY=multi
```

**Chiến lược tìm kiếm:** `multi` (mặc định), `single`, `all`

---

## 9. Cấu hình & Môi trường

### 9.1 File `.env` (138 dòng)

```ini
# Cloud LLM (CHÍNH)
LLM_CLOUD_ENABLED=true
LLM_CLOUD_URL=https://opencode.ai/zen/go
LLM_CLOUD_MODEL=mimo-v2.5
LLM_CLOUD_REPLICAS=8

# LM Studio (LOCAL — Chỉ Embedding + Vision)
LM_STUDIO_HOST=http://localhost:1234/v1
LM_STUDIO_EMBEDDING_URL=http://localhost:1234/v1/embeddings

# LLM Load Balancing
LLM_ENDPOINTS=http://localhost:1234|qwen/qwen3.5-9b|8
LLM_STRATEGY=priority
LLM_HEALTH_CHECK_INTERVAL=30
LLM_CIRCUIT_BREAKER_THRESHOLD=20
LLM_CIRCUIT_BREAKER_TIMEOUT=10
LLM_TIMEOUT=300

# Embedding Load Balancing
EMBEDDING_ENDPOINTS=http://localhost:1234|text-embedding-bge-m3|24
EMBEDDING_STRATEGY=least_connections

# Models
LLM_MODEL=mimo-v2.5
EMBEDDING_MODEL=text-embedding-bge-m3
EMBEDDING_DIM=1024

# RAG
COLLECTION_NAME=chatbot_docs
SCORE_THRESHOLD=0.3
RETRIEVAL_TOP_K=12
MAX_CONTEXT_CHARS=60000
MMR_LAMBDA=0.5

# SAG
SAG_CHAT_ENABLED=true
SAG_SEARCH_STRATEGY=multi

# Advanced RAG (mặc định đều tắt)
USE_RERANKER=false
USE_CONTEXT_COMPRESSION=false
USE_RELEVANCE_JUDGE=false
USE_FAITHFULNESS_CHECK=false

# Image Filter
IMAGE_FILTER_MIN_WIDTH=64
IMAGE_FILTER_MIN_HEIGHT=64
IMAGE_FILTER_MIN_ENTROPY=3.0
IMAGE_FILTER_MAX_WHITE_RATIO=0.85

# Parallel Workers
RELEVANCE_JUDGE_WORKERS=24
CONTEXT_COMPRESS_WORKERS=24
CHUNK_ANALYZER_WORKERS=24
FILE_PROCESS_WORKERS=8
IMAGE_FILTER_WORKERS=24
IMAGE_DESCRIBE_WORKERS=24
```

### 9.2 Dependencies (35 packages)

| Danh mục | Packages |
|----------|----------|
| Web | flask, flask-session, gunicorn |
| Dữ liệu | numpy, chromadb, langchain, langchain-community, langchain-text-splitters |
| HTTP | requests, httpx, beautifulsoup4, ddgs |
| ML | scikit-learn, sentence-transformers, tiktoken |
| NLP | underthesea, regex |
| Document | pillow, python-docx, python-pptx, pypdf |
| SAG | sqlalchemy, alembic |
| Config | pydantic, pydantic-settings, python-dotenv |
| Tiện ích | tqdm, tenacity, watchdog |
| Dev | taskipy, pytest, pytest-cov, ruff, pre-commit, mypy |

### 9.3 Production Server

**Gunicorn** với gthread workers:
- Workers: `2 * CPU + 1`
- Threads: 4 per worker
- Timeout: 120s
- Khởi chạy: `python run.py --prod`

---

## 10. Kiểm thử

### 10.1 Các file Test

| File | Dòng | Phạm vi |
|------|-------|----------|
| `test_admin.py` | 114 | Xác thực admin |
| `test_agent.py` | 69 | Research agent |
| `test_app.py` | 32 | Khởi tạo app |
| `test_cache.py` | 94 | Thao tác cache |
| `test_chroma.py` | 103 | Thao tác ChromaDB |
| `test_config.py` | 44 | Đọc cấu hình |
| `test_embeddings.py` | 74 | Thao tác embedding |
| `test_language_helpers.py` | 34 | Tiện ích ngôn ngữ |
| `test_preprocessing.py` | 135 | Tiền xử lý văn bản |
| `test_routes.py` | 112 | Routes API |
| `test_schedule.py` | 53 | Công việc định kỳ |
| `test_search.py` | 38 | Thao tác tìm kiếm |
| `test_security.py` | 66 | Tiện ích bảo mật |
| `test_service_router.py` | 104 | Load balancing |
| `test_utils.py` | 73 | Các hàm tiện ích |
| **TỔNG** | **1,183** | **17 file test** |

### 10.2 Công cụ

```toml
[tool.taskipy.tasks]
dev = "python run.py --dev"
lint = "ruff check src/ tests/"
format = "ruff format src/ tests/"
test = "pytest -ra -q"
typecheck = "mypy src/"

[tool.ruff]
line-length = 120
target-version = "py310"
select = ["E", "F", "W", "I", "N", "UP", "B", "SIM"]

[tool.pytest]
testpaths = ["tests"]
addopts = "-ra -q"

[tool.mypy]
python_version = "3.10"
ignore_missing_imports = true
```

---

## 11. Vấn đề đã biết & Lộ trình

### 11.1 Vấn đề đã biết

| # | Vấn đề | Mức độ | Ghi chú |
|---|--------|--------|---------|
| 1 | Version mismatch: `src/__init__.py` = 3.0.0-dev, `pyproject.toml` = 3.2.0 | Thấp | Cần đồng bộ version |
| 2 | `.env` chứa API key và admin password plaintext | Trung bình | Cần kiểm tra .gitignore đã exclude |
| 3 | ChromaDB embedded (in-process) | Trung bình | Blocking request threads. Không phù hợp multi-worker |
| 4 | Flask sessions dựa trên filesystem | Trung bình | Không share giữa các gunicorn workers. Cần Redis |
| 5 | `sentence-transformers` chưa cài | Trung bình | Reranker sẽ fail nếu enable |
| 6 | `underthesea` chưa cài | Thấp | BM25 dùng regex fallback |
| 7 | Phụ thuộc Cloud LLM (opencode.ai) | Trung bình | Cần LM Studio fallback khi mất internet |
| 8 | SAG SQLite DB lock contention | Thấp | WAL mode giúp, nhưng cần monitor khi tải lớn |

### 11.2 Lộ trình phát triển

#### Giai đoạn 1: Quick Wins (1-2 ngày)
- [ ] Đồng bộ version: cập nhật `src/__init__.py` → 3.2.0
- [ ] Tích hợp Exact Match Cache vào `HybridLLMClient.generate()`
- [ ] Tách prompt templates ra file riêng
- [ ] Kiểm tra .gitignore đã exclude .env

#### Giai đoạn 2: Semantic Cache (3-4 ngày)
- [ ] Semantic cache dựa trên ChromaDB
- [ ] Cosine similarity ≥ 0.88 → trả về cached response
- [ ] Cache invalidation + TTL

#### Giai đoạn 3: Model Router + Prompt Compression (3-4 ngày)
- [ ] Intent classifier (rule-based, zero-latency)
- [ ] Dynamic model routing (đơn giản → rule-based, phức tạp → LLM)
- [ ] Prompt compression (entropy-based)

#### Giai đoạn 4: Production Infrastructure (2-3 ngày)
- [ ] Graceful shutdown (SIGTERM handler)
- [ ] Health check endpoints (/healthz, /readyz)
- [ ] Redis cho session store + rate limiter backend
- [ ] Prometheus metrics export

#### Giai đoạn 5: Nâng cấp SAG (5-7 ngày)
- [ ] Hiển thị entity relationship (force-directed graph)
- [ ] Cross-source entity linking
- [ ] SAG + RAG unified scoring
- [ ] Tối ưu batch extraction pipeline

---

## Báo cáo kết thúc

**Trạng thái:** ✅ Dự án sẵn sàng hoạt động  
**Phiên bản:** 3.2.0  
**Modules:** 66 source files, 12.135 dòng mã nguồn  
**Tests:** 17 test files, 1.183 dòng kiểm thử  
**Dependencies:** 35 packages  
**Config:** 138 dòng .env  

**Thay đổi lớn so với v3.0.0-dev:**
- Cloud-first LLM (MiMo-V2.5) + local fallback
- Module SAG mới (12 files, 2.370+ dòng)
- Lưu trữ conversation dài hạn (persistent)
- Rate limiter + security middleware
- Smart image filter + vision describer
- Index checkpoint/resume
- SSE progress streaming

**Phiên bản:** 3.2.0  
**Ngày cập nhật báo cáo:** 19/08/2026  
