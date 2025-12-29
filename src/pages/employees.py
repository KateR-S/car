"""Employee management page."""

import streamlit as st
import uuid
from src.data_manager import DataManager
from src.models import Employee
import config


def render_employees_page(data_manager: DataManager):
    """Render the employees management page."""
    st.title("Ringer Management")
    
    # Add employee button in popover
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        with st.popover("➕ Add Ringer", use_container_width=True):
            render_employee_form(data_manager, None)
    
    # Display employee list
    render_employee_list(data_manager)


def render_employee_list(data_manager: DataManager):
    """Render list of ringers with edit/delete options."""
    employees = data_manager.get_employees()
    
    if not employees:
        st.info("No ringers found. Click 'Add Ringer' above to add your first ringer.")
        return
    
    st.subheader(f"Total Ringers: {len(employees)}")
    
    # Display employees in a table-like format
    for emp in employees:
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**{emp.full_name()}**")
                member_status = "✓ Member" if emp.member else "✗ Non-member"
                st.caption(f"{member_status} | Resident: {emp.resident}")
            
            with col2:
                # Edit button in popover
                with st.popover("✏️ Edit", use_container_width=True):
                    render_employee_form(data_manager, emp)
            
            with col3:
                if st.button("🗑️ Delete", key=f"delete_{emp.id}"):
                    data_manager.delete_employee(emp.id)
                    st.success(f"Deleted {emp.full_name()}")
                    st.rerun()
            
            st.divider()


def render_employee_form(data_manager: DataManager, editing_employee: Employee = None):
    """Render form to add or edit a ringer.
    
    Args:
        data_manager: The data manager instance
        editing_employee: Ringer object if editing, None if adding new
    """
    if editing_employee:
        st.subheader("✏️ Edit Ringer")
    else:
        st.subheader("➕ Add New Ringer")
    
    # Generate unique form key
    form_key = f"employee_form_{editing_employee.id if editing_employee else 'new'}"
    
    # Form
    with st.form(form_key, clear_on_submit=True):
        first_name = st.text_input(
            "First Name *",
            value=editing_employee.first_name if editing_employee else "",
            key=f"emp_first_name_{editing_employee.id if editing_employee else 'new'}"
        )
        
        last_name = st.text_input(
            "Last Name *",
            value=editing_employee.last_name if editing_employee else "",
            key=f"emp_last_name_{editing_employee.id if editing_employee else 'new'}"
        )
        
        member = st.checkbox(
            "Member",
            value=editing_employee.member if editing_employee else False,
            key=f"emp_member_{editing_employee.id if editing_employee else 'new'}"
        )
        
        resident = st.selectbox(
            "Resident Type *",
            options=config.RESIDENT_TYPES,
            index=config.RESIDENT_TYPES.index(editing_employee.resident) if editing_employee else 0,
            key=f"emp_resident_{editing_employee.id if editing_employee else 'new'}"
        )
        
        submit = st.form_submit_button(
            "Update Ringer" if editing_employee else "Add Ringer",
            type="primary",
            use_container_width=True
        )
        
        if submit:
            if not first_name or not last_name:
                st.error("Please fill in all required fields (*)")
            else:
                if editing_employee:
                    # Update existing employee
                    updated_employee = Employee(
                        id=editing_employee.id,
                        first_name=first_name.strip(),
                        last_name=last_name.strip(),
                        member=member,
                        resident=resident
                    )
                    data_manager.update_employee(editing_employee.id, updated_employee)
                    st.success(f"Updated {updated_employee.full_name()}")
                else:
                    # Add new employee
                    new_employee = Employee(
                        id=str(uuid.uuid4()),
                        first_name=first_name.strip(),
                        last_name=last_name.strip(),
                        member=member,
                        resident=resident
                    )
                    data_manager.add_employee(new_employee)
                    st.success(f"Added {new_employee.full_name()}")
                
                st.rerun()
