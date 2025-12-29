"""Neon PostgreSQL database manager for persistent storage."""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional
from src.models import Employee, Practice, Touch, Method


class NeonDataManager:
    """Manages data persistence using Neon PostgreSQL database."""
    
    def __init__(self):
        """Initialize Neon data manager with connection from environment variables."""
        self.connection_string = self._build_connection_string()
        self._ensure_tables()
    
    def _build_connection_string(self) -> str:
        """Build PostgreSQL connection string from environment variables.
        
        IMPORTANT: This method uses environment variables and never logs them.
        """
        db_role = os.environ.get('DB_ROLE')
        db_pass = os.environ.get('DB_PASS')
        db_name = os.environ.get('DB_NAME')
        db_database = os.environ.get('DB_DATABASE')
        
        if not all([db_role, db_pass, db_name, db_database]):
            raise ValueError(
                "Missing required environment variables: DB_ROLE, DB_PASS, DB_NAME, DB_DATABASE. "
                "Please set these environment variables to use Neon database."
            )
        
        # Build connection string (credentials are not logged)
        return f"postgresql://{db_role}:{db_pass}@{db_name}.eu-west-2.aws.neon.tech/{db_database}?sslmode=require"
    
    def _get_connection(self):
        """Get a database connection."""
        return psycopg2.connect(self.connection_string)
    
    def _ensure_tables(self):
        """Create database tables if they don't exist."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Create employees table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS employees (
                        id VARCHAR(255) PRIMARY KEY,
                        first_name VARCHAR(255) NOT NULL,
                        last_name VARCHAR(255) NOT NULL,
                        member BOOLEAN NOT NULL,
                        resident VARCHAR(50) NOT NULL
                    )
                """)
                
                # Create practices table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS practices (
                        id VARCHAR(255) PRIMARY KEY,
                        date VARCHAR(50) NOT NULL,
                        location VARCHAR(100) NOT NULL
                    )
                """)
                
                # Create methods table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS methods (
                        id VARCHAR(255) PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        code VARCHAR(100) NOT NULL
                    )
                """)
                
                # Create touches table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS touches (
                        id VARCHAR(255) PRIMARY KEY,
                        practice_id VARCHAR(255) NOT NULL,
                        method_id VARCHAR(255) NOT NULL,
                        conductor_id VARCHAR(255),
                        bells JSONB NOT NULL,
                        FOREIGN KEY (practice_id) REFERENCES practices(id) ON DELETE CASCADE
                    )
                """)
                
            conn.commit()
        finally:
            conn.close()
    
    # Employee methods
    def get_employees(self) -> List[Employee]:
        """Get all employees."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM employees ORDER BY last_name, first_name")
                rows = cur.fetchall()
                return [Employee(**dict(row)) for row in rows]
        finally:
            conn.close()
    
    def add_employee(self, employee: Employee):
        """Add a new employee."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO employees (id, first_name, last_name, member, resident) VALUES (%s, %s, %s, %s, %s)",
                    (employee.id, employee.first_name, employee.last_name, employee.member, employee.resident)
                )
            conn.commit()
        finally:
            conn.close()
    
    def update_employee(self, employee_id: str, employee: Employee):
        """Update an existing employee."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE employees SET first_name=%s, last_name=%s, member=%s, resident=%s WHERE id=%s",
                    (employee.first_name, employee.last_name, employee.member, employee.resident, employee_id)
                )
            conn.commit()
        finally:
            conn.close()
    
    def delete_employee(self, employee_id: str):
        """Delete an employee."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM employees WHERE id=%s", (employee_id,))
            conn.commit()
        finally:
            conn.close()
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Employee]:
        """Get employee by ID."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM employees WHERE id=%s", (employee_id,))
                row = cur.fetchone()
                return Employee(**dict(row)) if row else None
        finally:
            conn.close()
    
    # Practice methods
    def get_practices(self) -> List[Practice]:
        """Get all practices."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM practices ORDER BY date DESC")
                rows = cur.fetchall()
                return [Practice(**dict(row)) for row in rows]
        finally:
            conn.close()
    
    def add_practice(self, practice: Practice):
        """Add a new practice."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO practices (id, date, location) VALUES (%s, %s, %s)",
                    (practice.id, practice.date, practice.location)
                )
            conn.commit()
        finally:
            conn.close()
    
    def update_practice(self, practice_id: str, practice: Practice):
        """Update an existing practice."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE practices SET date=%s, location=%s WHERE id=%s",
                    (practice.date, practice.location, practice_id)
                )
            conn.commit()
        finally:
            conn.close()
    
    def delete_practice(self, practice_id: str):
        """Delete a practice and associated touches."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Touches will be deleted automatically due to CASCADE
                cur.execute("DELETE FROM practices WHERE id=%s", (practice_id,))
            conn.commit()
        finally:
            conn.close()
    
    def get_practice_by_id(self, practice_id: str) -> Optional[Practice]:
        """Get practice by ID."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM practices WHERE id=%s", (practice_id,))
                row = cur.fetchone()
                return Practice(**dict(row)) if row else None
        finally:
            conn.close()
    
    # Touch methods
    def get_touches(self, practice_id: Optional[str] = None) -> List[Touch]:
        """Get all touches, optionally filtered by practice."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if practice_id:
                    cur.execute("SELECT * FROM touches WHERE practice_id=%s", (practice_id,))
                else:
                    cur.execute("SELECT * FROM touches")
                rows = cur.fetchall()
                return [Touch(**dict(row)) for row in rows]
        finally:
            conn.close()
    
    def add_touch(self, touch: Touch):
        """Add a new touch."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO touches (id, practice_id, method_id, conductor_id, bells) VALUES (%s, %s, %s, %s, %s::jsonb)",
                    (touch.id, touch.practice_id, touch.method_id, touch.conductor_id, psycopg2.extras.Json(touch.bells))
                )
            conn.commit()
        finally:
            conn.close()
    
    def update_touch(self, touch_id: str, touch: Touch):
        """Update an existing touch."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE touches SET practice_id=%s, method_id=%s, conductor_id=%s, bells=%s::jsonb WHERE id=%s",
                    (touch.practice_id, touch.method_id, touch.conductor_id, psycopg2.extras.Json(touch.bells), touch_id)
                )
            conn.commit()
        finally:
            conn.close()
    
    def delete_touch(self, touch_id: str):
        """Delete a touch."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM touches WHERE id=%s", (touch_id,))
            conn.commit()
        finally:
            conn.close()
    
    def get_touch_by_id(self, touch_id: str) -> Optional[Touch]:
        """Get touch by ID."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM touches WHERE id=%s", (touch_id,))
                row = cur.fetchone()
                return Touch(**dict(row)) if row else None
        finally:
            conn.close()
    
    # Method methods
    def get_methods(self) -> List[Method]:
        """Get all workshop methods."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM methods ORDER BY name")
                rows = cur.fetchall()
                return [Method(**dict(row)) for row in rows]
        finally:
            conn.close()
    
    def add_method(self, method: Method):
        """Add a new method."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO methods (id, name, code) VALUES (%s, %s, %s)",
                    (method.id, method.name, method.code)
                )
            conn.commit()
        finally:
            conn.close()
    
    def update_method(self, method_id: str, method: Method):
        """Update an existing method."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE methods SET name=%s, code=%s WHERE id=%s",
                    (method.name, method.code, method_id)
                )
            conn.commit()
        finally:
            conn.close()
    
    def delete_method(self, method_id: str):
        """Delete a method."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM methods WHERE id=%s", (method_id,))
            conn.commit()
        finally:
            conn.close()
    
    def get_method_by_id(self, method_id: str) -> Optional[Method]:
        """Get method by ID."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM methods WHERE id=%s", (method_id,))
                row = cur.fetchone()
                return Method(**dict(row)) if row else None
        finally:
            conn.close()
