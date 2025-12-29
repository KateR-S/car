"""Method management page."""

import streamlit as st
import uuid
from src.data_manager import DataManager
from src.models import Method


def render_methods_page(data_manager: DataManager):
    """Render the methods management page."""
    st.title("📚 Method Management")
    
    # Add method button in popover
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        with st.popover("➕ Add Method", use_container_width=True):
            render_method_form(data_manager, None)
    
    # Display method list
    render_method_list(data_manager)


def render_method_list(data_manager: DataManager):
    """Render list of methods with edit/delete options."""
    methods = data_manager.get_methods()
    
    if not methods:
        st.info("No methods found. Click 'Add Method' above to add your first method.")
        return
    
    st.subheader(f"Total Methods: {len(methods)}")
    
    # Display methods in a table-like format
    for method in methods:
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**{method.name}**")
                st.caption(f"Code: {method.code}")
            
            with col2:
                # Edit button in popover
                with st.popover("✏️ Edit", use_container_width=True):
                    render_method_form(data_manager, method)
            
            with col3:
                if st.button("🗑️ Delete", key=f"delete_{method.id}"):
                    data_manager.delete_method(method.id)
                    st.success(f"Deleted {method.name}")
                    st.rerun()
            
            st.divider()


def render_method_form(data_manager: DataManager, editing_method: Method = None):
    """Render form to add or edit a method.
    
    Args:
        data_manager: The data manager instance
        editing_method: Method object if editing, None if adding new
    """
    if editing_method:
        st.subheader("✏️ Edit Method")
    else:
        st.subheader("➕ Add New Method")
    
    # Generate unique form key
    form_key = f"method_form_{editing_method.id if editing_method else 'new'}"
    
    # Form
    with st.form(form_key, clear_on_submit=True):
        name = st.text_input(
            "Method Name *",
            value=editing_method.name if editing_method else "",
            key=f"method_name_{editing_method.id if editing_method else 'new'}",
            help="The name of the workshop method"
        )
        
        code = st.text_input(
            "Method Code *",
            value=editing_method.code if editing_method else "",
            key=f"method_code_{editing_method.id if editing_method else 'new'}",
            help="A short code or identifier for the method"
        )
        
        submit = st.form_submit_button(
            "Update Method" if editing_method else "Add Method",
            type="primary",
            use_container_width=True
        )
        
        if submit:
            if not name or not code:
                st.error("Please fill in all required fields (*)")
            else:
                if editing_method:
                    # Update existing method
                    updated_method = Method(
                        id=editing_method.id,
                        name=name.strip(),
                        code=code.strip()
                    )
                    data_manager.update_method(editing_method.id, updated_method)
                    st.success(f"Updated {updated_method.name}")
                else:
                    # Add new method
                    new_method = Method(
                        id=str(uuid.uuid4()),
                        name=name.strip(),
                        code=code.strip()
                    )
                    data_manager.add_method(new_method)
                    st.success(f"Added {new_method.name}")
                
                st.rerun()
