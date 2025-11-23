import streamlit as st
import os
import tempfile
import time
import pdfplumber
import pymupdf as fitz
from pymilvus import MilvusClient
from utils.session_state import reset_chat_state

# Lazy import controller
@st.cache_resource()
def get_control():
    from controller import Control
    return Control()

def show():
    """Document management page"""
    
    st.title("📚 Document Management")
    st.markdown("Manage your document collections and upload new files")
    
    # Initialize connection
    db1 = MilvusClient(uri = os.environ['MILVUS_URL'])
    # db = 
    
    # Ensure user database exists
    database_list = db1.list_databases()
    user_name = st.session_state.user_name
    
    if user_name not in database_list:
        db1.create_database(db_name=user_name)
        st.success(f"✅ Created database for user: {user_name}")
    
    db1 = MilvusClient(uri = os.environ['MILVUS_URL'], db_name=user_name)
    
    # Main layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        show_collection_selector()
    
    with col2:
        show_stats()
    
    st.markdown("---")
    
    # Document upload section
    collect_list = st.session_state.db_handler.get_all_parent_collections(
        username=st.session_state.user_name
    )
    # if 'collection' in st.session_state:
    #     if st.session_state.collection:
    #         if st.session_state.collection in collect_list:
    

def show_collection_selector():
    """Collection selection and creation"""
    
    st.markdown("### 📁 Select or Create Collection")
    
    # Get existing collections
    collect_list = st.session_state.db_handler.get_all_parent_collections(
        username=st.session_state.user_name
    )
    collect_list = [i for i in collect_list if ' ' not in i]
    
    # Collection mode selection
    inde = None
    if 'new_collection_input' in st.session_state:
        print(st.session_state['new_collection_input'])
        if st.session_state['new_collection_input']:
            st.session_state.check_radio = "Select Existing Collection"
            st.session_state['new_collection_input'] = None
        # st.rerun()
    
    mode = st.radio(
        "Choose action:",
        ["Select Existing Collection", "Create New Collection"],
        horizontal=True,
        label_visibility="collapsed",
        key='check_radio'
        # index=inde
    )
    
    if mode == "Select Existing Collection":
        if not collect_list:
            st.info("📭 No collections found. Create a new one to get started!")
            return
        
        current_coll = st.session_state.collection if st.session_state.collection else (collect_list[0] if collect_list else '')
        
        try:
            ind = collect_list.index(current_coll) if current_coll in collect_list else 0
        except:
            ind = 0
        
        collection_name = st.selectbox(
            'Select Collection',
            options=collect_list,
            index=ind,
            help="Choose an existing collection to work with"
        )
        st.session_state.collection = collection_name
        
        # Show collection info
        if collection_name:
            show_collection_info(collection_name)
        st.divider()
        st.markdown("## Add more documents or proceed with the selected collection")
        show_document_upload()
    
    else:
        new_collection = st.text_input(
            'Collection Name',
            placeholder='Enter unique collection name (no spaces)',
            help="Collection name must be unique and contain no spaces",
            # key="new_collection_input"
        )
        
        if new_collection:
            if ' ' in new_collection:
                st.error("❌ Collection name cannot contain spaces")
            elif new_collection in collect_list:
                st.error("❌ Collection name already exists, chose another name")
            else:
                st.session_state.collection = new_collection
                st.success(f"✅ Ready to create collection: {new_collection}")
                # st.session_state.new_collection_input = ""
        show_document_upload(initialize=False)

def show_collection_info(collection_name):
    """Display information about selected collection"""
    
    try:
        # Try to get info from any of the collection variants
        for suffix in ['ann', 'sparse', 'dense', 'rerank']:
            try:
                info = st.session_state.db_handler.get_collection_info(
                    user_name=st.session_state.user_name,
                    collection_name=f"{collection_name}_{suffix}"
                )
                if info:
                    with st.expander("ℹ️ Collection Details", expanded=False):
                        st.markdown(f"**Retrieval:** {info.get('retrieval_technique', 'N/A')}")
                        st.markdown(f"**Database:** {info.get('database_type', 'N/A')}")
                        st.markdown(f"**Chunking:** {info.get('chunking_strategy', 'N/A')}")
                        st.markdown(f"**Documents:** {info.get('pdf_name', 'Multiple')}")
                    break
            except:
                continue
    except Exception as e:
        st.warning("Could not load collection details")

def show_stats():
    """Display user statistics"""
    
    st.markdown("### 📊 Statistics")
    
    collect_list = st.session_state.db_handler.get_all_parent_collections(
        username=st.session_state.user_name
    )
    
    st.metric("Total Collections", len(collect_list))
    
    if st.session_state.collection:
        st.metric("Active Collection", st.session_state.collection)

def show_document_upload(initialize = True, upload = True):
    """Document upload interface"""
    
    st.markdown("### 📤 Upload Documents")
    
    if not st.session_state.collection:
        st.warning("⚠️ Please select or create a collection first")
        return
    
    if 'collection' in st.session_state:
        if st.session_state.collection:
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=['txt', 'pdf'],
                help="Upload PDF or TXT files to add to your collection"
            )
    
    col1, col2 = st.columns(2)
    # if uploaded_file:
    with col1:
        if st.button("🚀 Use Selected Collection", use_container_width=True, disabled=not st.session_state.collection):
            initialize_empty_collection()
            st.session_state['check2'] = True
            st.rerun()
    
    with col2:
        if uploaded_file and st.button("📁 Process & Upload", use_container_width=True):
            process_and_upload(uploaded_file)

def initialize_empty_collection():
    """Initialize a collection without uploading documents"""
    
    with st.spinner("⏳ Initializing collection..."):
        try:
            cont = get_control()
            retriever_obj = cont.hybrid(
                raw_text='',
                collect_name=st.session_state.collection,
                user_name=st.session_state.user_name,
            )
            
            st.session_state.retriever_obj = retriever_obj
            st.session_state.setup_complete = True
            st.session_state.config = {
                'user_name': st.session_state.user_name,
            }
            
            st.success("✅ Collection initialized successfully!")
            reset_chat_state()
            
            time.sleep(1)
            st.session_state['check2'] = True
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error initializing collection: {str(e)}")

def process_and_upload(uploaded_file):
    """Process and upload document to collection"""
    
    with st.spinner(f"⏳ Processing {uploaded_file.name}..."):
        try:
            content = ''
            doc = None
            
            # Process based on file type
            if uploaded_file.type == 'text/plain':
                content = uploaded_file.read().decode('utf-8')
                st.info("📄 Text file processed")
            
            elif uploaded_file.type == 'application/pdf':
                # Extract text and create doc object
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                st.session_state.doc = doc
                
                # Reset file pointer
                uploaded_file.seek(0)
                
                with pdfplumber.open(uploaded_file) as pdf:
                    st.session_state.pdf = pdf
                    for page in pdf.pages:
                        content += page.extract_text() or ''
                
                # Save PDF file
                save_dir = f"documents/{st.session_state.user_name}/{st.session_state.collection}"
                os.makedirs(save_dir, exist_ok=True)
                
                file_path = os.path.join(save_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    uploaded_file.seek(0)
                    f.write(uploaded_file.getbuffer())
                
                st.info(f"📄 PDF processed: {len(doc)} pages")
            
            # Create/update retriever
            cont = get_control()
            retriever_obj = cont.hybrid(
                raw_text=content,
                collect_name=st.session_state.collection,
                user_name=st.session_state.user_name,
                pdf=doc,
                pdf_full=uploaded_file,
                retriever=['Sparse Retrieval', 'ANN Retrieval', 'Dense Retrieval']
            )
            
            st.session_state.retriever_obj = retriever_obj
            st.session_state.setup_complete = True
            st.session_state.config = {
                'user_name': st.session_state.user_name,
                'content': content
            }
            
            st.success(f"✅ {uploaded_file.name} uploaded successfully!")
            # st.balloons()
            if 'new_collection_input' not in st.session_state:
                st.session_state.new_collection_input = 'checked'
            reset_chat_state() 
            # time.sleep(2)
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            import traceback
            with st.expander("Error Details"):
                st.code(traceback.format_exc())
