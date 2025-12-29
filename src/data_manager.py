"""Data management utilities for persistent storage."""

import json
import os
from typing import Dict, List
from src.models import Employee, Practice, Touch
import config


class DataManager:
    """Manages data persistence using JSON file storage."""
    
    def __init__(self, data_file: str = config.DATA_FILE):
        """Initialize data manager with file path."""
        self.data_file = data_file
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        """Ensure data file and directory exist."""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        if not os.path.exists(self.data_file):
            self._save_data({
                "employees": [],
                "practices": [],
                "touches": [],
                "methods": []  # List of workshop method names
            })
    
    def _load_data(self) -> Dict:
        """Load data from JSON file."""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "employees": [],
                "practices": [],
                "touches": [],
                "methods": []
            }
    
    def _save_data(self, data: Dict):
        """Save data to JSON file."""
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    # Employee methods
    def get_employees(self) -> List[Employee]:
        """Get all employees."""
        data = self._load_data()
        return [Employee(**emp) for emp in data.get("employees", [])]
    
    def add_employee(self, employee: Employee):
        """Add a new employee."""
        data = self._load_data()
        data["employees"].append(employee.to_dict())
        self._save_data(data)
    
    def update_employee(self, employee_id: str, employee: Employee):
        """Update an existing employee."""
        data = self._load_data()
        for i, emp in enumerate(data["employees"]):
            if emp["id"] == employee_id:
                data["employees"][i] = employee.to_dict()
                break
        self._save_data(data)
    
    def delete_employee(self, employee_id: str):
        """Delete an employee."""
        data = self._load_data()
        data["employees"] = [emp for emp in data["employees"] if emp["id"] != employee_id]
        self._save_data(data)
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Employee]:
        """Get employee by ID."""
        employees = self.get_employees()
        for emp in employees:
            if emp.id == employee_id:
                return emp
        return None
    
    # Practice methods
    def get_practices(self) -> List[Practice]:
        """Get all practices."""
        data = self._load_data()
        return [Practice(**prac) for prac in data.get("practices", [])]
    
    def add_practice(self, practice: Practice):
        """Add a new practice."""
        data = self._load_data()
        data["practices"].append(practice.to_dict())
        self._save_data(data)
    
    def update_practice(self, practice_id: str, practice: Practice):
        """Update an existing practice."""
        data = self._load_data()
        for i, prac in enumerate(data["practices"]):
            if prac["id"] == practice_id:
                data["practices"][i] = practice.to_dict()
                break
        self._save_data(data)
    
    def delete_practice(self, practice_id: str):
        """Delete a practice and associated touches."""
        data = self._load_data()
        data["practices"] = [prac for prac in data["practices"] if prac["id"] != practice_id]
        # Also delete associated touches
        data["touches"] = [touch for touch in data["touches"] if touch["practice_id"] != practice_id]
        self._save_data(data)
    
    def get_practice_by_id(self, practice_id: str) -> Optional[Practice]:
        """Get practice by ID."""
        practices = self.get_practices()
        for prac in practices:
            if prac.id == practice_id:
                return prac
        return None
    
    # Touch methods
    def get_touches(self, practice_id: Optional[str] = None) -> List[Touch]:
        """Get all touches, optionally filtered by practice."""
        data = self._load_data()
        touches = [Touch(**touch) for touch in data.get("touches", [])]
        if practice_id:
            touches = [touch for touch in touches if touch.practice_id == practice_id]
        return touches
    
    def add_touch(self, touch: Touch):
        """Add a new touch."""
        data = self._load_data()
        data["touches"].append(touch.to_dict())
        self._save_data(data)
    
    def update_touch(self, touch_id: str, touch: Touch):
        """Update an existing touch."""
        data = self._load_data()
        for i, tch in enumerate(data["touches"]):
            if tch["id"] == touch_id:
                data["touches"][i] = touch.to_dict()
                break
        self._save_data(data)
    
    def delete_touch(self, touch_id: str):
        """Delete a touch."""
        data = self._load_data()
        data["touches"] = [touch for touch in data["touches"] if touch["id"] != touch_id]
        self._save_data(data)
    
    def get_touch_by_id(self, touch_id: str) -> Optional[Touch]:
        """Get touch by ID."""
        touches = self.get_touches()
        for touch in touches:
            if touch.id == touch_id:
                return touch
        return None
    
    # Method methods
    def get_methods(self) -> List[str]:
        """Get all workshop methods."""
        data = self._load_data()
        return data.get("methods", [])
    
    def add_method(self, method: str):
        """Add a new method."""
        data = self._load_data()
        if "methods" not in data:
            data["methods"] = []
        if method and method not in data["methods"]:
            data["methods"].append(method)
            self._save_data(data)
    
    def delete_method(self, method: str):
        """Delete a method."""
        data = self._load_data()
        if "methods" in data and method in data["methods"]:
            data["methods"].remove(method)
            self._save_data(data)


# Import Optional at the top
from typing import Optional
