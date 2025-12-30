"""Data models for the application."""

from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime


@dataclass
class Employee:
    """Employee model."""
    id: str
    first_name: str
    last_name: str
    member: bool
    resident: str
    
    def full_name(self) -> str:
        """Return full name."""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Practice:
    """Practice (all-hands day) model."""
    id: str
    date: str  # DD-MM-YYYY format
    location: str
    
    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Method:
    """Method (workshop type) model."""
    id: str
    name: str
    code: str
    
    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Touch:
    """Touch (workshop) model."""
    id: str
    practice_id: str
    method_id: str  # Method ID (was method name)
    touch_number: int  # Touch order number (1 to MAX_TOUCHES_PER_PRACTICE), unique per practice
    conductor_id: Optional[str] = None  # Employee ID
    bells: List[Optional[str]] = field(default_factory=lambda: [None] * 12)  # Employee IDs for each bell
    
    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)
