"""Tests for cache module."""

import json
import tempfile
from pathlib import Path

import pytest

from azvg.cache import CacheManager


def test_cache_initialization():
    """Test cache manager initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_root = Path(tmpdir)
        cache = CacheManager(cache_root, 'TestOrg', git_tracking=False)
        
        assert cache.cache_root == cache_root
        assert cache.organization == 'TestOrg'
        assert cache.org_dir == cache_root / 'TestOrg'
        assert cache.org_dir.exists()


def test_save_and_load_variable_group():
    """Test saving and loading variable groups."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_root = Path(tmpdir)
        cache = CacheManager(cache_root, 'TestOrg', git_tracking=False)
        
        vg_data = {
            'id': 123,
            'name': 'TestConfig',
            'variables': {
                'key1': {'value': 'value1'},
                'key2': {'value': 'value2', 'isSecret': True}
            }
        }
        
        # Save
        filepath = cache.save_variable_group('TestProject', vg_data)
        assert filepath.exists()
        
        # Load
        loaded = cache.load_variable_group('TestProject', 'TestConfig')
        assert loaded is not None
        assert loaded['name'] == 'TestConfig'
        assert loaded['id'] == 123


def test_save_secure_file():
    """Test saving secure files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_root = Path(tmpdir)
        cache = CacheManager(cache_root, 'TestOrg', git_tracking=False)
        
        content = b'This is binary content'
        filepath = cache.save_secure_file('TestProject', 'test.pfx',
                                         content, 'sf_123')
        
        assert filepath.exists()
        assert filepath.read_bytes() == content
        assert 'sf_123' in filepath.name
        assert 'test.pfx' in filepath.name


def test_list_cached_items():
    """Test listing cached items."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_root = Path(tmpdir)
        cache = CacheManager(cache_root, 'TestOrg', git_tracking=False)
        
        # Save some items
        vg_data = {'id': 1, 'name': 'Config1', 'variables': {}}
        cache.save_variable_group('TestProject', vg_data)
        
        vg_data = {'id': 2, 'name': 'Config2', 'variables': {}}
        cache.save_variable_group('TestProject', vg_data)
        
        cache.save_secure_file('TestProject', 'cert.pfx', 
                             b'content', 'sf_100')
        
        # List items
        vgs = cache.list_cached_vgs('TestProject')
        assert len(vgs) == 2
        assert any(vg['name'] == 'Config1' for vg in vgs)
        assert any(vg['name'] == 'Config2' for vg in vgs)
        
        sfs = cache.list_cached_sfs('TestProject')
        assert len(sfs) == 1
        assert sfs[0]['name'] == 'cert.pfx'
