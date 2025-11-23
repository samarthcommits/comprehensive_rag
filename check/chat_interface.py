import streamlit as st
import time
import json
import os
from io import BytesIO
from langchain_ollama import ChatOllama
import pdfplumber
import pymupdf as fitz
from PIL import Image
import io
from langchain_google_genai import ChatGoogleGenerativeAI
from pymilvus import MilvusClient
from utils.session_state import reset_retriever_state

def show():
    """Chat interface page"""
    
    if not st.session_state.setup_complete:
        st.warning("⚠️ Please set up a collection first in Document Management")
        # if st.button("Go to Document Management"):
        #     st.switch_page("pages/document_management.py")
        return
    
    st.title("💬 Chat with Your Documents")
    st.markdown("Ask questions and get intelligent answers from your documents")
    
    # Sidebar configuration
    show_sidebar_config()
    
    # Main chat interface
    show_chat_interface()

def show_sidebar_config():
    """Sidebar with configuration options"""
    
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        
        # Current collection info
        st.info(f"""
        **User:** {st.session_state.config.get('user_name', 'N/A')}  
        **Collection:** {st.session_state.collection or 'N/A'}
        """)
        
        st.markdown("---")
        
        # Load PDF for current collection
        load_collection_pdfs()
        
        st.markdown("---")
        
        # Collection switcher
        if st.checkbox("🔄 Switch Collection"):
            show_collection_switcher()
        
        st.markdown("---")

        check = st.checkbox('Refine results', help='Takes more time to fetch relevant documents, but gives better output', key='rerank')

        st.markdown("---")
        
        # Reset options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.session_state.context = []
                st.session_state.conte = []
                st.success("Chat cleared!")
                st.rerun()
        
        with col2:
            if st.button("🔄 Reset All", use_container_width=True):
                reset_retriever_state()
                st.success("Reset complete!")
                st.rerun()

def load_collection_pdfs():
    """Load PDFs for the current collection"""
    
    try:
        file_path = f"documents/{st.session_state.user_name}/{st.session_state.collection}"
        
        if not os.path.exists(file_path):
            return
        
        pdf_names = os.listdir(file_path)
        
        if not pdf_names:
            st.warning("No PDFs found in collection")
            return
        
        # Get primary PDF name from database
        pdf_name = ''
        for suffix in ['ann', 'sparse', 'dense', 'rerank']:
            try:
                info = st.session_state.db_handler.get_collection_info(
                    user_name=st.session_state.user_name,
                    collection_name=f"{st.session_state.collection}_{suffix}"
                )
                if info and info.get('pdf_name'):
                    pdf_name = info['pdf_name']
                    break
            except:
                continue
        
        # Load all PDFs
        pdf_dict = {}
        doc_dict = {}
        
        for pdf_file in pdf_names:
            file_p = os.path.join(file_path, pdf_file)
            with open(file_p, "rb") as f:
                file_bytes = f.read()
            
            fake_uploaded_file = BytesIO(file_bytes)
            
            with pdfplumber.open(fake_uploaded_file) as pdf:
                pdf_dict[pdf_file] = pdf
            
            doc_dict[pdf_file] = fitz.open(stream=file_bytes, filetype="pdf")
        
        # Store in session state
        st.session_state.pdf_dict = pdf_dict
        st.session_state.doc_dict = doc_dict
        
        # Set primary PDF if available
        if pdf_name and pdf_name in pdf_dict:
            st.session_state.pdf = pdf_dict[pdf_name]
            st.session_state.doc = doc_dict[pdf_name]
        
        st.success(f"📚 Loaded {len(pdf_names)} document(s)")
        
    except Exception as e:
        st.error(f"Error loading PDFs: {str(e)}")

def show_collection_switcher():
    """Allow switching between collections"""
    
    db1 = MilvusClient(
        db_name=st.session_state.config['user_name'],
        uri = os.environ['MILVUS_URL'],
        # password = os.environ['MILVUS_PASSWORD'],
        # user = 'milvus'
    )
    
    collections = db1.list_collections()
    
    selected_collection = st.selectbox(
        'Switch to Collection',
        options=collections,
        help="Select a different collection to chat with"
    )
    
    if selected_collection and st.button("Switch", use_container_width=True):
        try:
            collection_info = st.session_state.db_handler.get_collection_info(
                collection_name=selected_collection,
                user_name=st.session_state.config['user_name']
            )
            
            if collection_info:
                st.info(f"""
                **Retrieval:** {collection_info.get('retrieval_technique', 'N/A')}  
                **Chunking:** {collection_info.get('chunking_strategy', 'N/A')}
                """)
            
            st.session_state.collection = selected_collection
            st.success(f"Switched to: {selected_collection}")
            st.rerun()
            
        except Exception as e:
            st.error(f"Error switching collection: {str(e)}")

def show_chat_interface():
    """Main chat interface"""
    
    # Display chat history
    chat_container = st.container()
    
    with chat_container:
        for idx, message in enumerate(st.session_state.chat_history):
            with st.chat_message(message['role']):
                st.markdown(message['content'], unsafe_allow_html=True)
                
                # Show context for assistant messages
                if message['role'] == 'assistant' and 'conte' in message and message['conte']:
                    with st.expander(f"📄 View Source Context ({len(message['conte'])} pages)"):
                        for i, page_img in enumerate(message['conte'], start=1):
                            st.image(page_img, caption=f"Page {i}", use_container_width=True)
                            if i < len(message['conte']):
                                st.divider()
    
    # Chat input
    user_query = st.chat_input("💭 Ask a question about your documents...")
    
    if user_query:
        handle_user_query(user_query)

def handle_user_query(user_query, rerank = True):
    """Process user query and generate response"""
    
    # Add user message to history
    st.session_state.chat_history.append({
        'role': 'user',
        'content': user_query
    })
    
    with st.spinner("🤔 Thinking...", show_time=True):
        try:
            retriever = st.session_state.retriever_obj
            
            # Retrieve relevant documents
            start_time = time.perf_counter()
            check = False
            if 'rerank' in st.session_state:
                check = st.session_state['rerank']
            retrieved_docs = retriever.get_all_results(query = user_query, rerank = check)
            retrieval_time = time.perf_counter() - start_time
            
            if not retrieved_docs:
                st.warning("⚠️ No relevant documents found in the collection")
                return
            
            # Process and highlight PDF pages
            imgs = process_pdf_highlights(retrieved_docs)
            
            # Prepare context
            context = "\n\n".join([doc.page_content for doc in retrieved_docs])
            
            # Generate response using LLM
            llm = ChatOllama(model = 'gemma3:27b', base_url=os.environ['OLLAMA_API_ADDRESS'])
            # llm = ChatGoogleGenerativeAI(
            #     model="gemini-2.0-flash",
            #     temperature=0.3,
            #     api_key=os.getenv("GOOGLE_API_KEY", "")
            # )
            
            prompt = f"""Based on the following context, answer the user's question accurately and concisely.

Context:
{context}

Chat History:
{format_chat_history()}

Question: {user_query}

Answer:"""
            
            response = llm.invoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            
            # Add assistant response to history
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': answer,
                'context': [],
                'conte': imgs
            })
            
            # Show retrieval time
            st.toast(f"✅ Retrieved in {retrieval_time:.2f}s", icon="⚡")
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error generating response: {str(e)}")
            import traceback
            with st.expander("Error Details"):
                st.code(traceback.format_exc())

def process_pdf_highlights(retrieved_docs):
    """Highlight *all words* inside windows where multiple keywords co-occur."""

    imgs = []

    if not st.session_state.get("doc_dict"):
        return imgs

    try:

        page_pdf = {}
        for doc in retrieved_docs:
            try:
                pages = json.loads(str(doc.metadata.get("pages", "[]")))
                pdf_name = doc.metadata.get("pdf_name", "")
                if not pdf_name or pdf_name not in st.session_state.doc_dict:
                    continue

                page_pdf.setdefault(pdf_name, []).extend(pages)
                page_pdf[pdf_name] = list(set(page_pdf[pdf_name]))
            except Exception:
                continue

        all_keywordss = []
        for doc in retrieved_docs:
            all_keywords = set()
            words = doc.page_content.split()
            keywords = [w.strip(".,!?;:").lower() for w in words if len(w) > 2]
            keywords = words
            # all_keywords
            all_keywords.update(keywords[: len(keywords)])
            all_keywordss.append(all_keywords)

        WINDOW_SIZE = 200
        STEP = 12
        THRESHOLD_RATIO = 0.989
        print(THRESHOLD_RATIO, '------>thres')
        pal = [(1, 1, 0), (1, 1, 0), (1, 1, 0)]
        print('here-------------------look here', len(all_keywordss), len(retrieved_docs))
        print('pdf page - ', page_pdf)
        for pdf_name, page_nums in page_pdf.items():
            pdf_doc = st.session_state.doc_dict[pdf_name]
            print('pdf doc - ', pdf_doc)
            for page_num in page_nums:
                try:
                    page = pdf_doc[page_num - 1]
                    words_info = page.get_text("words")
                    words_info = sorted(words_info, key=lambda w: (w[1], w[0]))
                    words = [w[4].lower() for w in words_info]


                    ke = {}
                    # j = 0
                    for j, all_keywords in enumerate(all_keywordss):
                        i = 0
                        print('here---------- here', j)
                        while i < len(words):
                            # print('i', i)
                            wind = int(len(all_keywords)*1.2)
                            window = words_info[i:i + wind]
                            window_words = [w[4].lower() for w in window]
                            # window_words = [w.strip(".,!?;:").lower() for w in window_words if len(w) > 2]

                            keyword_count = len([w for w in window_words if w in all_keywords])

                            if keyword_count >= THRESHOLD_RATIO * len(all_keywords):
                                # flag = 0
                                ke[j] = THRESHOLD_RATIO * len(all_keywords)
                                for ijj, w in enumerate(window):
                                    # print('w - ', ijj)
                                    rect = fitz.Rect(w[0], w[1], w[2], w[3])
                                    highlight = page.add_highlight_annot(rect)
                                    # try:
                                    # print(pal[j], 'palj', j, pal)
                                    highlight.set_colors(stroke=pal[0])  
                                    # except:
                                    #     highlight.set_colors(stroke=(1, 0, 0))  
                                    highlight.update()

                                i += STEP

                            else:
                                i += STEP

                    # Render page
                    pix = page.get_pixmap(dpi=200)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    imgs.append(img)
                    print('appended')

                except Exception as e:
                    print('exception here - >', e)
                    continue

    except Exception as e:
        st.warning(f"Could not highlight PDFs: {str(e)}")

    return imgs

def process_pdf_highlights_v3(retrieved_docs):
    """Run multiple highlight passes — one per retrieved doc keyword list."""

    imgs = []

    if not st.session_state.get("doc_dict"):
        return imgs

    try:
        # -----------------------------
        # STEP 1 — Map PDFs to relevant pages
        # -----------------------------
        page_pdf = {}
        for doc in retrieved_docs:
            try:
                pages = json.loads(str(doc.metadata.get("pages", "[]")))
                pdf_name = doc.metadata.get("pdf_name", "")
                if not pdf_name or pdf_name not in st.session_state.doc_dict:
                    continue

                page_pdf.setdefault(pdf_name, []).extend(pages)
                page_pdf[pdf_name] = list(set(page_pdf[pdf_name]))
            except Exception:
                continue

        # ---------------------------------------------------------
        # STEP 2 — 🔥 Build SEPARATE keyword lists for each doc
        # ---------------------------------------------------------
        keyword_lists = []   # 🔥 each element = keyword list for one doc

        for doc in retrieved_docs:
            words = doc.page_content.split()
            keywords = [w.strip(".,!?;:").lower() for w in words]
            keyword_lists.append(keywords)    # 🔥 FULL keyword list for this doc

        # ---------------------------------------------------------
        # STEP 3 — 🔥 MULTIPLE highlight passes (one per keyword list)
        # ---------------------------------------------------------
        WINDOW_SIZE = 220
        STEP = 35
        THRESHOLD_RATIO = 0.35

        for pdf_name, page_nums in page_pdf.items():
            pdf_doc = st.session_state.doc_dict[pdf_name]

            for page_num in page_nums:
                try:
                    page = pdf_doc[page_num - 1]
                    words_info = sorted(
                        page.get_text("words"),
                        key=lambda w: (w[1], w[0])
                    )
                    lower_words = [w[4].lower() for w in words_info]

                    # 🔥 Run one highlighting loop PER keyword list
                    # -------------------------------------------------
                    for keywords in keyword_lists:     # 🔥 Multi-pass
                        i = 0
                        while i < len(lower_words):
                            window = words_info[i : i + WINDOW_SIZE]
                            window_words = [w[4].lower() for w in window]

                            keyword_count = len([w for w in window_words if w in keywords])

                            if keyword_count >= THRESHOLD_RATIO * len(keywords):

                                # Highlight all words in window
                                for w in window:
                                    rect = fitz.Rect(w[0], w[1], w[2], w[3])
                                    highlight = page.add_highlight_annot(rect)
                                    highlight.set_colors(stroke=(1, 1, 0))
                                    highlight.update()

                                i += WINDOW_SIZE
                            else:
                                i += STEP
                    # -------------------------------------------------

                    # Render final combined highlights
                    pix = page.get_pixmap(dpi=200)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    imgs.append(img)

                except Exception:
                    continue

    except Exception as e:
        st.warning(f"Could not highlight PDFs: {str(e)}")

    return imgs


def process_pdf_highlights_v2(retrieved_docs):
    """Highlight *all words* inside windows where multiple keywords co-occur."""

    imgs = []

    if not st.session_state.get("doc_dict"):
        return imgs

    try:
        # -----------------------------
        # STEP 1 — Map PDFs to relevant pages
        # -----------------------------
        page_pdf = {}
        for doc in retrieved_docs:
            try:
                pages = json.loads(str(doc.metadata.get("pages", "[]")))
                pdf_name = doc.metadata.get("pdf_name", "")
                if not pdf_name or pdf_name not in st.session_state.doc_dict:
                    continue

                page_pdf.setdefault(pdf_name, []).extend(pages)
                page_pdf[pdf_name] = list(set(page_pdf[pdf_name]))
            except Exception:
                continue

        # -----------------------------
        # STEP 2 — Extract keyword set
        # -----------------------------
        all_keywords = set()
        for doc in retrieved_docs:
            words = doc.page_content.split()
            keywords = [w.strip(".,!?;:").lower() for w in words if len(w) > 4]
            # keywords = [w.strip(".,!?;:").lower() for w in words]
            all_keywords.update(keywords[: len(keywords) // 2])

        # -----------------------------
        # STEP 3 — Highlight windows
        # -----------------------------
        WINDOW_SIZE = 220
        STEP = 35
        THRESHOLD_RATIO = 0.35

        for pdf_name, page_nums in page_pdf.items():
            pdf_doc = st.session_state.doc_dict[pdf_name]

            for page_num in page_nums:
                try:
                    page = pdf_doc[page_num - 1]
                    words_info = page.get_text("words")
                    words_info = sorted(words_info, key=lambda w: (w[1], w[0]))
                    words = [w[4].lower() for w in words_info]

                    i = 0
                    while i < len(words):
                        window = words_info[i:i + WINDOW_SIZE]
                        window_words = [w[4].lower() for w in window]

                        keyword_count = len([w for w in window_words if w in all_keywords])

                        if keyword_count >= THRESHOLD_RATIO * len(all_keywords):

                            # 🔥 Highlight *all* words in this window
                            for w in window:
                                rect = fitz.Rect(w[0], w[1], w[2], w[3])
                                highlight = page.add_highlight_annot(rect)
                                highlight.set_colors(stroke=(1, 1, 0))  # yellow
                                highlight.update()

                            # Skip over this entire block
                            i += WINDOW_SIZE

                        else:
                            i += STEP

                    # Render page
                    pix = page.get_pixmap(dpi=200)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    imgs.append(img)

                except Exception:
                    continue

    except Exception as e:
        st.warning(f"Could not highlight PDFs: {str(e)}")

    return imgs


def process_pdf_highlights_v1(retrieved_docs):
    """Process PDFs and highlight relevant sections"""
    
    imgs = []
    
    if not st.session_state.get('doc_dict'):
        return imgs
    
    try:
        # Organize pages by PDF
        page_pdf = {}
        for doc in retrieved_docs:
            try:
                doc.metadata['pages'] = json.loads(str(doc.metadata.get('pages', '[]')))
                pdf_name = doc.metadata.get('pdf_name', '')
                
                if not pdf_name or pdf_name not in st.session_state.doc_dict:
                    continue
                
                if pdf_name not in page_pdf:
                    page_pdf[pdf_name] = []
                
                page_pdf[pdf_name].extend(doc.metadata['pages'])
                page_pdf[pdf_name] = list(set(page_pdf[pdf_name]))
            except Exception as e:
                continue
        
        # Extract keywords for highlighting
        all_keywords = set()
        for doc in retrieved_docs:
            words = doc.page_content.split()
            keywords = [w.strip('.,!?;:') for w in words if len(w) > 4]
            all_keywords.update(keywords[:len(keywords) // 2])
        
        # Process each PDF and page
        for pdf_name in page_pdf:
            doc = st.session_state.doc_dict[pdf_name]
            
            for page_num in page_pdf[pdf_name]:
                try:
                    page = doc[page_num - 1]
                    
                    # Highlight keywords
                    for keyword in all_keywords:
                        text_instances = page.search_for(keyword)
                        for inst in text_instances:
                            highlight = page.add_highlight_annot(inst)
                            highlight.set_colors(stroke=[1, 1, 0])
                            highlight.update()
                    
                    # Render page to image
                    pix = page.get_pixmap(dpi=300)
                    img_bytes = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_bytes))
                    imgs.append(img)
                except Exception as e:
                    continue
        
    except Exception as e:
        st.warning(f"Could not highlight PDFs: {str(e)}")
    
    return imgs

def format_chat_history():
    """Format chat history for LLM prompt"""
    
    history = []
    for msg in st.session_state.chat_history[-6:]:  # Last 3 exchanges
        role = msg['role']
        content = msg['content']
        history.append(f"{role.capitalize()}: {content}")
    
    return "\n".join(history)