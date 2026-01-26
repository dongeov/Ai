import streamlit as st
import os
import tempfile
import json
import uuid
import hashlib
import sys
import threading
import time
import shutil
from datetime import datetime
from io import BytesIO
from pathlib import Path
import requests
from PIL import Image
import streamlit.components.v1 as components

from huggingface_hub import InferenceClient
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader,
    UnstructuredPDFLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# Cấu hình Token mặc định (đã ẩn khỏi giao diện)
HF_TOKEN = "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"
DEFAULT_REPO_ID = "openai/gpt-oss-20b"

BASE_DIR = Path(os.getcwd())
LOCAL_DATA_PATH = BASE_DIR / "data"
CACHE_SYNC_PATH = BASE_DIR / "ai_cache_sync"
VECTOR_STORE_DIR = BASE_DIR / "vector_store_cache"

LOCAL_DATA_PATH.mkdir(exist_ok=True)
CACHE_SYNC_PATH.mkdir(exist_ok=True)

SUPPORTED_EXTENSIONS = [
    '.pdf', '.txt', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.md'
]

def configure_page():
    st.set_page_config(
        page_title="AI Internal Assistant Pro",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def apply_custom_css():
    css_content = """
    <style>
        :root {
            --primary-bg: #f8fafc;
            --accent-color: #3b82f6;
            --success-color: #10b981;
            --text-color: #1e293b;
        }
        .stChatMessage {
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        [data-testid="stChatMessageUser"] {
            background: #e0f2fe;
            border-left: 4px solid var(--accent-color);
        }
        [data-testid="stChatMessageAssistant"] {
            background: #dcfce7;
            border-left: 4px solid var(--success-color);
        }
        .deep-think-indicator {
            background: #fffbeb;
            border-left: 3px solid #f59e0b;
            padding: 10px;
            border-radius: 4px;
            font-size: 0.9em;
            margin-top: 8px;
            color: #92400e;
        }
        .stButton>button {
            border-radius: 8px;
            transition: all 0.2s;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
    </style>
    """
    st.markdown(css_content, unsafe_allow_html=True)

def enable_auto_scroll():
    """Inject JS để tự động cuộn xuống cuối trang khi có nội dung mới"""
    js = """
    <script>
        function scrollDown() {
            var main = window.parent.document.querySelector(".main");
            if (main) {
                main.scrollTop = main.scrollHeight;
            }
        }
        
        // Tạo observer để theo dõi thay đổi trong DOM
        var observer = new MutationObserver(function(mutations) {
            scrollDown();
        });
        
        var target = window.parent.document.querySelector(".main");
        if (target) {
            observer.observe(target, { childList: true, subtree: true, characterData: true });
        }
    </script>
    """
    components.html(js, height=0, width=0)

class EmbeddingManager:
    @staticmethod
    @st.cache_resource
    def load_embedding_model():
        model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        model_kwargs = {'device': 'cpu'}
        encode_kwargs = {'normalize_embeddings': True}
        
        embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )
        return embeddings

class DocumentProcessor:
    def __init__(self):
        self.embedding_model = EmbeddingManager.load_embedding_model()

    def get_loader(self, file_path: Path):
        ext = file_path.suffix.lower()
        if ext == '.pdf':
            return PyPDFLoader(str(file_path))
        elif ext in ['.txt', '.md']:
            return TextLoader(str(file_path), encoding='utf-8')
        elif ext in ['.doc', '.docx']:
            return UnstructuredWordDocumentLoader(str(file_path))
        elif ext in ['.ppt', '.pptx']:
            return UnstructuredPowerPointLoader(str(file_path))
        elif ext in ['.xls', '.xlsx']:
            return UnstructuredExcelLoader(str(file_path))
        return None

    def process_file(self, file_path: Path, filename: str):
        loader = self.get_loader(file_path)
        if not loader:
            return []

        try:
            docs = loader.load()
            valid_docs = []
            for doc in docs:
                if doc.page_content and len(doc.page_content.strip()) > 10:
                    doc.metadata['source'] = filename
                    valid_docs.append(doc)
            return valid_docs
        except Exception as e:
            st.error(f"Lỗi đọc file {filename}: {str(e)}")
            return []

    def create_vector_store(self, documents):
        if not documents:
            return None
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(documents)
        
        vector_store = FAISS.from_documents(splits, self.embedding_model)
        return vector_store

class CacheManager:
    def __init__(self):
        self.vector_dir = VECTOR_STORE_DIR
        self.vector_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.vector_dir / "metadata.json"

    def get_current_file_hash(self):
        file_hashes = {}
        if not LOCAL_DATA_PATH.exists():
            return {}
            
        for f in LOCAL_DATA_PATH.glob('*'):
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
                stat = f.stat()
                file_hashes[f.name] = f"{stat.st_size}_{stat.st_mtime}"
        return file_hashes
    def get_saved_hashes(self):
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    def load_vector_store(self, embedding_model):
        if not (self.vector_dir / "index.faiss").exists():
            return None
        try:
            return FAISS.load_local(
                str(self.vector_dir), 
                embedding_model,
                allow_dangerous_deserialization=True
            )
        except Exception:
            return None

    def save_vector_store(self, vector_store, file_hashes):
        vector_store.save_local(str(self.vector_dir))
        with open(self.metadata_file, 'w') as f:
            json.dump(file_hashes, f)

    def is_cache_valid(self, current_hashes):
        if not self.metadata_file.exists():
            return False
        try:
            with open(self.metadata_file, 'r') as f:
                cached_hashes = json.load(f)
            return cached_hashes == current_hashes
        except:
            return False

class AIInternalAssistant:
    def __init__(self):
        configure_page()
        apply_custom_css()
        enable_auto_scroll() # Kích hoạt tự động cuộn
        
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "vector_store" not in st.session_state:
            st.session_state.vector_store = None
        if "deep_think_mode" not in st.session_state:
            st.session_state.deep_think_mode = False
        if "hf_token" not in st.session_state:
            st.session_state.hf_token = HF_TOKEN
        if "conversations" not in st.session_state:
            st.session_state.conversations = {}

        self.processor = DocumentProcessor()
        self.cache_manager = CacheManager()

    def sidebar_ui(self):
        with st.sidebar:
            # Đã ẩn phần Cấu hình & Token Input
            
            st.subheader("📚 Cơ sở tri thức (RAG)")
            
            uploaded_files = st.file_uploader(
                "Thêm tài liệu vào KB", 
                type=['pdf', 'txt', 'docx', 'md'],
                accept_multiple_files=True
            )
            
            if uploaded_files:
                for uf in uploaded_files:
                    save_path = LOCAL_DATA_PATH / uf.name
                    with open(save_path, "wb") as f:
                        f.write(uf.getbuffer())
                st.success(f"Đã thêm {len(uploaded_files)} file vào {LOCAL_DATA_PATH.name}")
                st.rerun()

            if st.button("🔄 Cập nhật / Index lại dữ liệu", use_container_width=True):
                self.reindex_data()

            if st.session_state.vector_store:
                st.success("✅ Database đã sẵn sàng")
            else:
                st.warning("⚠️ Chưa có Database")

            st.divider()
            
            st.session_state.deep_think_mode = st.toggle(
                "🧠 Chế độ Deep Think", 
                value=st.session_state.deep_think_mode
            )

            st.subheader("💬 Hội thoại")
            if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

    def reindex_data(self):
        """Xử lý thông minh: Chỉ index lại phần thay đổi"""
        # 1. Lấy trạng thái file hiện tại
        current_hashes = self.cache_manager.get_current_file_hash()
        saved_hashes = self.cache_manager.get_saved_hashes()
        
        # 2. Phân loại thay đổi
        current_keys = set(current_hashes.keys())
        saved_keys = set(saved_hashes.keys())
        
        new_files = current_keys - saved_keys
        deleted_files = saved_keys - current_keys
        modified_files = {f for f in current_keys & saved_keys if current_hashes[f] != saved_hashes[f]}
        
        # 3. Xử lý logic
        if not new_files and not deleted_files and not modified_files and st.session_state.vector_store is not None:
            st.info("✅ Dữ liệu đã được cập nhật. Không có thay đổi nào.")
            return

        # Trường hợp CHỈ CÓ FILE MỚI và đã có Database -> Chạy Incremental (Nhanh)
        if new_files and not deleted_files and not modified_files and st.session_state.vector_store is not None:
            with st.spinner(f"🚀 Đang cập nhật thêm {len(new_files)} tài liệu mới..."):
                new_docs = []
                progress_bar = st.progress(0)
                
                for i, filename in enumerate(new_files):
                    file_path = LOCAL_DATA_PATH / filename
                    docs = self.processor.process_file(file_path, filename)
                    new_docs.extend(docs)
                    progress_bar.progress((i + 1) / len(new_files))
                
                if new_docs:
                    # Chia nhỏ và thêm vào Vector Store hiện có
                    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                    splits = text_splitter.split_documents(new_docs)
                    
                    st.session_state.vector_store.add_documents(splits)
                    
                    # Lưu lại trạng thái mới
                    self.cache_manager.save_vector_store(st.session_state.vector_store, current_hashes)
                    st.success(f"✅ Đã thêm {len(new_docs)} tài liệu mới vào chỉ mục.")
                else:
                    st.warning("Không đọc được nội dung từ các file mới.")
                    # Vẫn cập nhật hash để lần sau không báo lại
                    self.cache_manager.save_vector_store(st.session_state.vector_store, current_hashes)
            return

        # Trường hợp CÓ FILE XÓA/SỬA hoặc CHƯA CÓ DATABASE -> Chạy Full Rebuild (An toàn)
        msg = "🔄 Đang khởi tạo cơ sở dữ liệu..."
        if deleted_files or modified_files:
            msg = f"🔄 Phát hiện thay đổi ({len(modified_files)} sửa, {len(deleted_files)} xóa). Đang tái cấu trúc chỉ mục..."
            
        with st.spinner(msg):
            all_docs = []
            files = list(LOCAL_DATA_PATH.glob('*'))
            
            if not files:
                st.error("Thư mục data trống! Hãy upload file.")
                return

            progress_bar = st.progress(0)
            for i, file_path in enumerate(files):
                if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    docs = self.processor.process_file(file_path, file_path.name)
                    all_docs.extend(docs)
                progress_bar.progress((i + 1) / len(files))
            
            if all_docs:
                vector_store = self.processor.create_vector_store(all_docs)
                st.session_state.vector_store = vector_store
                self.cache_manager.save_vector_store(vector_store, current_hashes)
                st.success(f"✅ Đã index {len(all_docs)} đoạn văn bản!")
            else:
                st.warning("Không trích xuất được nội dung nào từ các file.")

    def initialize_data(self):
        if st.session_state.vector_store is None:
            current_hashes = self.cache_manager.get_current_file_hash()
            if self.cache_manager.is_cache_valid(current_hashes):
                st.session_state.vector_store = self.cache_manager.load_vector_store(
                    self.processor.embedding_model
                )

    def generate_response(self, prompt):
        if not st.session_state.hf_token:
            st.error("Vui lòng nhập HuggingFace Token trong Sidebar!")
            return

        client = InferenceClient(token=st.session_state.hf_token)
        
        context = ""
        sources = []
        if st.session_state.vector_store:
            # Lấy nhiều ứng viên hơn (k=10) để lọc trùng lặp
            docs = st.session_state.vector_store.similarity_search(prompt, k=10)
            
            unique_docs = []
            seen_content = set()
            
            for doc in docs:
                # Chuẩn hóa nội dung (xóa khoảng trắng thừa) để so sánh
                clean_content = " ".join(doc.page_content.split())
                
                if clean_content not in seen_content:
                    seen_content.add(clean_content)
                    unique_docs.append(doc)
            
            # Chỉ lấy top 4 kết quả độc nhất
            selected_docs = unique_docs[:4]
            
            context = "\n\n".join([d.page_content for d in selected_docs])
            sources = list(set([d.metadata.get('source', 'unknown') for d in selected_docs]))

        role_desc = "Bạn là trợ lý AI nội bộ thông minh, hữu ích và chuyên nghiệp."
        if st.session_state.deep_think_mode:
            role_desc += " Hãy suy nghĩ sâu sắc (Deep Think), phân tích từng bước, logic và chi tiết."
        
        system_prompt = f"""{role_desc}
        
        NHIỆM VỤ CỤ THỂ:
        1. Phân tích kỹ lưỡng thông tin ngữ cảnh (CONTEXT) bên dưới để trả lời câu hỏi, ưu tiên trả lời các thông tin liên quan tới trung tâm khám phá khoa học và đổi mới sáng tạo.
        2. Nếu thông tin KHÔNG có trong Context, hãy dùng kiến thức của bạn để hỗ trợ nhưng PHẢI NÊU RÕ là thông tin này không nằm trong tài liệu.
        3. Trình bày câu trả lời một cách mạch lạc, chuyên nghiệp, sử dụng Markdown (in đậm, gạch đầu dòng dùng kí tự "*") để làm rõ ý.
        4. LUÔN trả lời bằng TIẾNG VIỆT.
        5. Cuối câu trả lời, LUÔN đề xuất 3 câu hỏi gợi ý liên quan để mở rộng vấn đề đang thảo luận.
        6. KHÔNG sử dụng thẻ HTML như <br>, hãy sử dụng xuống dòng tự nhiên. Sử dụng Markdown chuẩn cho văn bản và LaTeX (trong dấu $$ hoặc $) cho công thức toán học.
        7. Đối với công thức toán học, BẮT BUỘC luôn dùng LaTeX đặt trong dấu $$ (ví dụ: $$ \\boxed{{DoP = ...}} $$) để hiển thị đẹp và đóng khung kết quả quan trọng.
        8. Luôn dùng kiến thức của bản để kiểm chứng các thông tin khoa học, công thức và các kết quả có định lượng khác
        9. suy nghĩ kĩ trước khi đưa ra câu trả lời cuối cùng
        CONTEXT:
        {context}
        """

        try:
            stream = client.chat.completions.create(
                model=DEFAULT_REPO_ID,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=20480,
                temperature=0.7 if st.session_state.deep_think_mode else 0.3,
                stream=True
            )

            response_text = ""
            placeholder = st.empty()
            
            for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                response_text += content
                
                # Xử lý làm sạch thẻ <br> thành xuống dòng \n
                clean_text = response_text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
                
                placeholder.markdown(clean_text + "▌")
            
            # Hiển thị lần cuối bản sạch
            clean_text = response_text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
            placeholder.markdown(clean_text)
            
            if sources:
                with st.expander("📚 Nguồn tham khảo"):
                    for s in sources:
                        st.write(f"- {s}")
            
            # Lưu bản sạch vào lịch sử chat
            st.session_state.messages.append({
                "role": "assistant", 
                "content": clean_text,
                "sources": sources
            })

        except Exception as e:
            st.error(f"Lỗi API: {str(e)}")

    def run(self):
        self.initialize_data()
        self.sidebar_ui()

        st.title("🚀 trợ lý TTKP&DMST")
        st.caption(f"Model: {DEFAULT_REPO_ID} | Mode: {'Deep Think' if st.session_state.deep_think_mode else 'Standard'}")

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("sources"):
                    with st.expander("📚 Nguồn"):
                        for s in msg["sources"]:
                            st.write(f"- {s}")

        if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                if st.session_state.deep_think_mode:
                    st.markdown('<div class="deep-think-indicator">🧠 Đang suy luận sâu...</div>', unsafe_allow_html=True)
                self.generate_response(prompt)

if __name__ == "__main__":
    app = AIInternalAssistant()
    app.run()
