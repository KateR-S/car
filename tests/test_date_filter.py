"""Tests for touch date filtering functionality."""

import pytest
import uuid
from src.data_manager import DataManager
from src.neon_data_manager import NeonDataManager
from src.models import Practice, Touch, Employee, Method
from unittest.mock import Mock, MagicMock, patch
import os


class TestDateFilterDataManager:
    """Test date filtering with JSON DataManager."""
    
    @pytest.fixture
    def data_manager(self, tmp_path):
        """Create a temporary DataManager for testing."""
        data_file = tmp_path / "test_data.json"
        return DataManager(str(data_file))
    
    @pytest.fixture
    def sample_data(self, data_manager):
        """Create sample data for testing."""
        # Add employees
        emp1 = Employee(id=str(uuid.uuid4()), first_name="John", last_name="Doe", member=True, resident="Local")
        emp2 = Employee(id=str(uuid.uuid4()), first_name="Jane", last_name="Smith", member=True, resident="Local")
        data_manager.add_employee(emp1)
        data_manager.add_employee(emp2)
        
        # Add methods
        method1 = Method(id=str(uuid.uuid4()), name="Plain Bob", code="PB")
        method2 = Method(id=str(uuid.uuid4()), name="Grandsire", code="GS")
        data_manager.add_method(method1)
        data_manager.add_method(method2)
        
        # Add practices with different dates
        practice1 = Practice(id=str(uuid.uuid4()), date="30-12-2025", location="Cathedral")
        practice2 = Practice(id=str(uuid.uuid4()), date="31-12-2025", location="Withycombe Raleigh")
        practice3 = Practice(id=str(uuid.uuid4()), date="30-12-2025", location="Withycombe Raleigh")
        data_manager.add_practice(practice1)
        data_manager.add_practice(practice2)
        data_manager.add_practice(practice3)
        
        # Add touches
        touch1 = Touch(
            id=str(uuid.uuid4()),
            practice_id=practice1.id,
            method_id=method1.id,
            touch_number=1,
            conductor_id=emp1.id,
            bells=[emp1.id] + [None] * 11
        )
        touch2 = Touch(
            id=str(uuid.uuid4()),
            practice_id=practice2.id,
            method_id=method2.id,
            touch_number=1,
            conductor_id=emp2.id,
            bells=[emp2.id] + [None] * 11
        )
        touch3 = Touch(
            id=str(uuid.uuid4()),
            practice_id=practice3.id,
            method_id=method1.id,
            touch_number=1,
            conductor_id=emp1.id,
            bells=[emp1.id] + [None] * 11
        )
        data_manager.add_touch(touch1)
        data_manager.add_touch(touch2)
        data_manager.add_touch(touch3)
        
        return {
            'employees': [emp1, emp2],
            'methods': [method1, method2],
            'practices': [practice1, practice2, practice3],
            'touches': [touch1, touch2, touch3]
        }
    
    def test_get_touches_by_date_returns_correct_touches(self, data_manager, sample_data):
        """Test that get_touches_by_date returns touches for the correct date."""
        # Get touches for 30-12-2025 (should return 2 touches)
        touches = data_manager.get_touches_by_date("30-12-2025")
        assert len(touches) == 2
        
        # Verify they're the correct touches
        touch_ids = {t.id for t in touches}
        assert sample_data['touches'][0].id in touch_ids
        assert sample_data['touches'][2].id in touch_ids
    
    def test_get_touches_by_date_returns_empty_for_no_matches(self, data_manager, sample_data):
        """Test that get_touches_by_date returns empty list when no touches match."""
        touches = data_manager.get_touches_by_date("01-01-2026")
        assert len(touches) == 0
    
    def test_get_touches_by_date_returns_one_touch(self, data_manager, sample_data):
        """Test that get_touches_by_date returns single touch correctly."""
        touches = data_manager.get_touches_by_date("31-12-2025")
        assert len(touches) == 1
        assert touches[0].id == sample_data['touches'][1].id


class TestDateFilterNeonDataManager:
    """Test date filtering with Neon PostgreSQL DataManager."""
    
    @pytest.fixture
    def mock_neon_manager(self):
        """Create a mocked NeonDataManager for testing."""
        # Set up environment variables
        os.environ['DB_ROLE'] = 'test_role'
        os.environ['DB_PASS'] = 'test_pass'
        os.environ['DB_NAME'] = 'test_name'
        os.environ['DB_DATABASE'] = 'test_db'
        
        with patch('src.neon_data_manager.pool') as mock_pool:
            # Create mock connection pool
            mock_connection_pool = MagicMock()
            mock_pool.SimpleConnectionPool.return_value = mock_connection_pool
            
            manager = NeonDataManager()
            manager._connection_pool = mock_connection_pool
            
            yield manager
    
    def test_get_touches_by_date_executes_correct_query(self, mock_neon_manager):
        """Test that get_touches_by_date executes the correct SQL query."""
        # Create mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)
        mock_cursor.fetchall.return_value = []
        
        mock_conn.cursor.return_value = mock_cursor
        mock_neon_manager._connection_pool.getconn.return_value = mock_conn
        
        # Call the method
        mock_neon_manager.get_touches_by_date("30-12-2025")
        
        # Verify the SQL query was executed
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        sql_query = call_args[0][0]
        
        # Check that the query joins touches and practices and filters by date
        assert "SELECT t.* FROM touches t" in sql_query
        assert "INNER JOIN practices p" in sql_query
        assert "WHERE p.date" in sql_query
        assert "ORDER BY t.touch_number" in sql_query
        
        # Verify the date parameter was passed
        assert call_args[0][1] == ("30-12-2025",)
    
    def test_get_touches_by_date_returns_touch_objects(self, mock_neon_manager):
        """Test that get_touches_by_date returns Touch objects."""
        # Create mock connection and cursor with sample data
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)
        
        # Mock return data
        touch_data = {
            'id': str(uuid.uuid4()),
            'practice_id': str(uuid.uuid4()),
            'method_id': str(uuid.uuid4()),
            'touch_number': 1,
            'conductor_id': str(uuid.uuid4()),
            'bells': [None] * 12
        }
        mock_cursor.fetchall.return_value = [touch_data]
        
        mock_conn.cursor.return_value = mock_cursor
        mock_neon_manager._connection_pool.getconn.return_value = mock_conn
        
        # Call the method
        touches = mock_neon_manager.get_touches_by_date("30-12-2025")
        
        # Verify we got Touch objects
        assert len(touches) == 1
        assert isinstance(touches[0], Touch)
        assert touches[0].id == touch_data['id']
