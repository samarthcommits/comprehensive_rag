import streamlit as st

def apply_custom_styles():
    """Apply improved high-contrast, modern CSS styling with neutral sidebar"""
    
    st.markdown("""
    <style>
    /* Main container */
    .main {
        padding: 2rem;
        background-color: #f9faff;
        color: #1a202c;
    }

    /* Buttons */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
        color: #ffffff;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        border: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.12);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.18);
    }
    
    div[data-testid="stHorizontalBlock"] .stButton>button:first-child {
        background: linear-gradient(135deg, #0d9488 0%, #10b981 100%);
        color: #ffffff;
    }

    .stButton>button[kind="secondary"] {
        background: linear-gradient(135deg, #ec4899 0%, #f43f5e 100%);
        color: #ffffff;
    }

    /* Chat messages */
    .stChatMessage[data-testid="user"] {
        background: linear-gradient(135deg, #e8f0fe 0%, #c3dafb 100%);
        border-left: 4px solid #2563eb;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #1e293b;
    }
    
    .stChatMessage[data-testid="assistant"] {
        background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%);
        border-left: 4px solid #16a34a;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #111827;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f1f5f9;
        color: #1e293b;
        border-radius: 8px;
        font-weight: 600;
    }

    /* File uploader */
    .uploadedFile {
        border: 2px dashed #5a67d8;
        border-radius: 8px;
        padding: 1rem;
        background-color: #f0f4ff;
        color: #1a202c;
    }

    /* Info boxes */
    .stInfo, .stSuccess, .stWarning, .stError {
        border-radius: 8px;
        padding: 1rem;
        color: #1a202c;
    }

    /* Sidebar - Cool Gray theme */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%);
        color: #1a202c;
    }
    section[data-testid="stSidebar"] .stMarkdown {
        color: #1a202c !important;
    }

    /* Selectbox and text input */
    .stSelectbox, .stTextInput {
        border-radius: 8px;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 0.5rem 1rem;
        background-color: #f8fafc;
        color: #1e293b;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
        color: #ffffff;
        font-weight: 600;
    }

    /* Cards */
    .card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        color: #1e293b;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #5a67d8;
    }

    /* Headers */
    h1, h2, h3 {
        color: #1e293b;
        font-weight: 700;
    }

    /* Divider */
    hr {
        margin: 2rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #5a67d8, transparent);
    }
    </style>
    """, unsafe_allow_html=True)
