# 🚀 KẾ HOẠCH NÂNG CẤP AI CHATBOX V4

**Ngày lập kế hoạch:** 06/08/2026  
**Phiên bản hiện tại:** v3.0.0-dev  
**Mục tiêu:** Biến hệ thống RAG chatbot thành **AI Agent Platform** đa năng

---

## 📋 TỔNG QUAN CHIẾN LƯỢC

### Hiện trạng (v3.x)
- ✅ RAG hoạt động tốt với 745 vectors
- ✅ Offline hoàn toàn qua LM Studio
- ✅ Advanced features: Self-RAG, SAG, HyDE
- ⚠️ Chưa có AI Agent Orchestrator
- ⚠️ Thiếu Knowledge Graph persistent
- ⚠️ Chưa support multimodal (video/audio)
- ⚠️ Chưa có production hardening đầy đủ

### Mục tiêu nâng cấp (v4.x)
1. **AI Agent Platform** — Multi-agent orchestration
2. **Knowledge Graph Integration** — Neo4j/NetworkX persistent KG
3. **Multimodal Enhancement** — Video/audio support
4. **Production Hardening** — Monitoring, alerting, auto-scaling
5. **Advanced RAG v2** — Query planning, multi-hop reasoning

---

## 🎯 PHƯƠNG ÁN 1: AI AGENT ORCHESTRATOR (NÂNG CẤP LỚN)

### 1.1 Kiến trúc Multi-Agent System

```
┌─────────────────────────────────────────────────────────────┐
│                   AGENT PLATFORM v4                          │
├─────────────────────────────────────────────────────────────┤
│  Agent Orchestrator (Planner Agent)                         │
│  ├─ Query Analysis Agent                                    │
│  ├─ Research Agent (existing)                               │
│  ├─ Code Assistant Agent                                     │
│  ├─ Data Analyst Agent                                       │
│  └─ Creative Writer Agent                                    │
├─────────────────────────────────────────────────────────────┤
│  Communication Layer                                        │
│  ├─ Message Queue (Redis/RabbitMQ)                          │
│  └─ Inter-agent Messaging                                    │
├─────────────────────────────────────────────────────────────┤
│  Memory Layer                                                │
│  ├─ Short-term (Conversations)                              │
│  ├─ Long-term (Vector DB + KG)                              │
│  └─ Agent-specific memory                                    │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Các Agent mới đề xuất

#### Query Analysis Agent
**Mục đích:** Phân tích query phức tạp, chia thành các sub-tasks

**Prompt mẫu:**
```python
"""
Bạn là một nhà phân tích nhiệm vụ AI.

Nhiệm vụ: Phân tích user query và xác định các bước cần thực hiện.

Input: {query}

Output format (JSON):
{
  "intent": "question|research|analysis|coding|creative",
  "complexity": "simple|medium|complex",
  "required_agents": ["agent1", "agent2"],
  "tools_needed": ["search", "code", "math"],
  "constraints": [],
  "reasoning_steps": []
}
"""
```

#### Code Assistant Agent
**Mục đích:** Hỗ trợ coding, code review, generate code snippets

**Kỹ năng:**
- Parse và hiểu code đa ngôn ngữ (Python, JS, TypeScript, Go, Rust)
- Generate code từ description
- Code review với best practices
- Explain code với ví dụ cụ thể
- Debug với log analysis

#### Data Analyst Agent
**Mục đích:** Phân tích dữ liệu, generate insights từ CSV/SQL

**Kỹ năng:**
- Parse CSV/JSON files
- SQL generation và execution
- Statistical analysis
- Visualization (Matplotlib/Plotly)
- Trend detection

### 1.3 Agent Communication Protocol

```python
# Message format cho inter-agent communication
class AgentMessage(BaseModel):
    type: str  # "task|result|error|status"
    from_agent: str
    to_agent: Optional[str] = None  # If None, broadcast
    priority: int  # 1-5 (lower = higher priority)
    payload: dict
    
# Example workflow
# User: "Analyze sales trends and predict Q4 forecast"
# ┌─────────────────────────────────────────┐
# │ Query Analysis Agent                    │
# │ - Detect: complex, multi-step           │
# │ - Plan: data analysis + forecasting     │
# │ - Route to: Data Analyst Agent          │
# └──────────────┬──────────────────────────┘
#                │
#                ↓
# ┌─────────────────────────────────────────┐
# │ Data Analyst Agent                      │
# │ 1. Load CSV files                       │
# │ 2. SQL queries → data                   │
# │ 3. Plot trends                          │
# │ 4. Generate forecast                    │
# │ 5. Share results with Planner           │
# └──────────────┬──────────────────────────┘
#                │
#                ↓
# ┌─────────────────────────────────────────┐
# │ Planner Agent → Synthesize final answer │
# └─────────────────────────────────────────┘
```

### 1.4 Implementation Plan

#### Phase 1: Core Orchestrator (2-3 weeks)
```
Week 1:
  [ ] Design agent communication protocol
  [ ] Implement AgentManager base class
  [ ] Create message queue interface
  
Week 2:
  [ ] Implement Query Analysis Agent
  [ ] Implement Planner Agent
  [ ] Add inter-agent messaging
  
Week 3:
  [ ] Integration tests
  [ ] Documentation
  [ ] Deployment scripts
```

#### Phase 2: Specialized Agents (3-4 weeks)
```
Week 1-2:
  [ ] Code Assistant Agent
  [ ] Data Analyst Agent
  [ ] Creative Writer Agent
  
Week 3:
  [ ] Agent routing logic
  [ ] Context propagation
  [ ] Error handling
```

#### Phase 3: Advanced Features (2-3 weeks)
```
Week 1:
  [ ] Human-in-the-loop approval
  [ ] Agent performance monitoring
  [ ] Cost tracking
  
Week 2-3:
  [ ] Auto-scaling based on load
  [ ] Agent hot-swap capability
  [ ] A/B testing for routing
```

---

## 🗺️ PHƯƠNG ÁN 2: KNOWLEDGE GRAPH INTEGRATION

### 2.1 Kiến trúc Knowledge Graph

```
┌─────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE GRAPH v4                        │
├─────────────────────────────────────────────────────────────┤
│  Persistent Storage                                         │
│  ├─ Neo4j (production)                                      │
│  └─ NetworkX + SQLite (lightweight)                         │
├─────────────────────────────────────────────────────────────┤
│  Graph Construction                                          │
│  ├─ Entity Extraction                                       │
│  ├─ Relation Extraction                                      │
│  ├─ Knowledge Graph Embeddings                              │
│  └─ Graph Neural Networks                                   │
├─────────────────────────────────────────────────────────────┤
│  Query Processing                                            │
│  ├─ Subgraph Retrieval                                      │
│  ├─ Graph Traversal (BFS/DFS)                               │
│  └─ Property Graph Queries                                  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Schema thiết kế

```cypher
// Node types
(NODE:Room {name: "Phòng 5", type: "show", topic: "tĩnh điện"})
(NODE:Exhibit {name: "Điện trường tĩnh", location: "Phòng 5"})
(NODE:Activity {name: "Thí nghiệm Leyden Jar", duration: 30})
(NODE:Schedule {event: "Show thứ 6", date: "2026-08-08"})

// Relationships
(Room)-[:HAS_EXHIBIT]->(Exhibit)
(Exhibit)-[:INCLUDES_ACTIVITY]->(Activity)
(Activity)-[:PART_OF_SCHEDULE]->(Schedule)
(Room)-[:LOCATED_IN->{room_number: "5"}]->(Building)
```

### 2.3 Neo4j Integration

#### Setup Neo4j (docker)
```yaml
# docker-compose.yml
version: '3.8'
services:
  neo4j:
    image: neo4j:5.20
    ports:
      - "7474:7474"  # Browser
      - "7687:7687"  # Bolt
    environment:
      - NEO4J_AUTH=neo4j/admin123
      - NEO4J_PLUGINS=[["apoc"]]
    volumes:
      - neo4j_data:/data
    networks:
      - rag-net

volumes:
  neo4j_data:

networks:
  rag-net:
```

#### Neo4j Service (Python)
```python
# src/kg/neo4j_client.py
from neo4j import GraphDatabase
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

class Neo4JGraphDB:
    """Neo4j client wrapper with connection pooling."""
    
    def __init__(self, uri="bolt://localhost:7687", 
                 user="neo4j", password="admin123"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
    def close(self):
        self.driver.close()
    
    def create_node(self, label: str, properties: Dict) -> bool:
        with self.driver.session() as session:
            result = session.run(
                f"CREATE (n:`{label}` {self._format_props(properties)}) RETURN n",
            )
            return result.single() is not None
    
    def get_subgraph(self, start_node_id: str, depth: int = 2) -> List:
        with self.driver.session() as session:
            query = f"""
                MATCH (n)-[:*0..{depth}]->(m)
                RETURN n, m
            """
            return session.run(query)
```

### 2.4 Knowledge Graph Construction Pipeline

```python
# src/kg/graph_builder.py
from typing import List
import logging

logger = logging.getLogger(__name__)

class KnowledgeGraphBuilder:
    """Build KG from documents and existing data."""
    
    def __init__(self, neo4j_client: Neo4JGraphDB):
        self.neo4j = neo4j_client
    
    async def build_from_documents(self, document_ids: List[str]):
        """Extract entities, relations, and build graph."""
        
        # 1. Chunk analysis (existing)
        chunks = await self._get_chunks(document_ids)
        
        # 2. Entity extraction
        entities = await self._extract_entities(chunks)
        
        # 3. Relation extraction
        relations = await self._extract_relations(entities, chunks)
        
        # 4. Graph construction
        await self._construct_graph(entities, relations)
        
        # 5. Graph embeddings (optional, for GNN)
        await self._compute_graph_embeddings()
```

### 2.5 Query Enhancement với KG

```python
# src/kg/graph_query.py
class GraphEnhancedRAG:
    """Combine vector search with graph traversal."""
    
    def __init__(self, chroma_store: ChromaStore, neo4j_client: Neo4JGraphDB):
        self.chroma = chroma_store
        self.neo4j = neo4j_client
    
    async def hybrid_query(self, query: str) -> Tuple[str, List]:
        """1. Vector search → 2. Graph traversal → 3. Synthesize."""
        
        # Step 1: Vector retrieval
        vector_results = await self.chroma.search(query, top_k=10)
        
        # Step 2: Extract entities from chunks
        entities = await self._extract_entities_from_chunks(vector_results)
        
        # Step 3: Graph traversal to find related content
        graph_results = await self.neo4j.get_related_content(entities)
        
        # Step 4: Rerank with graph scores
        combined_results = self._merge_and_rerank(vector_results, graph_results)
        
        # Step 5: Generate answer
        answer = await self.llm.generate_answer(combined_results)
        
        return answer, combined_results
```

### 2.6 Implementation Plan KG

```
Week 1-2: Lightweight KG (NetworkX)
  [ ] Design graph schema
  [ ] Implement entity extraction
  [ ] Build relation extractor
  [ ] Create NetworkX-based builder
  
Week 3-4: Neo4j Integration
  [ ] Setup Neo4j Docker
  [ ] Create Neo4JGraphDB client
  [ ] Implement graph queries
  [ ] Add graph traversal utilities

Week 5: Hybrid RAG
  [ ] Combine vector + graph search
  [ ] Graph-enhanced reranking
  [ ] Query synthesis logic

Week 6-7: Advanced Features
  [ ] Knowledge graph embeddings (Node2Vec)
  [ ] GNN-based query understanding
  [ ] Graph visualization UI
```

---

## 🎥 PHƯƠNG ÁN 3: MULTIMODAL ENHANCEMENT

### 3.1 Video Support

#### Upload và phân tích video
```python
# src/multimodal/video_handler.py
from typing import Optional, List
import tempfile
import logging

logger = logging.getLogger(__name__)

class VideoHandler:
    """Handle video upload and processing."""
    
    def __init__(self):
        self.transcriber = WhisperTranscriber()  # For video transcription
        self.summarizer = LLMSummarizer()
    
    async def process_video(self, video_path: str, 
                           max_duration: int = 3600) -> dict:
        """
        Process video file.
        
        Returns: {
            'transcript': List[{'timestamp', 'text'}],
            'summary': str,
            'entities': List[str],
            'chapters': List[{'title', 'start', 'end'}],
            'video_hash': str
        }
        """
        
        # 1. Extract audio from video
        audio_path = await self._extract_audio(video_path)
        
        # 2. Transcribe with Whisper
        transcript = await self.transcriber.transcribe(audio_path)
        
        # 3. Generate summary and chapters
        summary, chapters = await self.summarizer.summarize(transcript)
        
        # 4. Extract entities (people, places, concepts)
        entities = await self._extract_entities(transcript)
        
        # 5. Chunk transcript for RAG
        chunks = await self._chunk_transcript(transcript, max_duration)
        
        return {
            'transcript': transcript,
            'summary': summary,
            'entities': entities,
            'chapters': chapters,
            'video_hash': hashlib.md5(open(video_path).read()).hexdigest()
        }
```

### 3.2 Audio Support

```python
# src/multimodal/audio_handler.py
class AudioHandler:
    """Handle audio file processing."""
    
    def __init__(self):
        self.transcriber = WhisperTranscriber()
    
    async def transcribe_audio(self, audio_path: str) -> dict:
        """Transcribe audio file to text and embed."""
        
        # Transcribe with Whisper (or vad for speaker diarization)
        transcript = await self.transcriber.transcribe(audio_path)
        
        # Chunk and embed
        chunks = await self._chunk_and_embed(transcript)
        
        return {
            'transcript': transcript,
            'chunks': chunks,
            'audio_hash': hashlib.md5(open(audio_path).read()).hexdigest()
        }
```

### 3.3 Image Enhancement (Advanced)

#### Visual Question Answering
```python
# src/multimodal/vqa.py
class VQAModule:
    """Visual Question Answering with image-text RAG."""
    
    def __init__(self, llm_model: str, embedding_model: str):
        self.llm = HybridLLMClient(model=llm_model)
        self.embedder = EmbeddingClient(model=embedding_model)
    
    async def answer_from_image(self, image_path: str, 
                                question: str) -> str:
        """
        Answer question based on analyzing the image content.
        
        Steps:
        1. Extract text from image (OCR/Tesseract)
        2. Visual features (SIFT/CLIP embeddings)
        3. Retrieve relevant knowledge chunks
        4. Generate answer combining visual + textual context
        """
        
        # Step 1: OCR extraction
        ocr_text = self._extract_ocr(image_path)
        
        # Step 2: Visual embedding (optional, using CLIP)
        image_embedding = await self._get_clip_embedding(image_path)
        
        # Step 3: RAG with multimodal context
        retrieved_chunks = await self.chroma.search_multimodal(
            question, 
            image_embedding,
            top_k=5
        )
        
        # Step 4: Generate answer
        context = f"Visual content:\n{ocr_text}\n\nRetrieved knowledge:\n" + \
                   "\n\n".join([c['content'] for c in retrieved_chunks])
        answer = await self.llm.generate(question, context)
        
        return answer
```

### 3.4 Implementation Plan Multimodal

```
Week 1-2: Audio/Video Processing
  [ ] Integrate Whisper API or local model
  [ ] Implement video transcription pipeline
  [ ] Add audio speaker diarization (optional)
  
Week 3: Video Chapters & Summarization
  [ ] Automatic chapter detection
  [ ] Highlight clip generation
  [ ] Summary extraction
  
Week 4-5: Visual Q&A Enhancement
  [ ] OCR integration (Tesseract/PaddleOCR)
  [ ] CLIP embedding for images
  [ ] Multimodal retrieval logic

Week 6: Storage & Retrieval
  [ ] Add video/audio to ChromaDB schemas
  [ ] Implement timestamp-based retrieval
  [ ] Add video player UI component
```

---

## 🛡️ PHƯƠNG ÁN 4: PRODUCTION HARDENING

### 4.1 Monitoring & Observability

#### OpenTelemetry Integration
```python
# src/monitoring/opentelemetry.py
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider

class TelemetrySetup:
    """Initialize OpenTelemetry for distributed tracing."""
    
    def __init__(self):
        self.tracer_provider = TracerProvider()
        self.meter_provider = MeterProvider()
        
        # Export to Jaeger/Tempo
        jaeger_exporter = get_jaeger_exporter()
        self.tracer_provider.add_span_processor(
            BatchSpanProcessor(jaeger_exporter)
        )
    
    def instrument_route(self, name: str):
        """Create traced endpoint."""
        tracer = self.tracer_provider.get_tracer("ai-chatbox")
        
        @tracer.start_as_current_span(name)
        def wrapper(func):
            async def inner(*args, **kwargs):
                return await func(*args, **kwargs)
            return inner
        
        return wrapper
    
    def record_metric(self, name: str, value: float, tags: dict = None):
        meter = self.meter_provider.get_meter("ai-chatbox")
        metric = meter.create_observable_gauge(
            name=name, unit="1", description=description
        )
```

#### Custom Metrics
```python
# src/monitoring/metrics.py
from prometheus_client import Counter, Gauge, Histogram

class RAGMetrics:
    """Custom metrics for RAG system."""
    
    queries_total = Counter(
        'rag_queries_total', 'Total RAG queries',
        ['intent', 'status', 'model']
    )
    
    retrieval_latency = Histogram(
        'rag_retrieval_latency_seconds', 
        'Time spent on retrieval',
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
    )
    
    embedding_latency = Histogram(
        'rag_embedding_latency_seconds',
        'Embedding generation time'
    )
    
    active_connections = Gauge(
        'rag_active_connections', 
        'Current number of active connections'
    )
```

### 4.2 Alerting System

```python
# src/monitoring/alerts.py
from prometheus_client import CollectorRegistry, generate_latest
import requests

class AlertManager:
    """Monitor system health and send alerts."""
    
    def __init__(self, webhook_url: str, api_token: str):
        self.webhook_url = webhook_alert_url
        self.token = api_token
    
    async def check_health(self) -> dict:
        """Check system health metrics."""
        
        checks = {
            'lm_studio': await self._check_lm_studio(),
            'chroma_db': await self._check_chroma_status(),
            'embedding_model': await self._check_embedding_available(),
            'cpu_usage': await self._get_cpu_usage(),
            'memory_usage': await self._get_memory_usage(),
        }
        
        # Determine overall health
        healthy = all(check.get('status') == 'healthy' for check in checks.values())
        
        return {
            'overall_health': 'healthy' if healthy else 'unhealthy',
            'checks': checks,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _check_lm_studio(self) -> dict:
        try:
            r = requests.get(
                "http://localhost:1234/v1/models",
                timeout=5
            )
            return {
                'status': 'healthy' if r.status_code == 200 else 'unhealthy',
                'details': r.json()
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
```

### 4.3 Auto-scaling & Load Balancing

#### Horizontal Pod Autoscaling (Kubernetes)
```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-chatbox-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-chatbox-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

#### Queue-based Load Management
```python
# src/monitoring/queue_manager.py
from asyncio import Queue
from typing import Callable

class RateLimiter:
    """Token bucket rate limiter for API calls."""
    
    def __init__(self, rate: float = 1.0, capacity: int = 10):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
    
    async def acquire(self):
        """Acquire a token, waiting if necessary."""
        while True:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens += elapsed * self.rate
            
            if self.tokens >= 1:
                self.tokens -= 1
                self.last_update = now
                return True
            
            # Wait for next token
            wait_time = (1 - self.tokens) / self.rate
            await asyncio.sleep(min(wait_time, 5))
```

### 4.4 Database Backups & Failover

```python
# src/monitoring/database_backup.py
import sqlite3
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseBackup:
    """Automated ChromaDB backups."""
    
    def __init__(self, db_path: str, backup_dir: str):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_backup(self, retention_days: int = 30) -> dict:
        """Create point-in-time backup."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"chroma_{timestamp}.db"
        
        # ChromaDB uses LMDB, so copy directory
        import shutil
        lmdb_path = self.db_path.parent
        
        shutil.copytree(
            lmdb_path, 
            backup_file.parent / f"lmdb_{timestamp}",
            ignore=shutil.ignore_patterns("__pycache__")
        )
        
        # Delete old backups
        self._cleanup_old_backups(retention_days)
        
        return {
            'status': 'success',
            'backup_path': str(backup_file),
            'timestamp': timestamp
        }
```

### 4.5 Implementation Plan Production Hardening

```
Week 1-2: Monitoring Setup
  [ ] Integrate OpenTelemetry
  [ ] Add custom metrics collection
  [ ] Setup Prometheus + Grafana
  
Week 3: Alerting System
  [ ] Health check endpoints
  [ ] Alert webhooks (Discord/Slack)
  [ ] Error tracking (Sentry)

Week 4: Scaling & Reliability
  [ ] Rate limiting implementation
  [ ] Database backup automation
  [ ] Circuit breaker patterns
  
Week 5-6: Production Deployment
  [ ] Kubernetes manifests
  [ ] CI/CD pipeline update
  [ ] Load testing scripts
```

---

## 📊 PHƯƠNG ÁN 5: ADVANCED RAG V2

### 5.1 Multi-hop Reasoning

```python
# src/search/multi_hop_reasoner.py
from typing import List, Dict

class MultiHopReasoner:
    """Enable multi-step reasoning through queries."""
    
    async def decompose_and_answer(self, query: str) -> str:
        """
        Break down complex query into sub-queries.
        
        Example: "What products did Company X launch in 2024?"
          → Sub-query 1: Who is Company X?
             → Sub-query 2: What did Company X launch?
             → Sub-query 3: Filter for 2024
        """
        
        # Step 1: Analyze query complexity
        intent = await self._analyze_intent(query)
        
        if not await self._needs_decomposition(intent):
            return await self._answer_directly(query)
        
        # Step 2: Decompose into sub-queries
        sub_queries = await self._decompose_query(query)
        
        # Step 3: Sequential retrieval
        contexts = []
        for i, sq in enumerate(sub_queries):
            context = await self.chroma.search(sq, top_k=5)
            contexts.append(context)
            
            # Optionally update query based on results
            if i < len(sub_queries) - 1:
                next_query = await self._refine_query(
                    sq, 
                    context[-1],
                    sub_queries[i + 1]
                )
        
        # Step 4: Synthesize final answer
        answer = await self.llm.synthesize(
            query=query,
            contexts=contexts,
            reasoning_steps=sub_queries
        )
        
        return answer
```

### 5.2 Query Planning Agent

```python
# src/search/query_planner.py
class QueryPlanner:
    """Plan multi-step retrieval strategies."""
    
    def __init__(self):
        self.strategies = [
            'direct_search',      # Single query → retrieve → answer
            'query_expansion',    # Synonyms + related queries
            'multi_hop',          # Decompose into sub-queries
            'hybrid_fusion',      # Vector + keyword + graph
            'iterative_refinement',  # Rerank and refine iteratively
        ]
    
    def select_strategy(self, query: str, intent: str) -> str:
        """Select optimal retrieval strategy."""
        
        # Simple queries → direct search
        if self._is_simple_query(query):
            return 'direct_search'
        
        # Entity mention → hybrid fusion
        entities = self._extract_entities(query)
        if entities:
            return 'hybrid_fusion'
        
        # Temporal query → multi-hop
        if self._has_temporal_terms(query):
            return 'multi_hop'
        
        # Ambiguous → iterative refinement
        confidence = self._estimate_confidence(query)
        if confidence < 0.6:
            return 'iterative_refinement'
        
        return 'query_expansion'
```

### 5.3 Advanced Retrieval Strategies

#### Reciprocal Rank Fusion + Cross-Encoder Rerank
```python
# src/search/advanced_rag.py
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

class AdvancedRAG:
    """Advanced retrieval with multiple strategies."""
    
    def __init__(self, 
                 chroma_store: ChromaStore,
                 bm25_retriever: BM25Retriever,
                 reranker: CrossEncoderReranker):
        self.chroma = chroma_store
        self.bm25 = bm25_retriever
        self.reranker = reranker
    
    async def advanced_search(self, query: str) -> List[dict]:
        """Retrieve using multiple strategies and fuse results."""
        
        # Strategy 1: Dense retrieval (vector search)
        vector_results = await self.chroma.search(query, top_k=50)
        
        # Strategy 2: Sparse retrieval (BM25)
        bm25_results = await self.bm25.search(query, top_k=50)
        
        # Strategy 3: Graph retrieval (if KG available)
        graph_results = None
        if await self.neo4j.is_available():
            entities = await self._extract_entities(query)
            graph_results = await self.neo4j.get_related(entities)
        
        # Reciprocal Rank Fusion (RRF)
        rrf_results = await self._apply_rrf(
            [vector_results, bm25_results], 
            k=60
        )
        
        if graph_results:
            rrf_results += graph_results
        
        # Cross-encoder rerank top candidates
        reranked = await self.reranker.rerank(query, rrf_results[:100])
        
        return reranked
    
    async def _apply_rrf(self, results_list: List[List[dict]], k: int = 60):
        """Apply Reciprocal Rank Fusion."""
        all_ids = set()
        for result in results_list:
            all_ids.update(doc['id'] for doc in result)
        
        rrf_scores = {doc_id: 0.0 for doc_id in all_ids}
        
        for rank, result in enumerate(results_list, start=1):
            for doc in result:
                rrf_scores[doc['id']] += 1 / (rank + k)
        
        return sorted(
            [self._find_doc_by_id(doc_id) for doc_id in rrf_scores],
            key=lambda x: rrf_scores[x['id']], 
            reverse=True
        )[:k]
```

### 5.4 Context Compression V2

```python
# src/search/context_compressor_v2.py
from typing import List, Optional

class AdaptiveContextCompressor:
    """Adaptive context compression based on query type."""
    
    def __init__(self):
        self.summarizer = LLMSummarizer()
        self.fact_checker = FaithfulnessChecker()
    
    async def compress_context(self, contexts: List[dict], 
                              query: str) -> Tuple[str, dict]:
        """
        Compress context while preserving faithfulness.
        
        Returns: (compressed_context, metadata)
        """
        
        # Step 1: Filter low-relevance chunks
        scored = await self._score_by_relevance(contexts, query)
        scored = [c for c in scored if c['score'] > 0.3]
        
        # Step 2: Group by topic
        grouped = await self._group_by_topic(scored)
        
        # Step 3: Summarize each group
        summaries = []
        for topic, chunks in grouped.items():
            summary = await self.summarizer.summarize(chunks)
            
            # Faithfulness check
            faithfulness = await self.fact_checker.check(
                query=query,
                summary=summary
            )
            
            if faithfulness >= 0.7:
                summaries.append(summary)
        
        # Step 4: Final synthesis
        compressed = "\n\n".join(summaries)
        
        metadata = {
            'original_chunk_count': len(contexts),
            'compressed_chunk_count': len(summaries),
            'compression_ratio': len(compressed) / sum(len(c['content']) for c in contexts),
            'faithfulness_score': await self.fact_checker.compute_overall(query, summaries)
        }
        
        return compressed, metadata
```

### 5.5 Implementation Plan Advanced RAG v2

```
Week 1-2: Query Decomposition
  [ ] Implement MultiHopReasoner
  [ ] Add query planner logic
  [ ] Create sub-query generation prompts
  
Week 3-4: Advanced Retrieval
  [ ] Implement RRF fusion
  [ ] Cross-encoder reranking
  [ ] Graph-enhanced retrieval

Week 5-6: Context Compression V2
  [ ] Topic-based grouping
  [ ] Faithfulness-aware summarization
  [ ] Adaptive compression logic

Week 7: Evaluation & Optimization
  [ ] Add multi-hop test cases
  [ ] Benchmark retrieval quality
  [ ] Optimize latency vs accuracy trade-off
```

---

## 📈 ROADMAP TỔNG THỂ

### Phase 1: Foundation (1-2 tháng)
| Task | Priority | Thời gian |
|------|----------|-----------|
| Query Analysis Agent | High | Week 1-2 |
| Knowledge Graph (NetworkX) | Medium | Week 3-4 |
| Monitoring Setup | High | Week 2-3 |
| Database Backups | High | Week 3 |

### Phase 2: Advanced Agents (2-3 tháng)
| Task | Priority | Thời gian |
|------|----------|-----------|
| Code Assistant Agent | High | Week 5-8 |
| Data Analyst Agent | Medium | Week 9-10 |
| Research Agent Enhancement | High | Week 11-12 |

### Phase 3: Multimodal (2-3 tháng)
| Task | Priority | Thời gian |
|------|----------|-----------|
| Audio Transcription | Medium | Week 13-15 |
| Video Processing | Low | Week 16-18 |
| Visual Q&A | Low | Week 19-20 |

### Phase 4: Advanced RAG v2 (2 tháng)
| Task | Priority | Thời gian |
|------|----------|-----------|
| Multi-hop Reasoning | High | Week 21-23 |
| Query Planning | High | Week 24 |
| Context Compression V2 | Medium | Week 25-26 |

### Phase 5: Production Hardening (Ongoing)
| Task | Priority | Thời gian |
|------|----------|-----------|
| Kubernetes Deployment | High | Month 4 |
| CI/CD Pipeline | High | Month 3-4 |
| Load Testing | Medium | Month 5 |

---

## 💰 ESTIMATED RESOURCES

### Development Effort
| Category | Hours | Team Members |
|----------|-------|--------------|
| Agent System | 160h | 2 Backend Devs |
| Knowledge Graph | 80h | 1 Backend + 1 Data Eng |
| Multimodal | 120h | 1 ML Engineer |
| Production Hardening | 100h | 1 DevOps Engineer |
| Testing & Docs | 80h | 1 QA Engineer |

**Tổng:** ~540 hours (≈ 2.7 người trong 3 tháng)

### Infrastructure Cost (monthly)
| Service | Estimated Cost |
|---------|----------------|
| Neo4j Docker | $0 (self-hosted) |
| Neo4j Enterprise Cloud | ~$100/month |
| Whisper API (optional) | ~$50/month |
| Monitoring Tools | ~$20/month |

---

## ✅ SUCCESS CRITERIA

### Technical Metrics
- [ ] Multi-hop reasoning accuracy > 85%
- [ ] Query decomposition success rate > 90%
- [ ] Graph retrieval latency < 1s
- [ ] Context compression ratio ≥ 3:1 with faithfulness > 0.8
- [ ] System availability > 99.5%

### Business Metrics
- [ ] User satisfaction score > 4.5/5
- [ ] Average response time < 2s
- [ ] Cost per query reduced by 30% (via caching/compression)
- [ ] Support ticket volume reduced by 50%

---

## 🚀 NEXT STEPS

1. **Review và phê duyệt kế hoạch** — Discuss với stakeholder
2. **Setup development environment** — Clone repo, setup dependencies
3. **Implement Phase 1** — Foundation improvements
4. **Weekly standup meetings** — Track progress
5. **Quarterly review** — Adjust priorities

---

## 📝 Ghi chú

- Ưu tiên cải thiện trải nghiệm người dùng trước
- Không để advanced features ảnh hưởng core functionality
- Luôn đảm bảo backward compatibility
- Document tất cả thay đổi trong CHANGELOG.md
