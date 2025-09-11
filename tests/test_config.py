"""Tests for config module."""

import unittest
import tempfile
import shutil
import os
import os.path

from azvg.config import Config


class TestConfig(unittest.TestCase):
    """Test cases for Config class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.temp_dir, '.azvg')
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_config_initialization(self):
        """Test config initialization with custom directory."""
        config = Config(self.config_dir)
        
        self.assertEqual(config.config_dir, self.config_dir)
        expected_config_file = os.path.join(self.config_dir, 'config.json')
        self.assertEqual(config.config_file, expected_config_file)
        self.assertIsNone(config.organization)
        self.assertIsNone(config.project)
    
    def test_config_save_and_load(self):
        """Test saving and loading configuration."""
        config = Config(self.config_dir)
        
        # Set values
        config.organization = 'TestOrg'
        config.project = 'TestProject'
        config.save()
        
        # Load new instance
        config2 = Config(self.config_dir)
        self.assertEqual(config2.organization, 'TestOrg')
        self.assertEqual(config2.project, 'TestProject')
    
    def test_pat_handling(self):
        """Test PAT handling including environment variables."""
        config = Config(self.config_dir)
        
        # Direct PAT
        config.set_org_config('Org1', {'pat': 'direct-pat-value'})
        self.assertEqual(config.get_pat('Org1'), 'direct-pat-value')
        
        # Environment variable reference
        os.environ['TEST_PAT'] = 'env-pat-value'
        config.set_org_config('Org2', {'pat': '${TEST_PAT}'})
        self.assertEqual(config.get_pat('Org2'), 'env-pat-value')
        
        # Cleanup
        del os.environ['TEST_PAT']
    
    def test_org_config(self):
        """Test organization configuration management."""
        config = Config(self.config_dir)
        
        org_config = {
            'pat': 'test-pat',
            'projects': {
                'Project1': {'aliases': {'prod': 'Production*'}},
                'Project2': {},
            }
        }
        
        config.set_org_config('TestOrg', org_config)
        retrieved = config.get_org_config('TestOrg')
        
        self.assertEqual(retrieved['pat'], 'test-pat')
        self.assertIn('Project1', retrieved['projects'])
        self.assertIn('Project2', retrieved['projects'])
    
    def test_default_config(self):
        """Test default configuration values."""
        config = Config(self.config_dir)
        
        # Check default structure
        self.assertIn('default', config.data)
        self.assertIn('organizations', config.data)
        self.assertIn('cache', config.data)
        
        # Check default values
        defaults = config.data['default']
        self.assertIsNone(defaults['organization'])
        self.assertIsNone(defaults['project'])
        
        # Check cache defaults
        cache_config = config.data['cache']
        self.assertEqual(cache_config['root'], self.config_dir)
        self.assertTrue(cache_config['git_tracking'])
        self.assertTrue(cache_config['auto_commit'])
    
    def test_missing_pat(self):
        """Test behavior when PAT is not configured."""
        config = Config(self.config_dir)
        
        # No organization configured
        self.assertIsNone(config.get_pat())
        
        # Organization configured but no PAT
        config.organization = 'TestOrg'
        self.assertIsNone(config.get_pat())
        
        # Organization with empty config
        config.set_org_config('TestOrg', {})
        self.assertIsNone(config.get_pat('TestOrg'))


if __name__ == '__main__':
    unittest.main()
