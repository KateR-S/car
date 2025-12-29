"""Touch (workshop) management page."""

import streamlit as st
import uuid
from src.data_manager import DataManager
from src.models import Touch
import config


def render_touches_page(data_manager: DataManager):
    """Render the touches management page."""
    st.title("🎯 Touch Management")
    
    # Tabs for different actions
    tab1, tab2 = st.tabs(["📋 View Touches", "➕ Add/Edit Touch"])
    
    with tab1:
        render_touch_list(data_manager)
    
    with tab2:
        render_touch_form(data_manager)


def render_touch_list(data_manager: DataManager):
    """Render list of touches with edit/delete options."""
    touches = data_manager.get_touches()
    practices = {p.id: p for p in data_manager.get_practices()}
    employees = {e.id: e for e in data_manager.get_employees()}
    
    if not touches:
        st.info("No touches found. Add your first touch using the 'Add/Edit Touch' tab.")
        return
    
    st.subheader(f"Total Touches: {len(touches)}")
    
    # Group by practice
    touches_by_practice = {}
    for touch in touches:
        if touch.practice_id not in touches_by_practice:
            touches_by_practice[touch.practice_id] = []
        touches_by_practice[touch.practice_id].append(touch)
    
    # Display touches grouped by practice
    for practice_id, practice_touches in touches_by_practice.items():
        practice = practices.get(practice_id)
        if practice:
            st.markdown(f"### 📅 Practice: {practice.date} - {practice.location}")
        else:
            st.markdown(f"### 📅 Practice: (Unknown)")
        
        for touch in practice_touches:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**🎯 {touch.method}**")
                    
                    # Show conductor
                    conductor = employees.get(touch.conductor_id) if touch.conductor_id else None
                    conductor_name = conductor.full_name() if conductor else "Not assigned"
                    st.caption(f"🎼 Conductor: {conductor_name}")
                    
                    # Count filled bells
                    filled_bells = sum(1 for bell in touch.bells if bell is not None)
                    st.caption(f"🔔 Bells filled: {filled_bells}/{config.MAX_BELLS}")
                
                with col2:
                    if st.button("✏️ Edit", key=f"edit_touch_{touch.id}"):
                        st.session_state.editing_touch = touch.id
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_touch_{touch.id}"):
                        data_manager.delete_touch(touch.id)
                        st.success(f"Deleted touch: {touch.method}")
                        st.rerun()
                
                # Expandable section to show all bells
                with st.expander("View Bell Assignments"):
                    cols = st.columns(3)
                    for i, bell_id in enumerate(touch.bells):
                        col_idx = i % 3
                        with cols[col_idx]:
                            emp = employees.get(bell_id) if bell_id else None
                            emp_name = emp.full_name() if emp else "Empty"
                            st.text(f"Bell {i+1}: {emp_name}")
                
                st.divider()
        
        st.markdown("---")


def render_touch_form(data_manager: DataManager):
    """Render form to add or edit a touch."""
    # Get employees and practices
    employees = data_manager.get_employees()
    practices = data_manager.get_practices()
    methods = data_manager.get_methods()
    
    if not practices:
        st.warning("⚠️ Please create at least one practice before adding touches.")
        return
    
    if not employees:
        st.warning("⚠️ Please add employees before creating touches.")
        return
    
    # Check if editing
    editing_id = st.session_state.get("editing_touch", None)
    editing_touch = None
    
    if editing_id:
        editing_touch = data_manager.get_touch_by_id(editing_id)
        st.subheader("✏️ Edit Touch")
    else:
        st.subheader("➕ Add New Touch")
    
    # Prepare employee options for dropdown
    employee_options = [""] + [f"{e.full_name()} (ID: {e.id[:8]})" for e in employees]
    employee_map = {"": None}
    for e in employees:
        employee_map[f"{e.full_name()} (ID: {e.id[:8]})"] = e.id
    
    # Form
    with st.form("touch_form", clear_on_submit=True):
        # Practice selection
        practice_options = [f"{p.date} - {p.location} (ID: {p.id[:8]})" for p in practices]
        practice_map = {}
        for p in practices:
            practice_map[f"{p.date} - {p.location} (ID: {p.id[:8]})"] = p.id
        
        if editing_touch:
            # Find the index of the current practice
            current_practice_str = None
            for key, val in practice_map.items():
                if val == editing_touch.practice_id:
                    current_practice_str = key
                    break
            practice_index = practice_options.index(current_practice_str) if current_practice_str else 0
        else:
            practice_index = 0
        
        selected_practice = st.selectbox(
            "Practice *",
            options=practice_options,
            index=practice_index,
            key="touch_practice"
        )
        practice_id = practice_map[selected_practice]
        
        # Method input with dropdown and new option
        st.markdown("**Method (Workshop Name) ***")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Add "New Method" option
            method_options = ["-- Select Method --"] + methods + ["➕ Add New Method"]
            
            if editing_touch and editing_touch.method in methods:
                method_index = methods.index(editing_touch.method) + 1
            else:
                method_index = 0
            
            selected_method_option = st.selectbox(
                "Select existing method",
                options=method_options,
                index=method_index,
                key="touch_method_select",
                label_visibility="collapsed"
            )
        
        with col2:
            pass
        
        # If "Add New Method" is selected, show text input
        method_name = ""
        if selected_method_option == "➕ Add New Method":
            method_name = st.text_input(
                "Enter new method name",
                value=editing_touch.method if editing_touch and editing_touch.method not in methods else "",
                key="touch_method_new"
            )
        elif selected_method_option != "-- Select Method --":
            method_name = selected_method_option
        elif editing_touch:
            method_name = editing_touch.method
        
        # Conductor selection
        st.markdown("**Conductor (Facilitator) ***")
        if editing_touch and editing_touch.conductor_id:
            conductor_emp = next((e for e in employees if e.id == editing_touch.conductor_id), None)
            conductor_str = f"{conductor_emp.full_name()} (ID: {conductor_emp.id[:8]})" if conductor_emp else ""
            conductor_index = employee_options.index(conductor_str) if conductor_str in employee_options else 0
        else:
            conductor_index = 0
        
        conductor_selection = st.selectbox(
            "Select conductor",
            options=employee_options,
            index=conductor_index,
            key="touch_conductor",
            label_visibility="collapsed"
        )
        conductor_id = employee_map[conductor_selection]
        
        # Bell assignments
        st.markdown("**Bell Assignments (12 slots)**")
        st.caption("Assign employees to each bell slot. Leave empty for unassigned slots.")
        
        # Create 12 bell selections in a grid
        bells = []
        cols_per_row = 3
        for row in range(4):  # 4 rows × 3 columns = 12 bells
            cols = st.columns(cols_per_row)
            for col_idx in range(cols_per_row):
                bell_num = row * cols_per_row + col_idx
                if bell_num < config.MAX_BELLS:
                    with cols[col_idx]:
                        # Get current value
                        if editing_touch and bell_num < len(editing_touch.bells):
                            current_bell_id = editing_touch.bells[bell_num]
                            if current_bell_id:
                                bell_emp = next((e for e in employees if e.id == current_bell_id), None)
                                bell_str = f"{bell_emp.full_name()} (ID: {bell_emp.id[:8]})" if bell_emp else ""
                                bell_index = employee_options.index(bell_str) if bell_str in employee_options else 0
                            else:
                                bell_index = 0
                        else:
                            bell_index = 0
                        
                        bell_selection = st.selectbox(
                            f"Bell {bell_num + 1}",
                            options=employee_options,
                            index=bell_index,
                            key=f"bell_{bell_num}"
                        )
                        bells.append(employee_map[bell_selection])
        
        # Submit buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submit = st.form_submit_button(
                "Update Touch" if editing_touch else "Add Touch",
                type="primary"
            )
        
        with col2:
            if editing_touch:
                cancel = st.form_submit_button("Cancel")
                if cancel:
                    st.session_state.editing_touch = None
                    st.rerun()
        
        if submit:
            if not method_name:
                st.error("Please select or enter a method name.")
            elif not conductor_id:
                st.error("Please select a conductor.")
            else:
                # Add method to list if it's new
                if method_name not in methods:
                    data_manager.add_method(method_name)
                
                if editing_touch:
                    # Update existing touch
                    updated_touch = Touch(
                        id=editing_touch.id,
                        practice_id=practice_id,
                        method=method_name,
                        conductor_id=conductor_id,
                        bells=bells
                    )
                    data_manager.update_touch(editing_touch.id, updated_touch)
                    st.success(f"Updated touch: {method_name}")
                    st.session_state.editing_touch = None
                else:
                    # Add new touch
                    new_touch = Touch(
                        id=str(uuid.uuid4()),
                        practice_id=practice_id,
                        method=method_name,
                        conductor_id=conductor_id,
                        bells=bells
                    )
                    data_manager.add_touch(new_touch)
                    st.success(f"Added touch: {method_name}")
                
                st.rerun()
