import streamlit as st
@st.cache_data()
def get_control():
    from controller import Control
    return Control()
from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage, AIMessage
from pymilvus import db, utility, connections
import torch
import html
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_datalist import stDatalist
from database import CollectionDatabase
torch.classes.__path__ = [] # add this line to manually set it to empty. 
import pdfplumber
import tempfile
import os
import sys
import time
import pymupdf as fitz
from PIL import Image
import io
from datetime import datetime
from database import UserDatabase
us = UserDatabase()
# sys.path.append("C:/Users/samarth.srivastava/Desktop/RAG_comprehensive")
# Page configuration
st.set_page_config(
    page_title="Document Retrieval Chatbot",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

import json
cont = get_control()

# Custom CSS for professional styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196F3;
    }
    .assistant-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4CAF50;
    }
    .stChatMessage[data-testid="user"] {
        background-color: #e3f2fd;
    }
    .stChatMessage[data-testid="assistant"] {
        background-color: #f5f5f5;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'retriever_obj' not in st.session_state:
    st.session_state.retriever_obj = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'setup_complete' not in st.session_state:
    st.session_state.setup_complete = False
if 'db_handler' not in st.session_state:
    st.session_state.db_handler = CollectionDatabase()
if 'username' not in st.session_state:
    print('set to default again')
    st.session_state.username = 'default'
if 'some_key' not in st.session_state:
    print('set to default again2')
    st.session_state.some_key = 'default'
if 'pdf' not in st.session_state:
    st.session_state.pdf = None
if 'context' not in st.session_state:
    st.session_state.context = []
if 'doc' not in st.session_state:
    st.session_state.doc = None
if 'conte' not in st.session_state:
    st.session_state.conte = []
if 'collection' not in st.session_state:
    st.session_state.collection = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
# if 'some_key' not in st.session_state:
#     st.session_state.some_key = 'default'

# Main app
st.title("🤖 Document Retrieval Chatbot")
def login_form():
    st.title("Login / Sign Up")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login")
        login_username = st.text_input("Username", key="login_user")
        login_password = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Login", key="login_btn"):
            if login_username and login_password:
                if us.validate_user(user_name=login_username, password=login_password):
                    st.success("Login successful!")
                    st.session_state.logged_in = True
                    st.session_state.user_name = login_username
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please enter both username and password")
    
    with tab2:
        st.subheader("Sign Up")
        signup_username = st.text_input("Username", key="signup_user")
        signup_password = st.text_input("Password", type="password", key="signup_pass")
        signup_password_confirm = st.text_input("Confirm Password", type="password", key="signup_pass_confirm")
        
        if st.button("Sign Up", key="signup_btn"):
            if signup_username and signup_password and signup_password_confirm:
                if signup_password != signup_password_confirm:
                    st.error("Passwords do not match")
                elif us.get_user_name_info(user_name=signup_username):
                    st.error("Username already exists")
                else:
                    us.insert_user(user_name=signup_username, password=signup_password)
                    os.mkdir(f'documents/{signup_username}')
                    st.success("Account created! Please login")
                

            else:
                st.warning("Please fill all fields")
# Configuration phase
if st.session_state.logged_in:
    st.markdown("---")
    if not st.session_state.setup_complete:
        if st.session_state.some_key:
            print('first some_key - >', st.session_state.some_key)
        st.markdown(f"## 🙋‍♂️Welcome, {st.session_state['user_name']}")
        
        st.write("Select collection or create a new one")
        
        # Create three columns for dropdowns
        conn = connections.connect(host="127.0.0.1", port="19530")
        database_list = db.list_database()
        db_list = database_list+['New User']

                
        URI = "http://localhost:19530"
        conn = connections.connect(host="127.0.0.1", port=19530)
        user_name = st.session_state.user_name
        database_list = db.list_database()
        if len(user_name)>0:
            if user_name not in database_list:
                db.create_database(db_name=user_name)
                st.rerun()
            conn = connections.connect(host="127.0.0.1", port="19530", db_name=user_name)
        # st.markdown("---")
        create_collection = st.checkbox('Create new collection')
        # File upload
        collect_list = st.session_state['db_handler'].get_all_parent_collections(username = st.session_state['user_name'])
        collect_list = [i for i in collect_list if ' ' not in i]
        if not create_collection:
            if not st.session_state.collection:
                try:
                    coll = collect_list[0]
                except:
                    coll = ''
                c_list = collect_list
            else:
                coll = st.session_state.collection
                c_list = collect_list
            try:
                ind = c_list.index(coll)
            except:
                ind = None
            collec = st.selectbox('Collection Name', options=c_list, index=ind)
            st.session_state.collection = collec
            collect_name = st.session_state.collection
        else:
            st.session_state['collection'] = st.text_input(placeholder='(name   must be unique)', label='Enter collection name :')
        if st.button('Proceed'):
            retriever_obj = cont.hybrid(
                                # database=database,
                                # chunking=chunking,
                                # retriever=retriever,
                                # raw_text=content,
                                raw_text='',
                                collect_name=st.session_state['collection'],
                                user_name=st.session_state['user_name'],
                                # pdf=doc
                            )
            st.session_state.retriever_obj = retriever_obj
            st.session_state.setup_complete = True
            st.session_state.config = {
                # 'database': database,
                # 'chunking': chunking,
                # 'retriever': retriever,
                'user_name': user_name,
            }
            st.rerun()
        else:

            st.markdown("### Upload Document")
            uploaded_file = st.file_uploader(
                "Choose a text file",
                type=['txt', 'pdf'],
                help="Upload a .txt file containing your documents"
            )
            if st.button('Logout'):
                st.session_state.logged_in = False
                st.rerun()
        
        # Initialize button
        if uploaded_file is not None:
            
            if st.button("🚀 Initialize Retriever", use_container_width=True):
                with st.spinner("Setting up retriever..."):
                    try:
                        # Save uploaded file to temporary location
                        print('here------->', uploaded_file.type)
                        if uploaded_file.type=='text/plain':
                            print('text file uploaded')
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8') as tmp_file:
                                content = uploaded_file.read().decode('utf-8')
                                tmp_file.write(content)
                                tmp_file_path = tmp_file.name
                            
                            os.unlink(tmp_file_path)
                        
                        if uploaded_file.type=='application/pdf':
                            print('pdf file uploaded')
                            content = ''
                            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                            st.session_state.doc = doc
                            with pdfplumber.open(uploaded_file) as pdf:
                                st.session_state.pdf = pdf
                                for page in pdf.pages:
                                    content = content+page.extract_text()
                            save_dir = f"documents/{st.session_state['user_name']}/{st.session_state['collection']}"
                            if not os.path.exists(save_dir):
                                os.mkdir(save_dir)
                            file_name = os.path.join(save_dir, uploaded_file.name)
                            with open(file_name, "wb") as f:
                                f.write(uploaded_file.getbuffer())


                            
                        # Call the controller function
                        # create_collection = st.checkbox('Create new collection')
                        if create_collection:
                            retriever_obj = cont.hybrid(
                                # database=database,
                                # chunking=chunking,
                                # retriever=retriever,
                                raw_text=content,
                                collect_name=st.session_state['collection'],
                                user_name=st.session_state['user_name'],
                                pdf=doc,
                                pdf_full = uploaded_file
                            )
                        else:
                            retriever_obj = cont.hybrid(
                                # database=database,
                                # chunking=chunking,
                                # retriever=retriever,
                                raw_text=content,
                                collect_name=st.session_state['collection'],
                                user_name=st.session_state['user_name'],
                                pdf=doc,
                                pdf_full=uploaded_file
                            )

                        
                        # Clean up temporary file
                        # Store in session state
                        st.session_state.retriever_obj = retriever_obj
                        st.session_state.setup_complete = True
                        st.session_state.config = {
                            # 'database': database,
                            # 'chunking': chunking,
                            # 'retriever': retriever,
                            'user_name': user_name,
                            'content': content
                        }
                        st.success("✅ Retriever initialized successfully!")
                        st.rerun()
                        
                    except Exception as e: 
                             
                        st.error(f"❌ Error initializing retriever: {str(e)}")

                    

    # Chat interface
    else:
        # Show current configuration in sidebar
        with st.sidebar:
            st.markdown("### Current Configuration")
            st.info(f"""
            **Username:** {st.session_state.config['user_name']}
            """)
            print('a')
            from io import BytesIO

            # Path where you saved the file earlier
            file_path = f"documents/{st.session_state['user_name']}/{st.session_state['collection']}"
            pdf_names = os.listdir(file_path)
            try:
                for i in ['ann', 'sparse', 'dense', 'rerank']:
                    pdf_name = st.session_state['db_handler'].get_collection_info(user_name = st.session_state['user_name'], collection_name = f"{st.session_state['collection']}_{i}")['pdf_name']
                    if pdf_name!='' and len(pdf_name)>0 and pdf_name:
                        break
            except:
                pdf_name = ''
            
            pdf_dict = {}
            doc_dict = {}
            for i in pdf_names:
                file_p = os.path.join(file_path, i)
                with open(file_p, "rb") as f:
                    file_bytes = f.read()              
                # Create a "file-like" object similar to Streamlit's uploaded file
                fake_uploaded_file = BytesIO(file_bytes)
                # if not st.session_state.pdf:
                with pdfplumber.open(fake_uploaded_file) as pdf:
                    pdf_dict[i] = pdf
                doc_dict[i] = fitz.open(stream=file_bytes, filetype="pdf")
            # Read the file back as binary
            print('pdf-name here  ', pdf_name, st.session_state['user_name'], st.session_state['collection'])
            if pdf_name!='' and len(pdf_name)>0 and pdf_name:
                dir = pdf_name
                file_p = os.path.join(file_path, dir)
                with open(file_p, "rb") as f:
                    file_bytes = f.read()
                

                 
                # Create a "file-like" object similar to Streamlit's uploaded file
                fake_uploaded_file = BytesIO(file_bytes)
                # if not st.session_state.pdf:
                with pdfplumber.open(fake_uploaded_file) as pdf:
                    st.session_state.pdf = pdf
                # if not st.session_state.doc:
                st.session_state.doc = fitz.open(stream=file_bytes, filetype="pdf")
            
            conn = connections.connect(db_name=st.session_state.config['user_name'], host="127.0.0.1", port="19530")
            collect_change = st.checkbox('Change collection')
            if collect_change:
                collections = st.selectbox('Collection Name', options=utility.list_collections())
                if collections:
                    collection_info = st.session_state.db_handler.get_collection_info(
                        collection_name=collections,
                        user_name=st.session_state.config['user_name']
                    )
                else:
                    collection_info = None
                
                if collection_info:
                    # Use stored retrieval technique
                    retrieval_technique = collection_info['retrieval_technique']
                    database_type = collection_info['database_type']
                    chunking_strategy = collection_info['chunking_strategy']
                    
                    st.info(f"📊 **Retrieval:** {retrieval_technique} | **Chunking:** {chunking_strategy}")

                # with st.spinner('Modifying retriever, please wait...', show_time=True):
                #     retriever_obj = cont.create_retriever(
                #                     database=st.session_state.config['database'],
                #                     chunking=st.session_state.config['chunking'],
                #                     retriever=st.session_state.config['retriever'],
                #                     # raw_text=st.session_state.config['content'],
                #                     collect_name=collections,
                #                     user_name=st.session_state.config['user_name']
                #                 )
                        
                    # st.session_state.retriever_obj = retriever_obj
            print('b')
            if st.button("🔄 Reset Configuration"):
                st.session_state.retriever_obj = None
                st.session_state.chat_history = []
                st.session_state.setup_complete = False
                st.rerun()
        print('c')
        st.markdown("### 💬 Chat with Your Documents")
        
        # Display chat history
        chat_container = st.container()
        print('d')
        with chat_container:
            for message in st.session_state.chat_history:
                with st.chat_message(message['role']):
                    st.markdown(message['content'], unsafe_allow_html=True)
                    if message['role'] == 'assistant' and 'context' in message:
                        with st.expander("View Context"):
                            for i, page in enumerate(message['conte'], start=1):
                                # st.markdown(f"**Page {page.page_number}**")
                                st.image(page)
                                if i < len(message['context']):
                                    st.divider()
                        
        print('e')
        # Chat input
        user_query = st.chat_input("Ask a question about your documents...")
        
        if user_query:
            # Add user message to history
            st.session_state.chat_history.append({
                'role': 'user',
                'content': user_query
            })
            
            with st.spinner("Generating response...", show_time=True):
                try:
                    full_context = []
                    imgs = []
                    retriever = st.session_state.retriever_obj
                    starttime = time.perf_counter()
                    retrieved_docs = retriever.get_all_results(user_query)
                    try:
                        print(retrieved_docs[0], '>>>>>>>>>m>e>t>a')
                    except:
                        st.info('No data in the vector store!')
                    if st.session_state.pdf:
                        all_pages = st.session_state.pdf.pages
                        page_n = []
                        print('a1')
                        page_pdf = {}
                        for i in retrieved_docs:
                            print(str(i.metadata['pages']), 'here page')
                            i.metadata['pages'] = json.loads(str(i.metadata['pages']))
                            if i.metadata['pdf_name'] == '':
                                print(i)
                                continue
                            if not page_pdf[i.metadata['pdf_name']]:
                                page_pdf[i.metadata['pdf_name']] = i.metadata['pages']
                            page_pdf[i.metadata['pdf_name']] = list(set(page_pdf[i.metadata['pdf_name']]+i.metadata['pages'])) 
                            page_n = page_n+i.metadata['pages']
                        full_context = []
                        # for i in list(set(page_n)):
                        #     full_context.append(all_pages[i])
                        doc = st.session_state.doc
                        page_numbers = list(set(page_n))
                        print('a2')
                        for pdf_p in page_pdf:
                            doc = doc_dict[pdf_p]
                            page_numbers = page_pdf[pdf_p]
                            for page_num in page_numbers:
                                print('a2.1')
                                page = doc[page_num - 1]
                                all_keywords = set()
                                for retrieved_doc in retrieved_docs:
                                    words = retrieved_doc.page_content.split()
                                    keywords = [w.strip('.,!?;:') for w in words if len(w) > 4]
                                    len_k = len(keywords) // 2
                                    all_keywords.update(keywords[:len_k])
                                
                                # Highlight all keywords at once
                                for keyword in all_keywords:
                                    text_instances = page.search_for(keyword)
                                    for inst in text_instances:
                                        highlight = page.add_highlight_annot(inst)
                                        highlight.set_colors(stroke=[1, 1, 0])
                                        highlight.update()
                                    
                                    # Render with highlights
                                pix = page.get_pixmap(dpi=500)
                                img_bytes = pix.tobytes("png")
                                img = Image.open(io.BytesIO(img_bytes))
                                imgs.append(img)
                        print('a3')   
                            # Display in Streamlit
                            # st.image(img, caption=f"Page {page_num}")
                        
                        st.session_state['context'].append(full_context)
                        st.session_state['conte'].append(imgs)
                    endtime = time.perf_counter()
                    print('Retrieval time', endtime-starttime)
                    # Prepare context from retrieved documents
                    context = "\n\n".join([doc.page_content for doc in retrieved_docs])
                    # print('context is ----------->\n', context)
                    # Initialize LLM
                    llm = ChatOllama(model="gemma3:27b", base_url = 'http://10.10.64.25:9500/')
                    

                    
                    # Generate response
                    prompt = f"""Based on the following context, answer the user's question.
                    
    Context:
    {context}

    Chat History: {st.session_state.chat_history}

    Question: {user_query}

    Answer:"""
                    
                    response = llm.invoke(prompt)
                    answer = response.content if hasattr(response, 'content') else str(response)
                    
                    # Add assistant response to history
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': answer,
                        'context': full_context,
                        'conte': imgs
                    })
                    
                    st.rerun()
                    
                except Exception as e:
                    full_context = []
                    imgs = []
                    retriever = st.session_state.retriever_obj
                    starttime = time.perf_counter()
                    retrieved_docs = retriever.get_all_results(user_query)
                    try:
                        print(retrieved_docs[0], '>>>>>>>>>m>e>t>a')
                    except:
                        st.info('No data in the vector store!')
                    if st.session_state.pdf:
                        all_pages = st.session_state.pdf.pages
                        page_n = []
                        print('a1')
                        page_pdf = {}
                        for i in retrieved_docs:
                            print(str(i.metadata['pages']), 'here page')
                            i.metadata['pages'] = json.loads(str(i.metadata['pages']))
                            if i.metadata['pdf_name'] == '':
                                print(i)
                                continue
                            if i.metadata['pdf_name'] not in page_pdf:
                                page_pdf[i.metadata['pdf_name']] = i.metadata['pages']
                            page_pdf[i.metadata['pdf_name']] = list(set(page_pdf[i.metadata['pdf_name']]+i.metadata['pages'])) 
                            page_n = page_n+i.metadata['pages']
                        full_context = []
                        # for i in list(set(page_n)):
                        #     full_context.append(all_pages[i])
                        doc = st.session_state.doc
                        page_numbers = list(set(page_n))
                        print('a2')
                        print('here dlkfj ', doc_dict)
                        for pdf_p in page_pdf:
                            doc = doc_dict[pdf_p]
                            page_numbers = page_pdf[pdf_p]
                            for page_num in page_numbers:
                                print('a2.1')
                                page = doc[page_num - 1]
                                all_keywords = set()
                                for retrieved_doc in retrieved_docs:
                                    words = retrieved_doc.page_content.split()
                                    keywords = [w.strip('.,!?;:') for w in words if len(w) > 4]
                                    len_k = len(keywords) // 2
                                    all_keywords.update(keywords[:len_k])
                                
                                # Highlight all keywords at once
                                for keyword in all_keywords:
                                    text_instances = page.search_for(keyword)
                                    for inst in text_instances:
                                        highlight = page.add_highlight_annot(inst)
                                        highlight.set_colors(stroke=[1, 1, 0])
                                        highlight.update()
                                    
                                    # Render with highlights
                                pix = page.get_pixmap(dpi=500)
                                img_bytes = pix.tobytes("png")
                                img = Image.open(io.BytesIO(img_bytes))
                                imgs.append(img)
                        print('a3')   
                            # Display in Streamlit
                            # st.image(img, caption=f"Page {page_num}")
                        
                        st.session_state['context'].append(full_context)
                        st.session_state['conte'].append(imgs)
                    endtime = time.perf_counter()
                    print('Retrieval time', endtime-starttime)
                    # Prepare context from retrieved documents
                    context = "\n\n".join([doc.page_content for doc in retrieved_docs])
                    # print('context is ----------->\n', context)
                    # Initialize LLM
                    llm = ChatOllama(model="gemma3:27b", base_url = 'http://10.10.64.25:9500/')
                    

                    
                    # Generate response
                    prompt = f"""Based on the following context, answer the user's question.
                    
    Context:
    {context}

    Chat History: {st.session_state.chat_history}

    Question: {user_query}

    Answer:"""
                    
                    response = llm.invoke(prompt)
                    answer = response.content if hasattr(response, 'content') else str(response)
                    
                    # Add assistant response to history
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': answer,
                        'context': full_context,
                        'conte': imgs
                    })
                    
                    st.rerun()
                    st.error(f"❌ Error generating response: {str(e)}")

else:
    login_form()
