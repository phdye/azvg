"""Tests for cache module."""

import unittest
import json
import tempfile
import shutil
import os
import os.path

from azvg.cache import CacheManager


class TestCacheManager(unittest.TestCase):
    """Test cases for CacheManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_cache_initialization(self):
        """Test cache manager initialization."""
        cache = CacheManager(self.temp_dir, 'TestOrg', git_tracking=False)
        
        self.assertEqual(cache.cache_root, self.temp_dir)
        self.assertEqual(cache.organization, 'TestOrg')
        
        expected_org_dir = os.path.join(self.temp_dir, 'TestOrg')
        self.assertEqual(cache.org_dir, expected_org_dir)
        self.assertTrue(os.path.exists(cache.org_dir))
    
    def test_save_and_load_variable_group(self):
        """Test saving and loading variable groups."""
        cache = CacheManager(self.temp_dir, 'TestOrg', git_tracking=False)
        
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
        self.assertTrue(os.path.exists(filepath))
        
        # Load
        loaded = cache.load_variable_group('TestProject', 'TestConfig')
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded['name'], 'TestConfig')
        self.assertEqual(loaded['id'], 123)
    
    def test_save_secure_file(self):
        """Test saving secure files."""
        cache = CacheManager(self.temp_dir, 'TestOrg', git_tracking=False)
        
        test_content = b'This is test file content'
        filename = 'test.txt'
        file_id = '456'
        
        # Save
        filepath = cache.save_secure_file('TestProject', filename, 
                                        test_content, file_id)
        self.assertTrue(os.path.exists(filepath))
        
        # Verify content
        with open(filepath, 'rb') as f:
            saved_content = f.read()
        self.assertEqual(saved_content, test_content)
    
    def test_list_cached_items(self):
        """Test listing cached variable groups and secure files."""
        cache = CacheManager(self.temp_dir, 'TestOrg', git_tracking=False)
        
        # Save some test data
        vg_data = {
            'id': 789,
            'name': 'ProdConfig',
            'variables': {'env': {'value': 'production'}}
        }
        cache.save_variable_group('TestProject', vg_data)
        
        test_content = b'Secure file content'
        cache.save_secure_file('TestProject', 'cert.pfx', 
                             test_content, '101')
        
        # List variable groups
        vgs = cache.list_cached_vgs('TestProject')
        self.assertEqual(len(vgs), 1)
        self.assertEqual(vgs[0]['name'], 'ProdConfig')
        self.assertEqual(vgs[0]['id'], 789)
        
        # List secure files
        sfs = cache.list_cached_sfs('TestProject')
        self.assertEqual(len(sfs), 1)
        self.assertEqual(sfs[0]['name'], 'cert.pfx')
        self.assertEqual(sfs[0]['id'], '101')
    
    def test_get_status(self):
        """Test getting cache status."""
        cache = CacheManager(self.temp_dir, 'TestOrg', git_tracking=False)
        
        # Add some test data
        vg_data = {'id': 1, 'name': 'Config1', 'variables': {}}
        cache.save_variable_group('Project1', vg_data)
        
        test_content = b'test'
        cache.save_secure_file('Project1', 'file1.txt', test_content, '1')
        
        # Get status
        status = cache.get_status()
        
        self.assertEqual(status['organization'], 'TestOrg')
        self.assertEqual(status['cache_dir'], cache.org_dir)
        self.assertFalse(status['git_tracking'])
        
        # Check projects
        self.assertEqual(len(status['projects']), 1)
        project = status['projects'][0]
        self.assertEqual(project['name'], 'Project1')
        self.assertEqual(project['variable_groups'], 1)
        self.assertEqual(project['secure_files'], 1)
    
    def test_project_directory_creation(self):
        """Test project directory creation."""
        cache = CacheManager(self.temp_dir, 'TestOrg', git_tracking=False)
        
        # Get project directory (should create it)
        proj_dir = cache.get_project_dir('NewProject')
        self.assertTrue(os.path.exists(proj_dir))
        self.assertTrue(os.path.isdir(proj_dir))
        
        # Get VG directory (should create it)
        vg_dir = cache.get_vg_dir('NewProject')
        self.assertTrue(os.path.exists(vg_dir))
        expected_vg_dir = os.path.join(proj_dir, 'variable-groups')
        self.assertEqual(vg_dir, expected_vg_dir)
        
        # Get SF directory (should create it)
        sf_dir = cache.get_sf_dir('NewProject')
        self.assertTrue(os.path.exists(sf_dir))
        expected_sf_dir = os.path.join(proj_dir, 'secure-files')
        self.assertEqual(sf_dir, expected_sf_dir)
    
    def test_variable_group_pattern_matching(self):
        """Test variable group pattern matching for loading."""
        cache = CacheManager(self.temp_dir, 'TestOrg', git_tracking=False)
        
        # Save multiple VGs
        vg1 = {'id': 1, 'name': 'ProductionConfig', 'variables': {}}
        vg2 = {'id': 2, 'name': 'StagingConfig', 'variables': {}}
        
        cache.save_variable_group('TestProject', vg1)
        cache.save_variable_group('TestProject', vg2)
        
        # Test exact match
        loaded = cache.load_variable_group('TestProject', 'ProductionConfig')
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded['name'], 'ProductionConfig')
        
        # Test pattern match
        loaded = cache.load_variable_group('TestProject', 'Production')
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded['name'], 'ProductionConfig')
        
        # Test no match
        loaded = cache.load_variable_group('TestProject', 'NonExistent')
        self.assertIsNone(loaded)


if __name__ == '__main__':
    unittest.main()
