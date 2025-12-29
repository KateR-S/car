"""Authentication module for the application."""

import streamlit as st
import config


def check_password() -> bool:
    """Check if user is authenticated.
    
    Returns:
        bool: True if authenticated, False otherwise
    """
    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    # If already authenticated, return True
    if st.session_state.authenticated:
        return True
    
    # Show login form
    st.title("🔐 Attendance Tracking App")
    st.markdown("### Please log in to continue")
    
    password = st.text_input("Password", type="password", key="password_input")
    
    col1, col2, _ = st.columns([1, 1, 3])
    with col1:
        if st.button("Login", type="primary"):
            if password == config.DEFAULT_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password. Please try again.")
    
    with col2:
        if st.button("Clear"):
            st.session_state.password_input = ""
            st.rerun()
    
    st.markdown("---")
    st.info(f"💡 **Note**: Default password is `{config.DEFAULT_PASSWORD}`")
    
    return False


def logout():
    """Log out the current user."""
    st.session_state.authenticated = False
    st.rerun()
