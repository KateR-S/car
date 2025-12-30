"""Neon PostgreSQL database manager for persistent storage."""

import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor, Json
from typing import Dict, List, Optional
import logging
import config
from src.models import Employee, Practice, Touch, Method

# Configure logging
logger = logging.getLogger(__name__)


class NeonDataManager:
    """Manages data persistence using Neon PostgreSQL database with connection pooling."""
    
    def __init__(self):
        """Initialize Neon data manager with connection pool."""
        logger.info("Initializing NeonDataManager")
        self.connection_string = self._build_connection_string()
        self._connection_pool = None
        self._init_connection_pool()
        self._ensure_tables()
        logger.info("NeonDataManager initialization complete")
    
    def _build_connection_string(self) -> str:
        """Build PostgreSQL connection string from environment variables.
        
        IMPORTANT: This method uses environment variables and never logs them.
        """
        logger.debug("Building connection string from environment variables")
        db_role = os.environ.get('DB_ROLE')
        db_pass = os.environ.get('DB_PASS')
        db_name = os.environ.get('DB_NAME')
        db_database = os.environ.get('DB_DATABASE')
        
        if not all([db_role, db_pass, db_name, db_database]):
            logger.error("Missing required database environment variables")
            raise ValueError(
                "Missing required environment variables: DB_ROLE, DB_PASS, DB_NAME, DB_DATABASE. "
                "Please set these environment variables to use Neon database."
            )
        
        # Build connection string (credentials are not logged)
        logger.debug("Connection string built successfully")
        return f"postgresql://{db_role}:{db_pass}@{db_name}.eu-west-2.aws.neon.tech/{db_database}?sslmode=require&channel_binding=require"
    
    def _init_connection_pool(self):
        """Initialize the connection pool."""
        try:
            min_conn = config.DB_POOL_MIN_CONNECTIONS
            max_conn = config.DB_POOL_MAX_CONNECTIONS
            logger.info(f"Creating connection pool (min={min_conn}, max={max_conn})")
            self._connection_pool = pool.SimpleConnectionPool(
                min_conn,
                max_conn,
                self.connection_string
            )
            logger.info("Connection pool created successfully")
        except psycopg2.OperationalError as e:
            logger.error(f"Failed to create connection pool: {str(e)}")
            raise ConnectionError(
                f"Failed to connect to Neon database. Please verify your credentials and network connection. "
                f"Error: {str(e)}"
            )
    
    def _get_connection(self):
        """Get a database connection from the pool."""
        if self._connection_pool is None:
            logger.error("Connection pool is not initialized")
            raise ConnectionError("Connection pool not initialized")
        
        try:
            logger.debug("Getting connection from pool")
            conn = self._connection_pool.getconn()
            logger.debug("Connection obtained from pool")
            return conn
        except psycopg2.OperationalError as e:
            logger.error(f"Failed to get connection from pool: {str(e)}")
            raise ConnectionError(
                f"Failed to get connection from pool. Error: {str(e)}"
            )
    
    def _release_connection(self, conn):
        """Release a connection back to the pool."""
        if self._connection_pool and conn:
            logger.debug("Releasing connection back to pool")
            self._connection_pool.putconn(conn)
    
    def close_all_connections(self):
        """Close all connections in the pool. Should be called on app shutdown."""
        if self._connection_pool:
            logger.info("Closing all connections in pool")
            self._connection_pool.closeall()
            logger.info("All connections closed")
    
    def _ensure_tables(self):
        """Create database tables if they don't exist."""
        logger.info("Ensuring database tables exist")
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Create ringers table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ringers (
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
                        touch_number INTEGER NOT NULL,
                        conductor_id VARCHAR(255),
                        bells JSONB NOT NULL,
                        FOREIGN KEY (practice_id) REFERENCES practices(id) ON DELETE CASCADE,
                        FOREIGN KEY (method_id) REFERENCES methods(id),
                        FOREIGN KEY (conductor_id) REFERENCES ringers(id),
                        UNIQUE(practice_id, touch_number)
                    )
                """)
                
            conn.commit()
            logger.info("Database tables ensured")
        finally:
            self._release_connection(conn)
    
    # Ringer methods
    def get_employees(self) -> List[Employee]:
        """Get all ringers."""
        logger.debug("Fetching all employees")
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM ringers ORDER BY last_name, first_name")
                rows = cur.fetchall()
                logger.debug(f"Fetched {len(rows)} employees")
                return [Employee(**dict(row)) for row in rows]
        finally:
            self._release_connection(conn)
    
    def add_employee(self, ringer: Employee):
        """Add a new ringer."""
        logger.info(f"Adding new employee: {ringer.first_name} {ringer.last_name}")
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO ringers (id, first_name, last_name, member, resident) VALUES (%s, %s, %s, %s, %s)",
                    (ringer.id, ringer.first_name, ringer.last_name, ringer.member, ringer.resident)
                )
            conn.commit()
            logger.info(f"Employee added successfully: {ringer.id}")
        finally:
            self._release_connection(conn)
    
    def update_employee(self, ringer_id: str, ringer: Employee):
        """Update an existing ringer."""
        logger.info(f"Updating employee: {ringer_id}")
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE ringers SET first_name=%s, last_name=%s, member=%s, resident=%s WHERE id=%s",
                    (ringer.first_name, ringer.last_name, ringer.member, ringer.resident, ringer_id)
                )
            conn.commit()
            logger.info(f"Employee updated successfully: {ringer_id}")
        finally:
            self._release_connection(conn)
    
    def delete_employee(self, ringer_id: str):
        """Delete a ringer."""
        logger.info(f"Deleting employee: {ringer_id}")
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM ringers WHERE id=%s", (ringer_id,))
            conn.commit()
            logger.info(f"Employee deleted successfully: {ringer_id}")
        finally:
            self._release_connection(conn)
    
    def get_employee_by_id(self, ringer_id: str) -> Optional[Employee]:
        """Get ringer by ID."""
        logger.debug(f"Fetching employee by ID: {ringer_id}")
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM ringers WHERE id=%s", (ringer_id,))
                row = cur.fetchone()
                result = Employee(**dict(row)) if row else None
                logger.debug(f"Employee {'found' if result else 'not found'}: {ringer_id}")
                return result
        finally:
            self._release_connection(conn)
    
    # Practice methods
    def get_practices(self) -> List[Practice]:
        """Get all practices."""
        logger.debug("Fetching all practices")
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM practices ORDER BY date DESC")
                rows = cur.fetchall()
                logger.debug(f"Fetched {len(rows)} practices")
                return [Practice(**dict(row)) for row in rows]
        finally:
            self._release_connection(conn)
    
    def add_practice(self, practice: Practice):
        """Add a new practice."""
        logger.info(f"Adding new practice: {practice.date} at {practice.location}")
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO practices (id, date, location) VALUES (%s, %s, %s)",
                    (practice.id, practice.date, practice.location)
                )
            conn.commit()
            logger.info(f"Practice added successfully: {practice.id}")
        finally:
            self._release_connection(conn)
    
    def update_practice(self, practice_id: str, practice: Practice):
        """Update an existing practice."""
        logger.info(f"Updating practice: {practice_id}")
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE practices SET date=%s, location=%s WHERE id=%s",
                    (practice.date, practice.location, practice_id)
                )
            conn.commit()
            logger.info(f"Practice updated successfully: {practice_id}")
        finally:
            self._release_connection(conn)
    
    def delete_practice(self, practice_id: str):
        """Delete a practice and associated touches."""
        logger.info(f"Deleting practice: {practice_id}")
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Touches will be deleted automatically due to CASCADE
                cur.execute("DELETE FROM practices WHERE id=%s", (practice_id,))
            conn.commit()
            logger.info(f"Practice deleted successfully: {practice_id}")
        finally:
            self._release_connection(conn)
    
    def get_practice_by_id(self, practice_id: str) -> Optional[Practice]:
        """Get practice by ID."""
        logger.debug(f"Fetching practice by ID: {practice_id}")
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM practices WHERE id=%s", (practice_id,))
                row = cur.fetchone()
                result = Practice(**dict(row)) if row else None
                logger.debug(f"Practice {'found' if result else 'not found'}: {practice_id}")
                return result
        finally:
            self._release_connection(conn)
    
    # Touch methods
    def get_touches(self, practice_id: Optional[str] = None) -> List[Touch]:
        """Get all touches, optionally filtered by practice."""
        logger.debug(f"Fetching touches{' for practice ' + practice_id if practice_id else ''}")
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if practice_id:
                    cur.execute("SELECT * FROM touches WHERE practice_id=%s ORDER BY touch_number", (practice_id,))
                else:
                    cur.execute("SELECT * FROM touches ORDER BY practice_id, touch_number")
                rows = cur.fetchall()
                logger.debug(f"Fetched {len(rows)} touches")
                return [Touch(**dict(row)) for row in rows]
        finally:
            self._release_connection(conn)
    
    def get_touches_by_date(self, date: str) -> List[Touch]:
        """Get all touches for practices on a specific date.
        
        Args:
            date: Date in DD-MM-YYYY format (e.g., "30-12-2025")
        
        Returns:
            List of touches for practices on the specified date
        """
        logger.debug(f"Fetching touches for date: {date}")
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Join touches with practices to filter by date
                cur.execute("""
                    SELECT t.* FROM touches t
                    INNER JOIN practices p ON t.practice_id = p.id
                    WHERE p.date = %s
                    ORDER BY t.touch_number
                """, (date,))
                rows = cur.fetchall()
                logger.debug(f"Fetched {len(rows)} touches for date {date}")
                return [Touch(**dict(row)) for row in rows]
        finally:
            self._release_connection(conn)
    
    def get_next_touch_number(self, practice_id: str) -> int:
        """Get the next available touch number for a practice.
        
        Returns the smallest available number from 1 to MAX_TOUCHES_PER_PRACTICE.
        If all slots are filled, returns MAX_TOUCHES_PER_PRACTICE + 1.
        """
        from config import MAX_TOUCHES_PER_PRACTICE
        logger.debug(f"Getting next touch number for practice: {practice_id}")
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT touch_number FROM touches WHERE practice_id=%s ORDER BY touch_number",
                    (practice_id,)
                )
                rows = cur.fetchall()
                existing_numbers = {row['touch_number'] for row in rows}
                
                # Find the first available number
                for i in range(1, MAX_TOUCHES_PER_PRACTICE + 1):
                    if i not in existing_numbers:
                        logger.debug(f"Next available touch number: {i}")
                        return i
                
                # All slots filled, return next number (will be over limit)
                logger.debug(f"All touch slots filled, returning {MAX_TOUCHES_PER_PRACTICE + 1}")
                return MAX_TOUCHES_PER_PRACTICE + 1
        finally:
            self._release_connection(conn)
    
    def add_touch(self, touch: Touch):
        """Add a new touch."""
        logger.info(f"Adding new touch: {touch.id} for practice {touch.practice_id}")
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO touches (id, practice_id, method_id, touch_number, conductor_id, bells) VALUES (%s, %s, %s, %s, %s, %s::jsonb)",
                    (touch.id, touch.practice_id, touch.method_id, touch.touch_number, touch.conductor_id, Json(touch.bells))
                )
            conn.commit()
            logger.info(f"Touch added successfully: {touch.id}")
        finally:
            self._release_connection(conn)
    
    def update_touch(self, touch_id: str, touch: Touch):
        """Update an existing touch."""
        logger.info(f"Updating touch: {touch_id}")
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE touches SET practice_id=%s, method_id=%s, touch_number=%s, conductor_id=%s, bells=%s::jsonb WHERE id=%s",
                    (touch.practice_id, touch.method_id, touch.touch_number, touch.conductor_id, Json(touch.bells), touch_id)
                )
            conn.commit()
            logger.info(f"Touch updated successfully: {touch_id}")
        finally:
            self._release_connection(conn)
    
    def delete_touch(self, touch_id: str):
        """Delete a touch."""
        logger.info(f"Deleting touch: {touch_id}")
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM touches WHERE id=%s", (touch_id,))
            conn.commit()
            logger.info(f"Touch deleted successfully: {touch_id}")
        finally:
            self._release_connection(conn)
    
    def get_touch_by_id(self, touch_id: str) -> Optional[Touch]:
        """Get touch by ID."""
        logger.debug(f"Fetching touch by ID: {touch_id}")
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM touches WHERE id=%s", (touch_id,))
                row = cur.fetchone()
                result = Touch(**dict(row)) if row else None
                logger.debug(f"Touch {'found' if result else 'not found'}: {touch_id}")
                return result
        finally:
            self._release_connection(conn)
    
    # Method methods
    def get_methods(self) -> List[Method]:
        """Get all workshop methods."""
        logger.debug("Fetching all methods")
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM methods ORDER BY name")
                rows = cur.fetchall()
                logger.debug(f"Fetched {len(rows)} methods")
                return [Method(**dict(row)) for row in rows]
        finally:
            self._release_connection(conn)
    
    def add_method(self, method: Method):
        """Add a new method."""
        logger.info(f"Adding new method: {method.name}")
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO methods (id, name, code) VALUES (%s, %s, %s)",
                    (method.id, method.name, method.code)
                )
            conn.commit()
            logger.info(f"Method added successfully: {method.id}")
        finally:
            self._release_connection(conn)
    
    def update_method(self, method_id: str, method: Method):
        """Update an existing method."""
        logger.info(f"Updating method: {method_id}")
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE methods SET name=%s, code=%s WHERE id=%s",
                    (method.name, method.code, method_id)
                )
            conn.commit()
            logger.info(f"Method updated successfully: {method_id}")
        finally:
            self._release_connection(conn)
    
    def delete_method(self, method_id: str):
        """Delete a method."""
        logger.info(f"Deleting method: {method_id}")
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM methods WHERE id=%s", (method_id,))
            conn.commit()
            logger.info(f"Method deleted successfully: {method_id}")
        finally:
            self._release_connection(conn)
    
    def get_method_by_id(self, method_id: str) -> Optional[Method]:
        """Get method by ID."""
        logger.debug(f"Fetching method by ID: {method_id}")
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM methods WHERE id=%s", (method_id,))
                row = cur.fetchone()
                result = Method(**dict(row)) if row else None
                logger.debug(f"Method {'found' if result else 'not found'}: {method_id}")
                return result
        finally:
            self._release_connection(conn)
