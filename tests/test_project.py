"""Tests for project module."""

import tempfile
from pathlib import Path

import pytest

from azvg.config import Config
from azvg.project import ProjectContext


def test_project_context_initialization():
    """Test project context initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / '.azvg'
        config = Config(config_dir)
        config.organization = 'TestOrg'
        config.project = 'TestProject'
        
        context = ProjectContext(config)
        
        assert context.current_org == 'TestOrg'
        assert context.current_project == 'TestProject'


def test_use_project():
    """Test switching projects."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / '.azvg'
        config = Config(config_dir)
        context = ProjectContext(config)
        
        context.use_project('NewProject')
        
        assert context.current_project == 'NewProject'
        assert config.project == 'NewProject'


def test_detect_project_from_target():
    """Test project detection from target string."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / '.azvg'
        config = Config(config_dir)
        config.project = 'DefaultProject'
        config.set_org_config('TestOrg', {
            'projects': {'Project1': {}, 'Project2': {}}
        })
        
        context = ProjectContext(config)
        context._current_org = 'TestOrg'
        
        # Test colon notation
        project, item = context.detect_project_from_target('Project1:Config')
        assert project == 'Project1'
        assert item == 'Config'
        
        # Test slash notation
        project, item = context.detect_project_from_target('Project2/Config')
        assert project == 'Project2'
        assert item == 'Config'
        
        # Test default project
        project, item = context.detect_project_from_target('Config')
        assert project == 'DefaultProject'
        assert item == 'Config'
