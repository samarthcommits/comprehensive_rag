import streamlit as st
from database import CollectionDatabase, UserDatabase

def initialize_session_state():
    """Initialize all session state variables"""
    
    # User authentication
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    
    # Database handlers
    if 'db_handler' not in st.session_state:
        st.session_state.db_handler = CollectionDatabase()
    if 'user_db' not in st.session_state:
        st.session_state.user_db = UserDatabase()
    
    # Retriever and collection
    if 'retriever_obj' not in st.session_state:
        st.session_state.retriever_obj = None
    if 'collection' not in st.session_state:
        st.session_state.collection = None
    if 'setup_complete' not in st.session_state:
        st.session_state.setup_complete = False
    
    # Chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Document handling
    if 'pdf' not in st.session_state:
        st.session_state.pdf = None
    if 'doc' not in st.session_state:
        st.session_state.doc = None
    if 'context' not in st.session_state:
        st.session_state.context = []
    if 'conte' not in st.session_state:
        st.session_state.conte = []
    
    # Configuration
    if 'config' not in st.session_state:
        st.session_state.config = {}
    
    # Legacy compatibility
    if 'username' not in st.session_state:
        st.session_state.username = 'default'
    if 'some_key' not in st.session_state:
        st.session_state.some_key = 'default'

def reset_chat_state():
    """Reset chat-related session state"""
    st.session_state.chat_history = []
    st.session_state.context = []
    st.session_state.conte = []

def reset_retriever_state():
    """Reset retriever and collection state"""
    st.session_state.retriever_obj = None
    st.session_state.setup_complete = False
    st.session_state.collection = None
    st.session_state.pdf = None
    st.session_state.doc = None
    reset_chat_state()
