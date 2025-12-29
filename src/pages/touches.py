"""Touch (workshop) management page."""

import streamlit as st
import uuid
from src.data_manager import DataManager
from src.models import Touch
import config


def render_touches_page(data_manager: DataManager):
    """Render the touches management page."""
    st.title("Touch Management")
    
    # Initialize session state for tab management
    if 'touch_tab' not in st.session_state:
        st.session_state.touch_tab = 0  # 0 = List, 1 = Add/Edit
    if 'editing_touch_id' not in st.session_state:
        st.session_state.editing_touch_id = None
    
    # Create custom tab buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 List Touches", 
                     type="primary" if st.session_state.touch_tab == 0 else "secondary",
                     use_container_width=True):
            st.session_state.touch_tab = 0
            st.rerun()
    
    with col2:
        if st.button("➕ Add/Edit Touch",
                     type="primary" if st.session_state.touch_tab == 1 else "secondary",
                     use_container_width=True):
            st.session_state.touch_tab = 1
            st.rerun()
    
    st.markdown("---")
    
    # Render the appropriate view based on selected tab
    if st.session_state.touch_tab == 0:
        render_touch_list(data_manager)
    else:
        editing_touch = None
        if st.session_state.editing_touch_id:
            editing_touch = data_manager.get_touch_by_id(st.session_state.editing_touch_id)
        render_touch_form(data_manager, editing_touch)


def render_touch_list(data_manager: DataManager):
    """Render list of touches with edit/delete options."""
    # Add touch button at the top
    if st.button("➕ Add Touch", type="primary", use_container_width=False):
        st.session_state.editing_touch_id = None
        st.session_state.touch_tab = 1  # Switch to Add/Edit tab
        st.rerun()
    
    st.markdown("---")
    
    touches = data_manager.get_touches()
    practices = {p.id: p for p in data_manager.get_practices()}
    employees = {e.id: e for e in data_manager.get_employees()}
    methods = {m.id: m for m in data_manager.get_methods()}
    
    if not touches:
        st.info("No touches found. Click 'Add Touch' above to add your first touch.")
        return
    
    st.subheader(f"Total Touches: {len(touches)}")
    
    # Sort touches by practice date (descending)
    touches_with_dates = []
    for touch in touches:
        practice = practices.get(touch.practice_id)
        if practice:
            # Convert date string (DD-MM-YYYY) to sortable format
            date_parts = practice.date.split('-')
            if len(date_parts) == 3:
                sortable_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"  # YYYY-MM-DD
                touches_with_dates.append((touch, sortable_date, practice))
    
    # Sort by date descending
    touches_with_dates.sort(key=lambda x: x[1], reverse=True)
    
    # Group by practice for display
    touches_by_practice = {}
    for touch, sortable_date, practice in touches_with_dates:
        practice_id = touch.practice_id
        if practice_id not in touches_by_practice:
            touches_by_practice[practice_id] = (practice, [])
        touches_by_practice[practice_id][1].append(touch)
    
    # Display touches grouped by practice (already sorted by date)
    for practice_id, (practice, practice_touches) in touches_by_practice.items():
        if practice:
            st.markdown(f"### 📅 Practice: {practice.date} - {practice.location}")
        else:
            st.markdown(f"### 📅 Practice: (Unknown)")
        
        for touch in practice_touches:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    method = methods.get(touch.method_id)
                    method_name = method.name if method else "(Unknown Method)"
                    st.markdown(f"**🎯 {method_name}**")
                    
                    conductor = employees.get(touch.conductor_id) if touch.conductor_id else None
                    if conductor:
                        st.caption(f"👨‍🏫 Conductor: {conductor.full_name()}")
                    
                    # Count filled bells
                    filled_bells = sum(1 for bell_id in touch.bells if bell_id)
                    st.caption(f"🔔 {filled_bells}/12 bells filled")
                
                with col2:
                    # Edit button that switches to edit tab
                    if st.button("✏️ Edit", key=f"edit_touch_{touch.id}", use_container_width=True):
                        st.session_state.editing_touch_id = touch.id
                        st.session_state.touch_tab = 1  # Switch to Add/Edit tab
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_touch_{touch.id}"):
                        method = methods.get(touch.method_id)
                        method_name = method.name if method else "touch"
                        data_manager.delete_touch(touch.id)
                        st.success(f"Deleted touch: {method_name}")
                        st.rerun()
                
                # Expandable section to show all bells
                with st.expander("View Bell Assignments"):
                    cols = st.columns(3)
                    for i, bell_id in enumerate(touch.bells):
                        col = cols[i % 3]
                        with col:
                            employee = employees.get(bell_id) if bell_id else None
                            if employee:
                                st.markdown(f"**Bell {i+1}:** {employee.full_name()}")
                            else:
                                st.markdown(f"**Bell {i+1}:** *(Empty)*")
                
                st.divider()


def render_touch_form(data_manager: DataManager, editing_touch: Touch = None):
    """Render form to add or edit a touch with table layout.
    
    Args:
        data_manager: The data manager instance
        editing_touch: Touch object if editing, None if adding new
    """
    practices = data_manager.get_practices()
    employees = data_manager.get_employees()
    methods = data_manager.get_methods()
    
    if not practices:
        st.warning("⚠️ Please create at least one practice before adding touches.")
        return
    
    if not employees:
        st.warning("⚠️ Please add ringers before creating touches.")
        return
    
    if not methods:
        st.warning("⚠️ Please create at least one method before adding touches. Go to the Methods page to add methods.")
        return
    
    if editing_touch:
        st.subheader("✏️ Edit Touch")
    else:
        st.subheader("➕ Add New Touch")
    
    # Generate unique form key
    form_key = f"touch_form_{editing_touch.id if editing_touch else 'new'}"
    
    # Prepare employee options for dropdown
    employee_options = [""] + [f"{e.full_name()}" for e in employees]
    employee_id_map = {"": None}
    for e in employees:
        employee_id_map[f"{e.full_name()}"] = e.id
    
    # Form
    with st.form(form_key, clear_on_submit=True):
        # Practice selection
        practice_options = [f"{p.date} - {p.location}" for p in practices]
        practice_id_map = {}
        for p in practices:
            practice_id_map[f"{p.date} - {p.location}"] = p.id
        
        if editing_touch:
            # Find the index of the current practice
            current_practice_str = None
            for key, val in practice_id_map.items():
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
            key=f"touch_practice_{editing_touch.id if editing_touch else 'new'}"
        )
        practice_id = practice_id_map[selected_practice]
        
        # Method selection
        method_options = [f"{m.name} ({m.code})" for m in methods]
        method_id_map = {}
        for m in methods:
            method_id_map[f"{m.name} ({m.code})"] = m.id
        
        if editing_touch:
            current_method_str = None
            for key, val in method_id_map.items():
                if val == editing_touch.method_id:
                    current_method_str = key
                    break
            method_index = method_options.index(current_method_str) if current_method_str else 0
        else:
            method_index = 0
        
        selected_method = st.selectbox(
            "Method *",
            options=method_options,
            index=method_index,
            key=f"touch_method_{editing_touch.id if editing_touch else 'new'}",
            help="To add a new method, go to the methods page."
        )
        method_id = method_id_map[selected_method]
        
        st.markdown("---")
        st.markdown("**Bell Assignments** (12 bells)")
        st.caption("Assign ringers to each bell and check the conductor checkbox in the row of the conductor")
        
        # Create table header
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            st.markdown("**Bell**")
        with col2:
            st.markdown("**Ringer**")
        with col3:
            st.markdown("**Conductor**")
        
        st.markdown("---")
        
        # Determine current conductor bell if editing
        conductor_bell_index = None
        if editing_touch and editing_touch.conductor_id:
            for i, bell_id in enumerate(editing_touch.bells):
                if bell_id == editing_touch.conductor_id:
                    conductor_bell_index = i
                    break
        
        # Bell assignments
        bell_assignments = []
        for i in range(12):
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                st.markdown(f"**{i+1}**")
            
            with col2:
                if editing_touch and i < len(editing_touch.bells) and editing_touch.bells[i]:
                    bell_emp = next((e for e in employees if e.id == editing_touch.bells[i]), None)
                    bell_str = f"{bell_emp.full_name()}" if bell_emp else ""
                    bell_index = employee_options.index(bell_str) if bell_str in employee_options else 0
                else:
                    bell_index = 0
                
                bell_selection = st.selectbox(
                    f"Bell {i+1}",
                    options=employee_options,
                    index=bell_index,
                    key=f"bell_{i}_{editing_touch.id if editing_touch else 'new'}",
                    label_visibility="collapsed"
                )
                bell_assignments.append(employee_id_map[bell_selection])
            
            with col3:
                # Radio button functionality using checkboxes
                # We'll use the value to track which one is checked
                is_checked = (conductor_bell_index == i)
                st.checkbox(
                    f"Conductor {i+1}",
                    value=is_checked,
                    key=f"conductor_{i}_{editing_touch.id if editing_touch else 'new'}",
                    label_visibility="collapsed"
                )
        
        st.markdown("---")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            submit = st.form_submit_button(
                "💾 Save Touch" if editing_touch else "➕ Add Touch",
                type="primary",
                use_container_width=True
            )
        with col2:
            cancel = st.form_submit_button(
                "❌ Cancel",
                use_container_width=True
            )
        
        if cancel:
            st.session_state.editing_touch_id = None
            st.session_state.touch_tab = 0  # Return to list tab
            st.rerun()
        
        if submit:
            # Find which conductor checkbox is checked
            conductor_bell_index = None
            for i in range(12):
                checkbox_key = f"conductor_{i}_{editing_touch.id if editing_touch else 'new'}"
                if st.session_state.get(checkbox_key, False):
                    conductor_bell_index = i
                    break
            
            # Validate that conductor bell has a ringer assigned
            if conductor_bell_index is None:
                st.error("Please select a conductor by checking one of the conductor checkboxes")
            elif bell_assignments[conductor_bell_index] is None:
                st.error(f"Please assign a ringer to Bell {conductor_bell_index + 1} (the selected conductor bell)")
            else:
                conductor_id = bell_assignments[conductor_bell_index]
                
                if editing_touch:
                    # Update existing touch
                    updated_touch = Touch(
                        id=editing_touch.id,
                        practice_id=practice_id,
                        method_id=method_id,
                        conductor_id=conductor_id,
                        bells=bell_assignments
                    )
                    data_manager.update_touch(editing_touch.id, updated_touch)
                    st.success("Touch updated successfully!")
                else:
                    # Add new touch
                    new_touch = Touch(
                        id=str(uuid.uuid4()),
                        practice_id=practice_id,
                        method_id=method_id,
                        conductor_id=conductor_id,
                        bells=bell_assignments
                    )
                    data_manager.add_touch(new_touch)
                    st.success("Touch added successfully!")
                
                # Reset editing state and return to list tab
                st.session_state.editing_touch_id = None
                st.session_state.touch_tab = 0  # Return to list tab
                st.rerun()
