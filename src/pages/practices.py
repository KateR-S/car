"""Practice management page."""

import streamlit as st
import uuid
from datetime import datetime
from src.data_manager import DataManager
from src.models import Practice
import config


def render_practices_page(data_manager: DataManager):
    """Render the practices management page."""
    st.title("Practice Management")
    
    # Add practice button in popover
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        with st.popover("➕ Add Practice", use_container_width=True):
            render_practice_form(data_manager, None)
    
    # Display practice list
    render_practice_list(data_manager)


def render_practice_list(data_manager: DataManager):
    """Render list of practices with edit/delete options."""
    practices = data_manager.get_practices()
    
    if not practices:
        st.info("No practices found. Click 'Add Practice' above to add your first practice.")
        return
    
    st.subheader(f"Total Practices: {len(practices)}")
    
    # Sort practices by date (most recent first)
    try:
        practices.sort(key=lambda p: datetime.strptime(p.date, "%d-%m-%Y"), reverse=True)
    except (ValueError, AttributeError):
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
                # Edit button in popover
                with st.popover("✏️ Edit", use_container_width=True):
                    render_practice_form(data_manager, practice)
            
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


def render_practice_form(data_manager: DataManager, editing_practice: Practice = None):
    """Render form to add or edit a practice.
    
    Args:
        data_manager: The data manager instance
        editing_practice: Practice object if editing, None if adding new
    """
    if editing_practice:
        st.subheader("✏️ Edit Practice")
    else:
        st.subheader("➕ Add New Practice")
    
    # Generate unique form key
    form_key = f"practice_form_{editing_practice.id if editing_practice else 'new'}"
    
    # Form
    with st.form(form_key, clear_on_submit=True):
        # Date input as text field
        if editing_practice:
            default_date_str = editing_practice.date
        else:
            default_date_str = datetime.now().strftime("%d-%m-%Y")
        
        date_text = st.text_input(
            "Date (DD-MM-YYYY) *",
            value=default_date_str,
            key=f"practice_date_{editing_practice.id if editing_practice else 'new'}",
            help="Enter date in DD-MM-YYYY format"
        )
        
        location = st.selectbox(
            "Location *",
            options=config.LOCATIONS,
            index=config.LOCATIONS.index(editing_practice.location) if editing_practice else 0,
            key=f"practice_location_{editing_practice.id if editing_practice else 'new'}"
        )
        
        submit = st.form_submit_button(
            "Update Practice" if editing_practice else "Add Practice",
            type="primary",
            use_container_width=True
        )
        
        if submit:
            # Validate date format
            try:
                # Parse to validate format
                parsed_date = datetime.strptime(date_text.strip(), "%d-%m-%Y")
                formatted_date = parsed_date.strftime("%d-%m-%Y")
            except ValueError:
                st.error("Invalid date format. Please use DD-MM-YYYY format (e.g., 29-12-2025)")
                return
            
            if editing_practice:
                # Update existing practice
                updated_practice = Practice(
                    id=editing_practice.id,
                    date=formatted_date,
                    location=location
                )
                data_manager.update_practice(editing_practice.id, updated_practice)
                st.success(f"Updated practice on {formatted_date}")
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
