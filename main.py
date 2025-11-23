import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Document Retrieval Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import session state initializer
from utils.session_state import initialize_session_state
from utils.styles import apply_custom_styles

# Initialize session state
initialize_session_state()

# Apply custom styles
apply_custom_styles()

# Import page modules
from check import auth, document_management, chat_interface

def main():
    """Main application entry point"""
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🤖 RAG Chatbot")
        st.markdown("---")
        
        if st.session_state.logged_in:
            st.success(f"👤 Logged in as: **{st.session_state.user_name}**")
            st.markdown("---")
            
            # Navigation
            if 'check2' in st.session_state:
                print('yes')
                if st.session_state['check2']:
                    st.session_state['check_key1'] = "💬 Chat"
                    st.session_state['check2'] = False
                    st.rerun()

            print('no')
            page = st.radio(
                "Navigation",
                ["📚 Document Management", "💬 Chat"],
                label_visibility="collapsed", 
                key='check_key1'
            )
            
            st.markdown("---")
            
            if st.button("🚪 Logout", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        else:
            st.info("Please login to continue")
            page = "auth"
    
    # Route to appropriate page
    if not st.session_state.logged_in:
        auth.show()
    elif page == "📚 Document Management":
        document_management.show()
    elif page == "💬 Chat":
        chat_interface.show()

if __name__ == "__main__":
    main()