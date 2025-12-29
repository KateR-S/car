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
        """Test successful database connection."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch.object(NeonDataManager, '_ensure_tables'):
                manager = NeonDataManager()
                
                with patch('psycopg2.connect') as mock_connect:
                    mock_conn = Mock()
                    mock_connect.return_value = mock_conn
                    
                    conn = manager._get_connection()
                    
                    assert conn == mock_conn
                    mock_connect.assert_called_once_with(manager.connection_string)
    
    def test_get_connection_failure(self):
        """Test connection error handling."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch.object(NeonDataManager, '_ensure_tables'):
                manager = NeonDataManager()
                
                with patch('psycopg2.connect') as mock_connect:
                    mock_connect.side_effect = psycopg2.OperationalError("Connection failed")
                    
                    with pytest.raises(ConnectionError) as exc_info:
                        manager._get_connection()
                    
                    assert "Failed to connect to Neon database" in str(exc_info.value)
    
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
            
            with patch.object(NeonDataManager, '_get_connection', return_value=mock_conn):
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
            with patch.object(NeonDataManager, '_ensure_tables'):
                manager = NeonDataManager()
                
                mock_conn = Mock()
                mock_cursor = Mock()
                mock_cursor.fetchall.return_value = [
                    {'id': '1', 'first_name': 'John', 'last_name': 'Doe', 'member': True, 'resident': 'Local'}
                ]
                
                with patch.object(manager, '_get_connection', return_value=mock_conn):
                    mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
                    mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
                    
                    ringers = manager.get_employees()
                    
                    assert len(ringers) == 1
                    assert isinstance(ringers[0], Employee)
                    assert ringers[0].first_name == 'John'
                    mock_cursor.execute.assert_called_once()
                    assert 'SELECT * FROM ringers' in mock_cursor.execute.call_args[0][0]
    
    def test_add_employee(self):
        """Test adding a ringer."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
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
            
            with patch.object(NeonDataManager, '_get_connection', return_value=mock_conn):
                manager = NeonDataManager()
                
                # Check that foreign key references ringers table
                calls = [str(call) for call in mock_cursor.execute.call_args_list]
                ringers_fk = any('REFERENCES ringers(id)' in str(call) for call in calls)
                assert ringers_fk, "Foreign key should reference ringers table"
    
    def test_connection_cleanup_on_error(self):
        """Test that connections are properly closed even on error."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch.object(NeonDataManager, '_ensure_tables'):
                manager = NeonDataManager()
                
                mock_conn = Mock()
                mock_cursor = Mock()
                mock_cursor.execute.side_effect = Exception("Database error")
                
                with patch.object(manager, '_get_connection', return_value=mock_conn):
                    mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
                    mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
                    
                    with pytest.raises(Exception):
                        manager.get_employees()
                    
                    # Connection should still be closed
                    mock_conn.close.assert_called_once()
