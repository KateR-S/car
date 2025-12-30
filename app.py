"""Main Streamlit application for Attendance Tracking."""

import streamlit as st
import logging
from src.auth import check_password, logout
from src.data_manager import (
    get_data_manager, 
    get_cached_employees,
    get_cached_practices,
    get_cached_touches,
    get_cached_touches_by_date,
    get_cached_methods
)
from src.pages.employees import render_employees_page
from src.pages.practices import render_practices_page
from src.pages.touches import render_touches_page
from src.pages.methods import render_methods_page

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Page configuration
st.set_page_config(
    page_title="Attendance Tracking App",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    """Main application entry point."""
    logger.info("Starting application")
    
    # Check authentication
    if not check_password():
        logger.debug("Authentication failed or pending")
        return
    
    logger.debug("Authentication successful")
    
    # Initialize data manager (will use Neon if configured, with connection pooling via cache_resource)
    logger.debug("Initializing data manager")
    data_manager = get_data_manager()
    logger.debug("Data manager initialized")
    
    # Sidebar navigation
    with st.sidebar:
        st.title("📊 Attendance Tracker")
        st.markdown("---")
        
        # Navigation menu
        page = st.radio(
            "Navigation",
            ["Home", "Ringers", "Practices", "Touches", "Methods"],
            key="navigation"
        )
        
        st.markdown("---")
        
        # Statistics - use cached functions for better performance
        st.markdown("### 📈 Quick Stats")
        logger.debug("Fetching data for sidebar stats")
        employees = get_cached_employees(data_manager)
        practices = get_cached_practices(data_manager)
        touches = get_cached_touches(data_manager)
        logger.debug(f"Stats: {len(employees)} employees, {len(practices)} practices, {len(touches)} touches")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Ringers", len(employees))
            st.metric("Practices", len(practices))
        with col2:
            st.metric("Touches", len(touches))
        
        st.markdown("---")
        
        # Logout button
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            logout()
    
    # Main content area
    logger.info(f"Rendering page: {page}")
    if page == "Home":
        render_home_page(data_manager)
    elif page == "Ringers":
        render_employees_page(data_manager)
    elif page == "Practices":
        render_practices_page(data_manager)
    elif page == "Touches":
        render_touches_page(data_manager)
    elif page == "Methods":
        render_methods_page(data_manager)


def render_home_page(data_manager):
    """Render the home/dashboard page."""
    st.title("Attendance Tracking Dashboard")
    st.markdown("Welcome to the Attendance Tracking App!")
    
    st.markdown("---")
    
    # Overview section
    col1, col2, col3 = st.columns(3)
    
    # Use cached data functions for better performance
    logger.debug("Fetching data for home page")
    employees = get_cached_employees(data_manager)
    practices = get_cached_practices(data_manager)
    touches = get_cached_touches(data_manager)
    logger.debug("Home page data fetched")
    
    with col1:
        st.markdown("### Ringers")
        st.metric("Total", len(employees))
        if employees:
            members = sum(1 for e in employees if e.member)
            st.caption(f"Members: {members} | Non-members: {len(employees) - members}")
    
    with col2:
        st.markdown("### Practices")
        st.metric("Total", len(practices))
        if practices:
            locations = {}
            for p in practices:
                locations[p.location] = locations.get(p.location, 0) + 1
            st.caption(f"Locations: {', '.join(locations.keys())}")
    
    with col3:
        st.markdown("### Touches")
        st.metric("Total", len(touches))
        if touches:
            # Get unique method IDs and count them
            method_ids = set(t.method_id for t in touches if t.method_id)
            st.caption(f"Unique methods: {len(method_ids)}")
    
    st.markdown("---")
    
    # Quick start guide
    st.markdown("### 🚀 Quick Start Guide")
    
    with st.expander("ℹ️ How to use this app", expanded=False):
        st.markdown("""
        #### Getting Started

        To track details of who rang what tonight:

        1. **Add a new Practice**
           - Navigate to the Practices page
           - Add a new practice and make sure the date is correct
           - You will only need to do this once per practice

        2. **Add a new Touch**
           - Navigate to the Touches page
           - Create a new touch
           - Fill in the touch and ringers
        
        - **If you have issues**
           - If you are missing a ringer, you need to add them in the "Ringers" page.
           - If you are missing a method, you need to add it in the "Methods" page.
           - Use the edit (✏️) and delete (🗑️) buttons to manage your data
        """)
    
    # Recent activity
    st.markdown("### Recent Activity")
    
    if not employees and not practices and not touches:
        st.info("👋 No data yet! Start by adding ringers, then create practices and touches.")
    else:
        # Show recent practices
        if practices:
            st.markdown("#### Latest Practices")
            recent_practices = sorted(practices, key=lambda p: p.date, reverse=True)[:3]
            for p in recent_practices:
                touch_count = len(get_cached_touches(data_manager, p.id))
                st.markdown(f"- **{p.date}** at {p.location} ({touch_count} touch(es))")
        
        # Show method usage
        if touches:
            st.markdown("#### Popular Methods")
            # Get all methods
            all_methods = {m.id: m for m in get_cached_methods(data_manager)}
            method_counts = {}
            for t in touches:
                if t.method_id and t.method_id in all_methods:
                    method_name = all_methods[t.method_id].name
                    method_counts[method_name] = method_counts.get(method_name, 0) + 1
            
            if method_counts:
                sorted_methods = sorted(method_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                for method, count in sorted_methods:
                    st.markdown(f"- **{method}**: {count} time(s)")
            else:
                st.caption("No methods assigned yet")


if __name__ == "__main__":
    main()
