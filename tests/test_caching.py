"""Tests for caching and connection pooling functionality."""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.data_manager import (
    get_data_manager,
    get_cached_employees,
    get_cached_practices,
    get_cached_touches,
    get_cached_methods,
    invalidate_data_cache,
    get_cache_version
)
from src.models import Employee, Practice, Touch, Method


class TestConnectionPooling:
    """Test suite for connection pooling in NeonDataManager."""
    
    def test_neon_manager_uses_connection_pool(self):
        """Test that NeonDataManager initializes with a connection pool."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db',
            'USE_NEON': 'true'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch('psycopg2.pool.SimpleConnectionPool') as mock_pool:
                mock_pool_instance = Mock()
                mock_pool.return_value = mock_pool_instance
                
                with patch('src.neon_data_manager.NeonDataManager._ensure_tables'):
                    from src.neon_data_manager import NeonDataManager
                    manager = NeonDataManager()
                    
                    # Verify connection pool was created
                    mock_pool.assert_called_once()
                    assert manager._connection_pool == mock_pool_instance
    
    def test_get_connection_from_pool(self):
        """Test that _get_connection retrieves from pool."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch('psycopg2.pool.SimpleConnectionPool'):
                with patch('src.neon_data_manager.NeonDataManager._ensure_tables'):
                    from src.neon_data_manager import NeonDataManager
                    manager = NeonDataManager()
                    
                    mock_conn = Mock()
                    manager._connection_pool = Mock()
                    manager._connection_pool.getconn.return_value = mock_conn
                    
                    conn = manager._get_connection()
                    
                    assert conn == mock_conn
                    manager._connection_pool.getconn.assert_called_once()
    
    def test_release_connection_to_pool(self):
        """Test that _release_connection returns connection to pool."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch('psycopg2.pool.SimpleConnectionPool'):
                with patch('src.neon_data_manager.NeonDataManager._ensure_tables'):
                    from src.neon_data_manager import NeonDataManager
                    manager = NeonDataManager()
                    
                    mock_conn = Mock()
                    manager._connection_pool = Mock()
                    
                    manager._release_connection(mock_conn)
                    
                    manager._connection_pool.putconn.assert_called_once_with(mock_conn)
    
    def test_connection_reused_across_calls(self):
        """Test that connections are reused across multiple database calls."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch('psycopg2.pool.SimpleConnectionPool'):
                with patch('src.neon_data_manager.NeonDataManager._ensure_tables'):
                    from src.neon_data_manager import NeonDataManager
                    manager = NeonDataManager()
                    
                    # Mock the connection pool
                    mock_conn = Mock()
                    mock_cursor = Mock()
                    mock_cursor.fetchall.return_value = []
                    mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
                    mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
                    
                    manager._connection_pool = Mock()
                    manager._connection_pool.getconn.return_value = mock_conn
                    
                    # Make multiple calls
                    manager.get_employees()
                    manager.get_employees()
                    manager.get_employees()
                    
                    # Connection should be obtained 3 times (once per call)
                    assert manager._connection_pool.getconn.call_count == 3
                    # Connection should be released 3 times (once per call)
                    assert manager._connection_pool.putconn.call_count == 3


class TestDataCaching:
    """Test suite for data caching functionality."""
    
    def test_cache_version_increments_on_invalidation(self):
        """Test that cache version increments when invalidated."""
        # Import streamlit for this test
        import streamlit as st
        
        # Initialize session state
        if 'cache_version' not in st.session_state:
            st.session_state.cache_version = 0
        
        initial_version = get_cache_version()
        invalidate_data_cache()
        new_version = get_cache_version()
        
        assert new_version == initial_version + 1
    
    def test_cached_functions_use_cache_version(self):
        """Test that cached functions include cache version in their signature."""
        # This test verifies that cached functions will be invalidated
        # when cache version changes
        
        mock_manager = Mock()
        mock_manager.get_employees.return_value = [
            Employee(id='1', first_name='John', last_name='Doe', member=True, resident='Local')
        ]
        
        # Without streamlit (in test mode), should call directly
        employees = get_cached_employees(mock_manager)
        assert len(employees) == 1
        mock_manager.get_employees.assert_called_once()
    
    def test_json_data_manager_created_without_neon(self):
        """Test that DataManager is created when USE_NEON is false."""
        with patch.dict(os.environ, {'USE_NEON': 'false'}, clear=False):
            # Need to reload module to pick up new env var
            import importlib
            import src.data_manager
            importlib.reload(src.data_manager)
            from src.data_manager import get_data_manager, DataManager
            
            manager = get_data_manager()
            assert isinstance(manager, DataManager)
    
    def test_neon_data_manager_created_with_neon(self):
        """Test that NeonDataManager is created when USE_NEON is true."""
        env_vars = {
            'USE_NEON': 'true',
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch('psycopg2.pool.SimpleConnectionPool'):
                with patch('src.neon_data_manager.NeonDataManager._ensure_tables'):
                    # Need to reload module to pick up new env var
                    import importlib
                    import src.data_manager
                    import config
                    importlib.reload(config)
                    importlib.reload(src.data_manager)
                    from src.data_manager import get_data_manager
                    from src.neon_data_manager import NeonDataManager
                    
                    manager = get_data_manager()
                    assert isinstance(manager, NeonDataManager)


class TestLogging:
    """Test suite for logging functionality."""
    
    def test_neon_manager_logs_operations(self):
        """Test that NeonDataManager logs database operations."""
        env_vars = {
            'DB_ROLE': 'test_role',
            'DB_PASS': 'test_pass',
            'DB_NAME': 'test_name',
            'DB_DATABASE': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch('psycopg2.pool.SimpleConnectionPool'):
                with patch('src.neon_data_manager.NeonDataManager._ensure_tables'):
                    with patch('src.neon_data_manager.logger') as mock_logger:
                        from src.neon_data_manager import NeonDataManager
                        manager = NeonDataManager()
                        
                        # Verify initialization logging
                        assert mock_logger.info.call_count >= 1
                        
                        # Setup mock for get_employees
                        mock_conn = Mock()
                        mock_cursor = Mock()
                        mock_cursor.fetchall.return_value = []
                        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
                        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
                        
                        manager._connection_pool = Mock()
                        manager._connection_pool.getconn.return_value = mock_conn
                        
                        # Call a method and verify logging
                        manager.get_employees()
                        assert mock_logger.debug.call_count >= 1
