"""Tests for project module."""

import unittest
import tempfile
import shutil
import os.path

from azvg.config import Config
from azvg.project import ProjectContext


class TestProjectContext(unittest.TestCase):
    """Test cases for ProjectContext class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.temp_dir, '.azvg')
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_project_context_initialization(self):
        """Test project context initialization."""
        config = Config(self.config_dir)
        config.organization = 'TestOrg'
        config.project = 'TestProject'
        
        context = ProjectContext(config)
        
        self.assertEqual(context.current_org, 'TestOrg')
        self.assertEqual(context.current_project, 'TestProject')
    
    def test_use_project(self):
        """Test switching projects."""
        config = Config(self.config_dir)
        context = ProjectContext(config)
        
        context.use_project('NewProject')
        
        self.assertEqual(context.current_project, 'NewProject')
        self.assertEqual(config.project, 'NewProject')
    
    def test_detect_project_from_target(self):
        """Test project detection from target string."""
        config = Config(self.config_dir)
        config.project = 'DefaultProject'
        config.set_org_config('TestOrg', {
            'projects': {'Project1': {}, 'Project2': {}}
        })
        
        context = ProjectContext(config)
        context._current_org = 'TestOrg'
        
        # Test colon notation
        project, item = context.detect_project_from_target('Project1:Config')
        self.assertEqual(project, 'Project1')
        self.assertEqual(item, 'Config')
        
        # Test slash notation
        project, item = context.detect_project_from_target('Project2/Config')
        self.assertEqual(project, 'Project2')
        self.assertEqual(item, 'Config')
        
        # Test default project
        project, item = context.detect_project_from_target('Config')
        self.assertEqual(project, 'DefaultProject')
        self.assertEqual(item, 'Config')
    
    def test_list_projects(self):
        """Test listing projects from config."""
        config = Config(self.config_dir)
        config.organization = 'TestOrg'
        config.set_org_config('TestOrg', {
            'projects': {
                'Project1': {'description': 'First project'},
                'Project2': {'description': 'Second project'},
                'Project3': {}
            }
        })
        
        context = ProjectContext(config)
        projects = context.list_projects()
        
        self.assertEqual(len(projects), 3)
        self.assertIn('Project1', projects)
        self.assertIn('Project2', projects)
        self.assertIn('Project3', projects)
    
    def test_get_project_info(self):
        """Test getting project information."""
        config = Config(self.config_dir)
        config.organization = 'TestOrg'
        config.project = 'Project1'
        config.set_org_config('TestOrg', {
            'projects': {
                'Project1': {
                    'description': 'Test project',
                    'default_type': 'vg'
                }
            }
        })
        
        context = ProjectContext(config)
        
        # Test with default project
        info = context.get_project_info()
        self.assertEqual(info['description'], 'Test project')
        self.assertEqual(info['default_type'], 'vg')
        
        # Test with specified project
        info = context.get_project_info('Project1')
        self.assertEqual(info['description'], 'Test project')
    
    def test_is_project(self):
        """Test project existence checking."""
        config = Config(self.config_dir)
        config.organization = 'TestOrg'
        config.set_org_config('TestOrg', {
            'projects': {'Project1': {}, 'Project2': {}}
        })
        
        context = ProjectContext(config)
        
        self.assertTrue(context.is_project('Project1'))
        self.assertTrue(context.is_project('Project2'))
        self.assertFalse(context.is_project('NonExistent'))
    
    def test_get_project_cache_dir(self):
        """Test getting project cache directory path."""
        config = Config(self.config_dir)
        config.organization = 'TestOrg'
        config.project = 'TestProject'
        
        context = ProjectContext(config)
        
        # Test with default project and org
        cache_dir = context.get_project_cache_dir()
        expected = os.path.join(config.data['cache']['root'], 
                               'TestOrg', 'TestProject')
        self.assertEqual(cache_dir, expected)
        
        # Test with specified project and org
        cache_dir = context.get_project_cache_dir('OtherProject', 'OtherOrg')
        expected = os.path.join(config.data['cache']['root'], 
                               'OtherOrg', 'OtherProject')
        self.assertEqual(cache_dir, expected)
    
    def test_get_project_cache_dir_error(self):
        """Test error handling when org/project not specified."""
        config = Config(self.config_dir)
        context = ProjectContext(config)
        
        # Should raise ValueError when org/project not set
        with self.assertRaises(ValueError):
            context.get_project_cache_dir()
    
    def test_properties(self):
        """Test property setters and getters."""
        config = Config(self.config_dir)
        context = ProjectContext(config)
        
        # Test setting current project
        context.current_project = 'NewProject'
        self.assertEqual(context.current_project, 'NewProject')
        self.assertEqual(config.project, 'NewProject')
        
        # Test current org
        config.organization = 'TestOrg'
        context = ProjectContext(config)  # Reinitialize
        self.assertEqual(context.current_org, 'TestOrg')


if __name__ == '__main__':
    unittest.main()
