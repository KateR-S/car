"""Touch (workshop) management page."""

import streamlit as st
import uuid
import logging
from src.data_manager import (
    DataManager, 
    get_cached_touches,
    get_cached_touches_by_date,
    get_cached_practices,
    get_cached_employees,
    get_cached_methods,
    invalidate_data_cache
)
from src.models import Touch
import config

logger = logging.getLogger(__name__)


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
    logger.debug("Rendering touch list")
    
    # Add touch button at the top
    if st.button("➕ Add Touch", type="primary", use_container_width=False):
        st.session_state.editing_touch_id = None
        st.session_state.touch_tab = 1  # Switch to Add/Edit tab
        st.rerun()
    
    st.markdown("---")
    
    # Date filter section
    st.subheader("Filter by Date")
    
    # Get unique dates from practices
    logger.debug("Fetching practices for date filter")
    practices = get_cached_practices(data_manager)
    
    # Create a list of dates and map to sortable format
    date_options = []
    date_map = {}  # Maps display format to DD-MM-YYYY format
    
    for practice in practices:
        date_str = practice.date  # DD-MM-YYYY format
        if date_str not in date_map.values():
            # Convert to sortable format for ordering
            date_parts = date_str.split('-')
            if len(date_parts) == 3:
                sortable_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"  # YYYY-MM-DD
                date_map[sortable_date] = date_str
    
    # Sort dates in descending order (most recent first)
    sorted_dates = sorted(date_map.keys(), reverse=True)
    date_options = [date_map[sd] for sd in sorted_dates]
    
    if not date_options:
        st.info("No practices found. Please create a practice first.")
        return
    
    # Initialize session state for date filter - default to latest date in database
    if 'touch_filter_date' not in st.session_state:
        # Default to the latest date (first in sorted list)
        st.session_state.touch_filter_date = date_options[0]
    
    # Find the index of the current filter date, or default to latest date
    selected_index = 0
    if st.session_state.touch_filter_date in date_options:
        selected_index = date_options.index(st.session_state.touch_filter_date)
    else:
        # If current date is not in options (e.g., practice was deleted), reset to latest
        st.session_state.touch_filter_date = date_options[0]
        selected_index = 0
    
    # Date filter dropdown
    selected_date = st.selectbox(
        "Select Date",
        options=date_options,
        index=selected_index,
        key="date_filter_dropdown"
    )
    
    # Update session state if date changed
    if selected_date != st.session_state.touch_filter_date:
        st.session_state.touch_filter_date = selected_date
        st.rerun()
    
    st.markdown("---")
    
    logger.debug(f"Fetching touches for date: {selected_date}")
    touches = get_cached_touches_by_date(data_manager, selected_date)
    practices_dict = {p.id: p for p in practices}
    employees = {e.id: e for e in get_cached_employees(data_manager)}
    methods = {m.id: m for m in get_cached_methods(data_manager)}
    
    if not touches:
        st.info(f"No touches found for {selected_date}. Click 'Add Touch' above to add a touch for this date.")
        return
    
    st.subheader(f"Touches for {selected_date}: {len(touches)}")
    
    # Group by practice for display
    touches_by_practice = {}
    for touch in touches:
        practice = practices_dict.get(touch.practice_id)
        if practice:
            if touch.practice_id not in touches_by_practice:
                touches_by_practice[touch.practice_id] = (practice, [])
            touches_by_practice[touch.practice_id][1].append(touch)
    
    # Sort touches within each practice by touch_number
    for practice_id in touches_by_practice:
        practice, practice_touches = touches_by_practice[practice_id]
        practice_touches.sort(key=lambda t: t.touch_number)
        touches_by_practice[practice_id] = (practice, practice_touches)
    
    # Display touches grouped by practice
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
                    st.markdown(f"**Touch #{touch.touch_number}: {method_name}**")
                    
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
                        logger.info(f"Deleting touch: {touch.id}")
                        data_manager.delete_touch(touch.id)
                        invalidate_data_cache()  # Invalidate cache after deletion
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
    logger.debug("Rendering touch form")
    practices = get_cached_practices(data_manager)
    employees = get_cached_employees(data_manager)
    methods = get_cached_methods(data_manager)
    
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
        
        # Touch number input (auto-suggested but editable)
        if editing_touch:
            suggested_number = editing_touch.touch_number
        else:
            suggested_number = data_manager.get_next_touch_number(practice_id)
        
        touch_number = st.number_input(
            "Touch Number *",
            min_value=1,
            max_value=config.MAX_TOUCHES_PER_PRACTICE,
            value=suggested_number,
            step=1,
            key=f"touch_number_{editing_touch.id if editing_touch else 'new'}",
            help=f"Touch order number (1 to {config.MAX_TOUCHES_PER_PRACTICE}). Must be unique per practice."
        )
        
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
        st.caption("Assign ringers to each bell and check the conductor checkbox in the row of the conductor. Only one conductor can be selected.")
        
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
                # Checkbox for conductor selection
                # Note: Checkboxes are used instead of radio buttons because:
                # 1. The requirement specifies "checkbox" in the conductor column
                # 2. Radio buttons would require a different UI layout (single group)
                # 3. In a form, both checkboxes and radio buttons are submitted together,
                #    so neither can provide dynamic mutual exclusion during user interaction
                # 4. We validate on submit to ensure only one conductor is selected
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
            # Find which conductor checkboxes are checked
            checked_conductors = []
            for i in range(12):
                checkbox_key = f"conductor_{i}_{editing_touch.id if editing_touch else 'new'}"
                if st.session_state.get(checkbox_key, False):
                    checked_conductors.append(i)
            
            # Validate conductor selection
            if len(checked_conductors) == 0:
                st.error("Please select a conductor by checking one of the conductor checkboxes")
            elif len(checked_conductors) > 1:
                st.error(f"Please select only ONE conductor. You have selected {len(checked_conductors)} conductors (bells: {', '.join(str(c+1) for c in checked_conductors)})")
            elif bell_assignments[checked_conductors[0]] is None:
                st.error(f"Please assign a ringer to Bell {checked_conductors[0] + 1} (the selected conductor bell)")
            else:
                conductor_bell_index = checked_conductors[0]
                conductor_id = bell_assignments[conductor_bell_index]
                
                # Validate touch_number uniqueness
                existing_touches = data_manager.get_touches(practice_id)
                touch_numbers_in_use = {t.touch_number for t in existing_touches if t.id != (editing_touch.id if editing_touch else None)}
                
                if touch_number in touch_numbers_in_use:
                    st.error(f"Touch number {touch_number} is already used in this practice. Please choose a different number.")
                else:
                    if editing_touch:
                        # Update existing touch
                        logger.info(f"Updating touch: {editing_touch.id}")
                        updated_touch = Touch(
                            id=editing_touch.id,
                            practice_id=practice_id,
                            method_id=method_id,
                            touch_number=touch_number,
                            conductor_id=conductor_id,
                            bells=bell_assignments
                        )
                        data_manager.update_touch(editing_touch.id, updated_touch)
                        invalidate_data_cache()  # Invalidate cache after update
                        st.success("Touch updated successfully!")
                    else:
                        # Add new touch
                        logger.info("Adding new touch")
                        new_touch = Touch(
                            id=str(uuid.uuid4()),
                            practice_id=practice_id,
                            method_id=method_id,
                            touch_number=touch_number,
                            conductor_id=conductor_id,
                            bells=bell_assignments
                        )
                        data_manager.add_touch(new_touch)
                        invalidate_data_cache()  # Invalidate cache after addition
                        st.success("Touch added successfully!")
                    
                    # Reset editing state and return to list tab
                    st.session_state.editing_touch_id = None
                    st.session_state.touch_tab = 0  # Return to list tab
                    st.rerun()
