"""Configuration management for azvg."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Manages azvg configuration."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration.
        
        Args:
            config_dir: Optional config directory path.
        """
        self.config_dir = config_dir or self._default_config_dir()
        self.config_file = self.config_dir / "config.yaml"
        self.data = self._load_config()
    
    @staticmethod
    def _default_config_dir() -> Path:
        """Get default configuration directory."""
        if os.name == 'nt':
            base = Path(os.environ.get('APPDATA', '~'))
        else:
            base = Path(os.environ.get('XDG_CONFIG_HOME', '~/.config'))
        
        return (base / '.azvg').expanduser()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Configuration dictionary.
        """
        if not self.config_file.exists():
            return self._default_config()
        
        with open(self.config_file, 'r') as f:
            return yaml.safe_load(f) or {}
    
    def _default_config(self) -> Dict[str, Any]:
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
                'root': str(self.config_dir),
                'git_tracking': True,
                'auto_commit': True,
            }
        }
    
    def save(self) -> None:
        """Save configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            yaml.dump(self.data, f, default_flow_style=False)
    
    @property
    def organization(self) -> Optional[str]:
        """Get current organization."""
        return self.data.get('default', {}).get('organization')
    
    @organization.setter
    def organization(self, value: str) -> None:
        """Set current organization."""
        if 'default' not in self.data:
            self.data['default'] = {}
        self.data['default']['organization'] = value
    
    @property
    def project(self) -> Optional[str]:
        """Get current project."""
        return self.data.get('default', {}).get('project')
    
    @project.setter
    def project(self, value: str) -> None:
        """Set current project."""
        if 'default' not in self.data:
            self.data['default'] = {}
        self.data['default']['project'] = value
    
    def get_org_config(self, org: str) -> Dict[str, Any]:
        """Get organization configuration.
        
        Args:
            org: Organization name.
            
        Returns:
            Organization configuration dictionary.
        """
        return self.data.get('organizations', {}).get(org, {})
    
    def set_org_config(self, org: str, config: Dict[str, Any]) -> None:
        """Set organization configuration.
        
        Args:
            org: Organization name.
            config: Configuration dictionary.
        """
        if 'organizations' not in self.data:
            self.data['organizations'] = {}
        self.data['organizations'][org] = config
    
    def get_pat(self, org: Optional[str] = None) -> Optional[str]:
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
