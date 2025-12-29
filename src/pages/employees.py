"""Employee management page."""

import streamlit as st
import uuid
from src.data_manager import DataManager
from src.models import Employee
import config


def render_employees_page(data_manager: DataManager):
    """Render the employees management page."""
    st.title("👥 Employee Management")
    
    # Tabs for different actions
    tab1, tab2 = st.tabs(["📋 View Employees", "➕ Add/Edit Employee"])
    
    with tab1:
        render_employee_list(data_manager)
    
    with tab2:
        render_employee_form(data_manager)


def render_employee_list(data_manager: DataManager):
    """Render list of employees with edit/delete options."""
    employees = data_manager.get_employees()
    
    if not employees:
        st.info("No employees found. Add your first employee using the 'Add/Edit Employee' tab.")
        return
    
    st.subheader(f"Total Employees: {len(employees)}")
    
    # Display employees in a table-like format
    for emp in employees:
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**{emp.full_name()}**")
                member_status = "✓ Member" if emp.member else "✗ Non-member"
                st.caption(f"{member_status} | Resident: {emp.resident}")
            
            with col2:
                if st.button("✏️ Edit", key=f"edit_{emp.id}"):
                    st.session_state.editing_employee = emp.id
                    st.rerun()
            
            with col3:
                if st.button("🗑️ Delete", key=f"delete_{emp.id}"):
                    data_manager.delete_employee(emp.id)
                    st.success(f"Deleted {emp.full_name()}")
                    st.rerun()
            
            st.divider()


def render_employee_form(data_manager: DataManager):
    """Render form to add or edit an employee."""
    # Check if editing
    editing_id = st.session_state.get("editing_employee", None)
    editing_employee = None
    
    if editing_id:
        editing_employee = data_manager.get_employee_by_id(editing_id)
        st.subheader("✏️ Edit Employee")
    else:
        st.subheader("➕ Add New Employee")
    
    # Form
    with st.form("employee_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input(
                "First Name *",
                value=editing_employee.first_name if editing_employee else "",
                key="emp_first_name"
            )
        
        with col2:
            last_name = st.text_input(
                "Last Name *",
                value=editing_employee.last_name if editing_employee else "",
                key="emp_last_name"
            )
        
        col3, col4 = st.columns(2)
        
        with col3:
            member = st.checkbox(
                "Member",
                value=editing_employee.member if editing_employee else False,
                key="emp_member"
            )
        
        with col4:
            resident = st.selectbox(
                "Resident Type *",
                options=config.RESIDENT_TYPES,
                index=config.RESIDENT_TYPES.index(editing_employee.resident) if editing_employee else 0,
                key="emp_resident"
            )
        
        col5, col6, col7 = st.columns([1, 1, 2])
        
        with col5:
            submit = st.form_submit_button(
                "Update Employee" if editing_employee else "Add Employee",
                type="primary"
            )
        
        with col6:
            if editing_employee:
                cancel = st.form_submit_button("Cancel")
                if cancel:
                    st.session_state.editing_employee = None
                    st.rerun()
        
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
                    st.session_state.editing_employee = None
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
