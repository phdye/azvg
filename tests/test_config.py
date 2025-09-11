"""Tests for config module."""

import tempfile
from pathlib import Path
import yaml

import pytest

from azvg.config import Config


def test_config_initialization():
    """Test config initialization with custom directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / '.azvg'
        config = Config(config_dir)
        
        assert config.config_dir == config_dir
        assert config.config_file == config_dir / 'config.yaml'
        assert config.organization is None
        assert config.project is None


def test_config_save_and_load():
    """Test saving and loading configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / '.azvg'
        config = Config(config_dir)
        
        # Set values
        config.organization = 'TestOrg'
        config.project = 'TestProject'
        config.save()
        
        # Load new instance
        config2 = Config(config_dir)
        assert config2.organization == 'TestOrg'
        assert config2.project == 'TestProject'


def test_pat_handling():
    """Test PAT handling including environment variables."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / '.azvg'
        config = Config(config_dir)
        
        # Direct PAT
        config.set_org_config('Org1', {'pat': 'direct-pat-value'})
        assert config.get_pat('Org1') == 'direct-pat-value'
        
        # Environment variable reference
        import os
        os.environ['TEST_PAT'] = 'env-pat-value'
        config.set_org_config('Org2', {'pat': '${TEST_PAT}'})
        assert config.get_pat('Org2') == 'env-pat-value'
        
        # Cleanup
        del os.environ['TEST_PAT']


def test_org_config():
    """Test organization configuration management."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / '.azvg'
        config = Config(config_dir)
        
        org_config = {
            'pat': 'test-pat',
            'projects': {
                'Project1': {'aliases': {'prod': 'Production*'}},
                'Project2': {},
            }
        }
        
        config.set_org_config('TestOrg', org_config)
        retrieved = config.get_org_config('TestOrg')
        
        assert retrieved['pat'] == 'test-pat'
        assert 'Project1' in retrieved['projects']
        assert 'Project2' in retrieved['projects']
