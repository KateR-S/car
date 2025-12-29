"""Practice management page."""

import streamlit as st
import uuid
from datetime import datetime
from src.data_manager import DataManager
from src.models import Practice
import config


def render_practices_page(data_manager: DataManager):
    """Render the practices management page."""
    st.title("📅 Practice Management")
    
    # Tabs for different actions
    tab1, tab2 = st.tabs(["📋 View Practices", "➕ Add/Edit Practice"])
    
    with tab1:
        render_practice_list(data_manager)
    
    with tab2:
        render_practice_form(data_manager)


def render_practice_list(data_manager: DataManager):
    """Render list of practices with edit/delete options."""
    practices = data_manager.get_practices()
    
    if not practices:
        st.info("No practices found. Add your first practice using the 'Add/Edit Practice' tab.")
        return
    
    st.subheader(f"Total Practices: {len(practices)}")
    
    # Sort practices by date (most recent first)
    try:
        practices.sort(key=lambda p: datetime.strptime(p.date, "%d-%m-%Y"), reverse=True)
    except:
        pass  # If date parsing fails, keep original order
    
    # Display practices
    for practice in practices:
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**📅 {practice.date}**")
                st.caption(f"📍 Location: {practice.location}")
                
                # Show number of touches for this practice
                touches = data_manager.get_touches(practice.id)
                st.caption(f"🎯 {len(touches)} touch(es)")
            
            with col2:
                if st.button("✏️ Edit", key=f"edit_practice_{practice.id}"):
                    st.session_state.editing_practice = practice.id
                    st.rerun()
            
            with col3:
                if st.button("🗑️ Delete", key=f"delete_practice_{practice.id}"):
                    # Check if there are associated touches
                    touches = data_manager.get_touches(practice.id)
                    if touches:
                        st.warning(f"This practice has {len(touches)} associated touch(es). They will also be deleted.")
                    data_manager.delete_practice(practice.id)
                    st.success(f"Deleted practice on {practice.date}")
                    st.rerun()
            
            st.divider()


def render_practice_form(data_manager: DataManager):
    """Render form to add or edit a practice."""
    # Check if editing
    editing_id = st.session_state.get("editing_practice", None)
    editing_practice = None
    
    if editing_id:
        editing_practice = data_manager.get_practice_by_id(editing_id)
        st.subheader("✏️ Edit Practice")
    else:
        st.subheader("➕ Add New Practice")
    
    # Form
    with st.form("practice_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Date input
            if editing_practice:
                try:
                    default_date = datetime.strptime(editing_practice.date, "%d-%m-%Y")
                except:
                    default_date = datetime.now()
            else:
                default_date = datetime.now()
            
            date_input = st.date_input(
                "Date *",
                value=default_date,
                key="practice_date"
            )
        
        with col2:
            location = st.selectbox(
                "Location *",
                options=config.LOCATIONS,
                index=config.LOCATIONS.index(editing_practice.location) if editing_practice else 0,
                key="practice_location"
            )
        
        col3, col4, col5 = st.columns([1, 1, 2])
        
        with col3:
            submit = st.form_submit_button(
                "Update Practice" if editing_practice else "Add Practice",
                type="primary"
            )
        
        with col4:
            if editing_practice:
                cancel = st.form_submit_button("Cancel")
                if cancel:
                    st.session_state.editing_practice = None
                    st.rerun()
        
        if submit:
            # Format date as DD-MM-YYYY
            formatted_date = date_input.strftime("%d-%m-%Y")
            
            if editing_practice:
                # Update existing practice
                updated_practice = Practice(
                    id=editing_practice.id,
                    date=formatted_date,
                    location=location
                )
                data_manager.update_practice(editing_practice.id, updated_practice)
                st.success(f"Updated practice on {formatted_date}")
                st.session_state.editing_practice = None
            else:
                # Add new practice
                new_practice = Practice(
                    id=str(uuid.uuid4()),
                    date=formatted_date,
                    location=location
                )
                data_manager.add_practice(new_practice)
                st.success(f"Added practice on {formatted_date}")
            
            st.rerun()
