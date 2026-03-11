"""
Tests for MemorySystem
"""

import pytest
from core.memory import MemorySystem


@pytest.mark.asyncio
async def test_memory_initialization():
    """Test memory system initializes"""
    memory = MemorySystem({'db_path': ':memory:', 'collection_name': 'test'})
    await memory.initialize()
    
    assert memory.client is not None
    assert memory.collection is not None
    
    await memory.shutdown()


@pytest.mark.asyncio
async def test_store_context(mock_memory):
    """Test storing context"""
    await mock_memory.store_context("test-agent", {
        "request": "test request",
        "result": "test result"
    })
    
    # Should not raise exception
    assert True


@pytest.mark.asyncio
async def test_store_result(mock_memory):
    """Test storing result"""
    await mock_memory.store_result("test-agent", {
        "status": "success",
        "output": "test output"
    })
    
    # Should not raise exception
    assert True


@pytest.mark.asyncio
async def test_search(mock_memory):
    """Test memory search"""
    # Store some data
    await mock_memory.store_context("test-agent", {
        "request": "create login form",
        "result": "form created"
    })
    
    # Search
    results = await mock_memory.search("login", limit=5)
    
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_search_empty(mock_memory):
    """Test search with no results"""
    results = await mock_memory.search("nonexistent query", limit=5)
    
    assert isinstance(results, list)
    assert len(results) == 0
