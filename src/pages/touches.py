"""Touch (workshop) management page."""

import streamlit as st
import uuid
from src.data_manager import DataManager
from src.models import Touch
import config


def render_touches_page(data_manager: DataManager):
    """Render the touches management page."""
    st.title("🎯 Touch Management")
    
    # Add touch button in popover
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        with st.popover("➕ Add Touch", use_container_width=True):
            render_touch_form(data_manager, None)
    
    # Display touch list
    render_touch_list(data_manager)


def render_touch_list(data_manager: DataManager):
    """Render list of touches with edit/delete options."""
    touches = data_manager.get_touches()
    practices = {p.id: p for p in data_manager.get_practices()}
    employees = {e.id: e for e in data_manager.get_employees()}
    methods = {m.id: m for m in data_manager.get_methods()}
    
    if not touches:
        st.info("No touches found. Click 'Add Touch' above to add your first touch.")
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
                    # Edit button in popover
                    with st.popover("✏️ Edit", use_container_width=True):
                        render_touch_form(data_manager, touch)
                
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
    """Render form to add or edit a touch.
    
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
        st.warning("⚠️ Please add employees before creating touches.")
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
            help="Select the workshop method. Go to Methods page to add new methods."
        )
        method_id = method_id_map[selected_method]
        
        # Conductor selection
        if editing_touch and editing_touch.conductor_id:
            conductor_emp = next((e for e in employees if e.id == editing_touch.conductor_id), None)
            conductor_str = f"{conductor_emp.full_name()}" if conductor_emp else ""
            conductor_index = employee_options.index(conductor_str) if conductor_str in employee_options else 0
        else:
            conductor_index = 0
        
        conductor_selection = st.selectbox(
            "Conductor (Facilitator) *",
            options=employee_options,
            index=conductor_index,
            key=f"touch_conductor_{editing_touch.id if editing_touch else 'new'}"
        )
        conductor_id = employee_id_map[conductor_selection]
        
        # Bell assignments
        st.markdown("**Bell Assignments** (12 slots)")
        st.caption("Assign employees to each bell slot")
        
        bell_assignments = []
        cols_per_row = 3
        for i in range(12):
            if i % cols_per_row == 0:
                cols = st.columns(cols_per_row)
            
            col = cols[i % cols_per_row]
            with col:
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
                    key=f"bell_{i}_{editing_touch.id if editing_touch else 'new'}"
                )
                bell_assignments.append(employee_id_map[bell_selection])
        
        submit = st.form_submit_button(
            "Update Touch" if editing_touch else "Add Touch",
            type="primary",
            use_container_width=True
        )
        
        if submit:
            if not method_id or not conductor_id:
                st.error("Please select method and conductor")
            else:
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
                    st.success("Updated touch")
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
                    st.success("Added touch")
                
                st.rerun()
