"""Tests for NeonDataManager class."""

import os
import pytest
import psycopg2
from unittest.mock import Mock, patch, MagicMock
from src.neon_data_manager import NeonDataManager
from src.models import Employee, Practice, Touch, Method


class TestNeonDataManager:
    """Test suite for NeonDataManager."""
    
    def test_build_connection_string_with_all_env_vars(self):
        """Test connection string is built correctly when all env vars are set."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch.object(NeonDataManager, '_init_connection_pool'):
                with patch.object(NeonDataManager, '_ensure_tables'):
                    manager = NeonDataManager()
                    
                    expected = "postgresql://test_role:test_pass@test_name.eu-west-2.aws.neon.tech/test_db?sslmode=require&channel_binding=require"
                    assert manager.connection_string == expected
    
    def test_build_connection_string_missing_env_vars(self):
        """Test that ValueError is raised when env vars are missing."""
        # Clear all DB env vars
        env_vars = {k: v for k, v in os.environ.items() if not k.startswith('DB_')}
        
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError) as exc_info:
                NeonDataManager()
            
            assert "Missing required environment variables" in str(exc_info.value)
            assert "DB_ROLE" in str(exc_info.value)
    
    def test_get_connection_success(self):
        """Test successful database connection from pool."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch.object(NeonDataManager, '_init_connection_pool'):
                with patch.object(NeonDataManager, '_ensure_tables'):
                    manager = NeonDataManager()
                    
                    mock_conn = Mock()
                    manager._connection_pool = Mock()
                    manager._connection_pool.getconn.return_value = mock_conn
                    
                    conn = manager._get_connection()
                    
                    assert conn == mock_conn
                    manager._connection_pool.getconn.assert_called_once()
    
    def test_get_connection_failure(self):
        """Test connection error handling when pool fails."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch.object(NeonDataManager, '_init_connection_pool'):
                with patch.object(NeonDataManager, '_ensure_tables'):
                    manager = NeonDataManager()
                    
                    manager._connection_pool = Mock()
                    manager._connection_pool.getconn.side_effect = psycopg2.OperationalError("Connection failed")
                    
                    with pytest.raises(ConnectionError) as exc_info:
                        manager._get_connection()
                    
                    assert "Failed to get connection from pool" in str(exc_info.value)
    
    def test_ensure_tables_creates_ringers_table(self):
        """Test that ensure_tables creates the ringers table."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
            mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
            
            with patch.object(NeonDataManager, '_init_connection_pool'):
                with patch.object(NeonDataManager, '_get_connection', return_value=mock_conn):
                    with patch.object(NeonDataManager, '_release_connection'):
                        manager = NeonDataManager()
                        
                        # Check that ringers table was created
                        calls = [str(call) for call in mock_cursor.execute.call_args_list]
                        ringers_table_created = any('CREATE TABLE IF NOT EXISTS ringers' in str(call) for call in calls)
                        assert ringers_table_created, "Ringers table should be created"
    
    def test_get_employees_returns_list(self):
        """Test get_employees returns list of Employee objects."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch.object(NeonDataManager, '_init_connection_pool'):
                with patch.object(NeonDataManager, '_ensure_tables'):
                    manager = NeonDataManager()
                    
                    mock_conn = Mock()
                    mock_cursor = Mock()
                    mock_cursor.fetchall.return_value = [
                        {'id': '1', 'first_name': 'John', 'last_name': 'Doe', 'member': True, 'resident': 'Local'}
                    ]
                    
                    with patch.object(manager, '_get_connection', return_value=mock_conn):
                        with patch.object(manager, '_release_connection'):
                            mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
                            mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
                            
                            ringers = manager.get_employees()
                            
                            assert len(ringers) == 1
                            assert isinstance(ringers[0], Employee)
                            assert ringers[0].first_name == 'John'
                            mock_cursor.execute.assert_called_once()
                            assert 'SELECT * FROM ringers' in mock_cursor.execute.call_args[0][0]
                            manager._release_connection.assert_called_once_with(mock_conn)
    
    def test_add_employee(self):
        """Test adding a ringer."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch.object(NeonDataManager, '_init_connection_pool'):
                with patch.object(NeonDataManager, '_ensure_tables'):
                    manager = NeonDataManager()
                    
                    mock_conn = Mock()
                    mock_cursor = Mock()
                    
                    with patch.object(manager, '_get_connection', return_value=mock_conn):
                        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
                        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
                        
                        ringer = Employee(id='1', first_name='Jane', last_name='Smith', member=False, resident='Regional')
                        manager.add_employee(ringer)
                        
                        mock_cursor.execute.assert_called_once()
                        call_args = mock_cursor.execute.call_args[0]
                        assert 'INSERT INTO ringers' in call_args[0]
                        assert call_args[1] == ('1', 'Jane', 'Smith', False, 'Regional')
                        mock_conn.commit.assert_called_once()
    
    def test_update_employee(self):
        """Test updating a ringer."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch.object(NeonDataManager, '_init_connection_pool'):
                with patch.object(NeonDataManager, '_ensure_tables'):
                    manager = NeonDataManager()
                    
                    mock_conn = Mock()
                    mock_cursor = Mock()
                    
                    with patch.object(manager, '_get_connection', return_value=mock_conn):
                        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
                        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
                        
                        ringer = Employee(id='1', first_name='Jane', last_name='Doe', member=True, resident='Local')
                        manager.update_employee('1', ringer)
                        
                        mock_cursor.execute.assert_called_once()
                        call_args = mock_cursor.execute.call_args[0]
                        assert 'UPDATE ringers' in call_args[0]
                        assert call_args[1] == ('Jane', 'Doe', True, 'Local', '1')
                        mock_conn.commit.assert_called_once()
    
    def test_delete_employee(self):
        """Test deleting a ringer."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch.object(NeonDataManager, '_init_connection_pool'):
                with patch.object(NeonDataManager, '_ensure_tables'):
                    manager = NeonDataManager()
                    
                    mock_conn = Mock()
                    mock_cursor = Mock()
                    
                    with patch.object(manager, '_get_connection', return_value=mock_conn):
                        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
                        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
                        
                        manager.delete_employee('1')
                        
                        mock_cursor.execute.assert_called_once()
                        call_args = mock_cursor.execute.call_args[0]
                        assert 'DELETE FROM ringers' in call_args[0]
                        assert call_args[1] == ('1',)
                        mock_conn.commit.assert_called_once()
    
    def test_get_employee_by_id(self):
        """Test getting a ringer by ID."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch.object(NeonDataManager, '_init_connection_pool'):
                with patch.object(NeonDataManager, '_ensure_tables'):
                    manager = NeonDataManager()
                    
                    mock_conn = Mock()
                    mock_cursor = Mock()
                    mock_cursor.fetchone.return_value = {
                        'id': '1', 'first_name': 'John', 'last_name': 'Doe', 'member': True, 'resident': 'Local'
                    }
                    
                    with patch.object(manager, '_get_connection', return_value=mock_conn):
                        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
                        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
                        
                        ringer = manager.get_employee_by_id('1')
                        
                        assert ringer is not None
                        assert isinstance(ringer, Employee)
                        assert ringer.id == '1'
                        assert ringer.first_name == 'John'
                        mock_cursor.execute.assert_called_once()
                        assert 'SELECT * FROM ringers WHERE id=' in mock_cursor.execute.call_args[0][0]
    
    def test_get_employee_by_id_not_found(self):
        """Test getting a ringer by ID that doesn't exist."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch.object(NeonDataManager, '_init_connection_pool'):
                with patch.object(NeonDataManager, '_ensure_tables'):
                    manager = NeonDataManager()
                    
                    mock_conn = Mock()
                    mock_cursor = Mock()
                    mock_cursor.fetchone.return_value = None
                    
                    with patch.object(manager, '_get_connection', return_value=mock_conn):
                        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
                        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
                        
                        ringer = manager.get_employee_by_id('999')
                        
                        assert ringer is None
    
    def test_add_practice(self):
        """Test adding a practice."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch.object(NeonDataManager, '_init_connection_pool'):
                with patch.object(NeonDataManager, '_ensure_tables'):
                    manager = NeonDataManager()
                    
                    mock_conn = Mock()
                    mock_cursor = Mock()
                    
                    with patch.object(manager, '_get_connection', return_value=mock_conn):
                        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
                        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
                        
                        practice = Practice(id='p1', date='01-01-2024', location='Office A')
                        manager.add_practice(practice)
                        
                        mock_cursor.execute.assert_called_once()
                        call_args = mock_cursor.execute.call_args[0]
                        assert 'INSERT INTO practices' in call_args[0]
                        mock_conn.commit.assert_called_once()
    
    def test_add_touch(self):
        """Test adding a touch."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch.object(NeonDataManager, '_init_connection_pool'):
                with patch.object(NeonDataManager, '_ensure_tables'):
                    manager = NeonDataManager()
                    
                    mock_conn = Mock()
                    mock_cursor = Mock()
                    
                    with patch.object(manager, '_get_connection', return_value=mock_conn):
                        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
                        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
                        
                        touch = Touch(id='t1', practice_id='p1', method_id='m1', conductor_id='r1', bells=[None]*12)
                        manager.add_touch(touch)
                        
                        mock_cursor.execute.assert_called_once()
                        call_args = mock_cursor.execute.call_args[0]
                        assert 'INSERT INTO touches' in call_args[0]
                        mock_conn.commit.assert_called_once()
    
    def test_foreign_key_constraint_to_ringers(self):
        """Test that touches table has foreign key constraint to ringers table."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
            mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
            
            with patch.object(NeonDataManager, '_init_connection_pool'):
                with patch.object(NeonDataManager, '_get_connection', return_value=mock_conn):
                    manager = NeonDataManager()
                    
                    # Check that foreign key references ringers table
                    calls = [str(call) for call in mock_cursor.execute.call_args_list]
                    ringers_fk = any('REFERENCES ringers(id)' in str(call) for call in calls)
                    assert ringers_fk, "Foreign key should reference ringers table"
    
    def test_connection_cleanup_on_error(self):
        """Test that connections are properly released even on error."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch.object(NeonDataManager, '_init_connection_pool'):
                with patch.object(NeonDataManager, '_ensure_tables'):
                    manager = NeonDataManager()
                    
                    mock_conn = Mock()
                    mock_cursor = Mock()
                    mock_cursor.execute.side_effect = Exception("Database error")
                    
                    with patch.object(manager, '_get_connection', return_value=mock_conn):
                        with patch.object(manager, '_release_connection') as mock_release:
                            mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
                            mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
                            
                            with pytest.raises(Exception):
                                manager.get_employees()
                            
                            # Connection should still be released
                            mock_release.assert_called_once_with(mock_conn)
    
    def test_get_next_touch_number_empty_practice(self):
        """Test get_next_touch_number returns 1 for practice with no touches."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch.object(NeonDataManager, '_init_connection_pool'):
                with patch.object(NeonDataManager, '_ensure_tables'):
                    manager = NeonDataManager()
                    
                    mock_conn = Mock()
                    mock_cursor = Mock()
                    mock_cursor.fetchall.return_value = []
                    
                    with patch.object(manager, '_get_connection', return_value=mock_conn):
                        with patch.object(manager, '_release_connection'):
                            mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
                            mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
                            
                            next_number = manager.get_next_touch_number('p1')
                            
                            assert next_number == 1
    
    def test_get_next_touch_number_with_gaps(self):
        """Test get_next_touch_number finds first gap in touch numbers."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch.object(NeonDataManager, '_init_connection_pool'):
                with patch.object(NeonDataManager, '_ensure_tables'):
                    manager = NeonDataManager()
                    
                    mock_conn = Mock()
                    mock_cursor = Mock()
                    # Simulate touches with numbers 1, 2, 4 (gap at 3)
                    mock_cursor.fetchall.return_value = [
                        {'touch_number': 1},
                        {'touch_number': 2},
                        {'touch_number': 4}
                    ]
                    
                    with patch.object(manager, '_get_connection', return_value=mock_conn):
                        with patch.object(manager, '_release_connection'):
                            mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
                            mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
                            
                            next_number = manager.get_next_touch_number('p1')
                            
                            assert next_number == 3
    
    def test_touch_number_unique_constraint(self):
        """Test that touches table has unique constraint on (practice_id, touch_number)."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
            mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
            
            with patch.object(NeonDataManager, '_init_connection_pool'):
                with patch.object(NeonDataManager, '_get_connection', return_value=mock_conn):
                    with patch.object(NeonDataManager, '_release_connection'):
                        manager = NeonDataManager()
                        
                        # Check that unique constraint on practice_id and touch_number exists
                        calls = [str(call) for call in mock_cursor.execute.call_args_list]
                        unique_constraint = any('UNIQUE(practice_id, touch_number)' in str(call) for call in calls)
                        assert unique_constraint, "Unique constraint should exist on (practice_id, touch_number)"
