"""Configuration management for azvg."""

import os
import os.path
import json


class Config(object):
    """Manages azvg configuration."""
    
    def __init__(self, config_dir=None):
        """Initialize configuration.
        
        Args:
            config_dir: Optional config directory path.
        """
        self.config_dir = config_dir or self._default_config_dir()
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.data = self._load_config()
    
    @staticmethod
    def _default_config_dir():
        """Get default configuration directory."""
        # Use ~/.azvg as per design document
        return os.path.expanduser('~/.azvg')
    
    def _load_config(self):
        """Load configuration from file.
        
        Returns:
            Configuration dictionary.
        """
        if not os.path.exists(self.config_file):
            return self._default_config()
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f) or {}
        except (IOError, ValueError) as e:
            # Return default config if file is corrupted
            return self._default_config()
    
    def _default_config(self):
        """Return default configuration.
        
        Returns:
            Default configuration dictionary.
        """
        return {
            'default': {
                'organization': None,
                'project': None,
            },
            'organizations': {},
            'cache': {
                'root': self.config_dir,
                'git_tracking': True,
                'auto_commit': True,
            }
        }
    
    def save(self):
        """Save configuration to file."""
        # Ensure config directory exists
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        with open(self.config_file, 'w') as f:
            json.dump(self.data, f, indent=2, sort_keys=True)
    
    @property
    def organization(self):
        """Get current organization."""
        return self.data.get('default', {}).get('organization')
    
    @organization.setter
    def organization(self, value):
        """Set current organization."""
        if 'default' not in self.data:
            self.data['default'] = {}
        self.data['default']['organization'] = value
    
    @property
    def project(self):
        """Get current project."""
        return self.data.get('default', {}).get('project')
    
    @project.setter
    def project(self, value):
        """Set current project."""
        if 'default' not in self.data:
            self.data['default'] = {}
        self.data['default']['project'] = value
    
    def get_org_config(self, org):
        """Get organization configuration.
        
        Args:
            org: Organization name.
            
        Returns:
            Organization configuration dictionary.
        """
        return self.data.get('organizations', {}).get(org, {})
    
    def set_org_config(self, org, config):
        """Set organization configuration.
        
        Args:
            org: Organization name.
            config: Configuration dictionary.
        """
        if 'organizations' not in self.data:
            self.data['organizations'] = {}
        self.data['organizations'][org] = config
    
    def get_pat(self, org=None):
        """Get PAT for organization.
        
        Args:
            org: Organization name (uses default if not provided).
            
        Returns:
            Personal Access Token or None.
        """
        org = org or self.organization
        if not org:
            return None
        
        pat = self.get_org_config(org).get('pat')
        
        # Support environment variable references
        if pat and pat.startswith('${') and pat.endswith('}'):
            env_var = pat[2:-1]
            return os.environ.get(env_var)
        
        return pat
