import streamlit as st
import os

def show():
    """Authentication page - Login and Sign Up"""
    
    # Center the content
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center; color: #667eea;'>🤖 Document Retrieval Chatbot</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #718096;'>Intelligent document analysis powered by AI</p>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
        
        with tab1:
            show_login()
        
        with tab2:
            show_signup()

def show_login():
    """Login form"""
    st.markdown("### Welcome Back!")
    st.markdown("Please enter your credentials to continue")
    
    with st.form("login_form"):
        login_username = st.text_input("Username", placeholder="Enter your username")
        login_password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("Login", use_container_width=True)
        with col2:
            st.form_submit_button("Clear", use_container_width=True, type="secondary")
        
        if submit:
            if not login_username or not login_password:
                st.warning("⚠️ Please enter both username and password")
            else:
                us = st.session_state.user_db
                if us.validate_user(user_name=login_username, password=login_password):
                    st.success("✅ Login successful!")
                    st.session_state.logged_in = True
                    st.session_state.user_name = login_username
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")

def show_signup():
    """Sign up form"""
    st.markdown("### Create New Account")
    st.markdown("Join us to start analyzing your documents")
    
    with st.form("signup_form"):
        signup_username = st.text_input("Username", placeholder="Choose a username")
        signup_password = st.text_input("Password", type="password", placeholder="Choose a password")
        signup_password_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("Sign Up", use_container_width=True)
        with col2:
            st.form_submit_button("Clear", use_container_width=True, type="secondary")
        
        if submit:
            if not signup_username or not signup_password or not signup_password_confirm:
                st.warning("⚠️ Please fill all fields")
            elif signup_password != signup_password_confirm:
                st.error("❌ Passwords do not match")
            elif len(signup_password) < 6:
                st.error("❌ Password must be at least 6 characters long")
            else:
                us = st.session_state.user_db
                if us.get_user_name_info(user_name=signup_username):
                    st.error("❌ Username already exists. Please choose another one.")
                else:
                    try:
                        us.insert_user(user_name=signup_username, password=signup_password)
                        # Create user document directory
                        user_dir = f'documents/{signup_username}'
                        if not os.path.exists(user_dir):
                            os.makedirs(user_dir)
                        st.success("✅ Account created successfully! Please login.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Error creating account: {str(e)}")

