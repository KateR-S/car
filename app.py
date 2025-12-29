"""Main Streamlit application for Attendance Tracking."""

import streamlit as st
from src.auth import check_password, logout
from src.data_manager import DataManager
from src.pages.employees import render_employees_page
from src.pages.practices import render_practices_page
from src.pages.touches import render_touches_page
from src.pages.methods import render_methods_page


# Page configuration
st.set_page_config(
    page_title="Attendance Tracking App",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    """Main application entry point."""
    
    # Check authentication
    if not check_password():
        return
    
    # Initialize data manager
    data_manager = DataManager()
    
    # Sidebar navigation
    with st.sidebar:
        st.title("📊 Attendance Tracker")
        st.markdown("---")
        
        # Navigation menu
        page = st.radio(
            "Navigation",
            ["🏠 Home", "👥 Employees", "📅 Practices", "🎯 Touches", "📚 Methods"],
            key="navigation"
        )
        
        st.markdown("---")
        
        # Statistics
        st.markdown("### 📈 Quick Stats")
        employees = data_manager.get_employees()
        practices = data_manager.get_practices()
        touches = data_manager.get_touches()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Employees", len(employees))
            st.metric("Practices", len(practices))
        with col2:
            st.metric("Touches", len(touches))
        
        st.markdown("---")
        
        # Logout button
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            logout()
    
    # Main content area
    if page == "🏠 Home":
        render_home_page(data_manager)
    elif page == "👥 Employees":
        render_employees_page(data_manager)
    elif page == "📅 Practices":
        render_practices_page(data_manager)
    elif page == "🎯 Touches":
        render_touches_page(data_manager)
    elif page == "📚 Methods":
        render_methods_page(data_manager)


def render_home_page(data_manager: DataManager):
    """Render the home/dashboard page."""
    st.title("🏠 Attendance Tracking Dashboard")
    st.markdown("Welcome to the Attendance Tracking App!")
    
    st.markdown("---")
    
    # Overview section
    col1, col2, col3 = st.columns(3)
    
    employees = data_manager.get_employees()
    practices = data_manager.get_practices()
    touches = data_manager.get_touches()
    
    with col1:
        st.markdown("### 👥 Employees")
        st.metric("Total", len(employees))
        if employees:
            members = sum(1 for e in employees if e.member)
            st.caption(f"Members: {members} | Non-members: {len(employees) - members}")
    
    with col2:
        st.markdown("### 📅 Practices")
        st.metric("Total", len(practices))
        if practices:
            locations = {}
            for p in practices:
                locations[p.location] = locations.get(p.location, 0) + 1
            st.caption(f"Locations: {', '.join(locations.keys())}")
    
    with col3:
        st.markdown("### 🎯 Touches")
        st.metric("Total", len(touches))
        if touches:
            methods = set(t.method for t in touches)
            st.caption(f"Unique methods: {len(methods)}")
    
    st.markdown("---")
    
    # Quick start guide
    st.markdown("### 🚀 Quick Start Guide")
    
    with st.expander("ℹ️ How to use this app", expanded=False):
        st.markdown("""
        #### Getting Started
        
        1. **Add Employees** 👥
           - Navigate to the Employees page
           - Add your team members with their details
           - Specify if they are members and their resident type
        
        2. **Create Practices** 📅
           - Go to the Practices page
           - Add all-hands days with dates and locations
           - Practices represent your events
        
        3. **Organize Touches** 🎯
           - Visit the Touches page
           - Create workshops (touches) for each practice
           - Assign a conductor (facilitator)
           - Fill up to 12 bell slots with employees
        
        #### Key Terms
        
        - **Practice**: An all-hands day event (up to 8 touches per practice)
        - **Touch**: A workshop within a practice
        - **Bell**: A participant slot in a touch (12 bells per touch)
        - **Conductor**: The facilitator of a touch
        - **Method**: The name/title of a workshop
        
        #### Tips
        
        - Use the edit (✏️) and delete (🗑️) buttons to manage your data
        - Data is automatically saved and persists across sessions
        - The sidebar shows quick statistics at a glance
        """)
    
    # Recent activity
    st.markdown("### 📋 Recent Activity")
    
    if not employees and not practices and not touches:
        st.info("👋 No data yet! Start by adding employees, then create practices and touches.")
    else:
        # Show recent practices
        if practices:
            st.markdown("#### Latest Practices")
            recent_practices = sorted(practices, key=lambda p: p.date, reverse=True)[:3]
            for p in recent_practices:
                touch_count = len(data_manager.get_touches(p.id))
                st.markdown(f"- **{p.date}** at {p.location} ({touch_count} touch(es))")
        
        # Show method usage
        if touches:
            st.markdown("#### Popular Methods")
            method_counts = {}
            for t in touches:
                method_counts[t.method] = method_counts.get(t.method, 0) + 1
            
            sorted_methods = sorted(method_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            for method, count in sorted_methods:
                st.markdown(f"- **{method}**: {count} time(s)")


if __name__ == "__main__":
    main()
