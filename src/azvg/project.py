"""Project context management for azvg."""

from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path
import logging

from .config import Config

logger = logging.getLogger(__name__)


class ProjectContext:
    """Manages project context and operations."""
    
    def __init__(self, config: Config):
        """Initialize project context.
        
        Args:
            config: Configuration instance.
        """
        self.config = config
        self._current_project = config.project
        self._current_org = config.organization
    
    @property
    def current_project(self) -> Optional[str]:
        """Get current project."""
        return self._current_project
    
    @current_project.setter
    def current_project(self, value: str) -> None:
        """Set current project."""
        self._current_project = value
        self.config.project = value
        self.config.save()
    
    @property
    def current_org(self) -> Optional[str]:
        """Get current organization."""
        return self._current_org
    
    def use_project(self, project: str) -> None:
        """Switch to specified project.
        
        Args:
            project: Project name.
        """
        logger.info(f"Switching to project: {project}")
        self.current_project = project
    
    def list_projects(self, org: Optional[str] = None) -> List[str]:
        """List available projects.
        
        Args:
            org: Organization name (uses current if not provided).
            
        Returns:
            List of project names.
        """
        org = org or self.current_org
        if not org:
            return []
        
        org_config = self.config.get_org_config(org)
        projects = org_config.get('projects', {})
        return list(projects.keys())
    
    def get_project_info(self, project: Optional[str] = None) -> Dict[str, Any]:
        """Get project information.
        
        Args:
            project: Project name (uses current if not provided).
            
        Returns:
            Project information dictionary.
        """
        project = project or self.current_project
        if not project or not self.current_org:
            return {}
        
        org_config = self.config.get_org_config(self.current_org)
        return org_config.get('projects', {}).get(project, {})
    
    def detect_project_from_target(self, target: str) -> Tuple[str, str]:
        """Auto-detect project from target notation.
        
        Args:
            target: Target string (may include project notation).
            
        Returns:
            Tuple of (project, item).
        """
        # Support explicit project notation
        if ':' in target:
            # "Project-A:Config" notation
            project, item = target.split(':', 1)
            return project, item
        elif '/' in target:
            # "Project-A/Config" notation
            parts = target.split('/', 1)
            if self.is_project(parts[0]):
                return parts[0], parts[1]
        
        # Use default project
        return self.current_project or '', target
    
    def is_project(self, name: str) -> bool:
        """Check if name is a valid project.
        
        Args:
            name: Name to check.
            
        Returns:
            True if name is a valid project.
        """
        return name in self.list_projects()
    
    def get_project_cache_dir(self, project: Optional[str] = None,
                             org: Optional[str] = None) -> Path:
        """Get cache directory for project.
        
        Args:
            project: Project name (uses current if not provided).
            org: Organization name (uses current if not provided).
            
        Returns:
            Path to project cache directory.
        """
        org = org or self.current_org
        project = project or self.current_project
        
        if not org or not project:
            raise ValueError("Organization and project must be specified")
        
        cache_root = Path(self.config.data['cache']['root'])
        return cache_root / org / project
