"""Cache management for azvg."""

import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages local cache and git tracking."""
    
    def __init__(self, cache_root: Path, organization: str,
                 git_tracking: bool = True):
        """Initialize cache manager.
        
        Args:
            cache_root: Root cache directory.
            organization: Organization name.
            git_tracking: Enable git tracking.
        """
        self.cache_root = Path(cache_root)
        self.organization = organization
        self.org_dir = self.cache_root / organization
        self.git_tracking = git_tracking
        
        # Ensure directories exist
        self.org_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize git if enabled
        if git_tracking:
            self._init_git()
    
    def _init_git(self) -> None:
        """Initialize git repository if not exists."""
        git_dir = self.org_dir / '.git'
        if not git_dir.exists():
            logger.info(f"Initializing git repo in {self.org_dir}")
            subprocess.run(['git', 'init'], cwd=self.org_dir, check=True)
            
            # Create initial .gitignore
            gitignore = self.org_dir / '.gitignore'
            gitignore.write_text("*.tmp\n*.backup\n.DS_Store\n")
            
            subprocess.run(['git', 'add', '.gitignore'],
                         cwd=self.org_dir, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'],
                         cwd=self.org_dir, check=True)
    
    def get_project_dir(self, project: str) -> Path:
        """Get project directory.
        
        Args:
            project: Project name.
            
        Returns:
            Path to project directory.
        """
        project_dir = self.org_dir / project
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir
    
    def get_vg_dir(self, project: str) -> Path:
        """Get variable groups directory for project.
        
        Args:
            project: Project name.
            
        Returns:
            Path to variable groups directory.
        """
        vg_dir = self.get_project_dir(project) / 'variable-groups'
        vg_dir.mkdir(parents=True, exist_ok=True)
        return vg_dir
    
    def get_sf_dir(self, project: str) -> Path:
        """Get secure files directory for project.
        
        Args:
            project: Project name.
            
        Returns:
            Path to secure files directory.
        """
        sf_dir = self.get_project_dir(project) / 'secure-files'
        sf_dir.mkdir(parents=True, exist_ok=True)
        return sf_dir
    
    def save_variable_group(self, project: str, vg_data: Dict[str, Any],
                          commit_message: Optional[str] = None) -> Path:
        """Save variable group to cache.
        
        Args:
            project: Project name.
            vg_data: Variable group data.
            commit_message: Optional git commit message.
            
        Returns:
            Path to saved file.
        """
        vg_dir = self.get_vg_dir(project)
        vg_id = vg_data.get('id')
        vg_name = vg_data.get('name', 'unknown')
        
        # Sanitize name for filesystem
        safe_name = "".join(c if c.isalnum() or c in '-_' else '_'
                          for c in vg_name)
        filename = f"vg_{vg_id}_{safe_name}.json"
        filepath = vg_dir / filename
        
        # Save with pretty formatting
        with open(filepath, 'w') as f:
            json.dump(vg_data, f, indent=2, sort_keys=True)
        
        # Git commit if enabled
        if self.git_tracking:
            msg = commit_message or f"pull: {project}/{vg_name} (VG:{vg_id})"
            self._git_commit(filepath, msg)
        
        return filepath
    
    def save_secure_file(self, project: str, filename: str,
                       content: bytes, file_id: str,
                       commit_message: Optional[str] = None) -> Path:
        """Save secure file to cache.
        
        Args:
            project: Project name.
            filename: File name.
            content: File content.
            file_id: Secure file ID.
            commit_message: Optional git commit message.
            
        Returns:
            Path to saved file.
        """
        sf_dir = self.get_sf_dir(project)
        
        # Sanitize name for filesystem
        safe_name = "".join(c if c.isalnum() or c in '-_.' else '_'
                          for c in filename)
        filepath = sf_dir / f"sf_{file_id}_{safe_name}"
        
        # Save binary content
        with open(filepath, 'wb') as f:
            f.write(content)
        
        # Git commit if enabled
        if self.git_tracking:
            msg = commit_message or f"pull: {project}/{filename} (SF:{file_id})"
            self._git_commit(filepath, msg)
        
        return filepath
    
    def load_variable_group(self, project: str, 
                          vg_name: str) -> Optional[Dict[str, Any]]:
        """Load variable group from cache.
        
        Args:
            project: Project name.
            vg_name: Variable group name or pattern.
            
        Returns:
            Variable group data or None if not found.
        """
        vg_dir = self.get_vg_dir(project)
        
        # Try exact match first
        for file in vg_dir.glob("vg_*.json"):
            with open(file, 'r') as f:
                data = json.load(f)
                if data.get('name') == vg_name:
                    return data
        
        # Try pattern match
        for file in vg_dir.glob(f"*{vg_name}*.json"):
            with open(file, 'r') as f:
                return json.load(f)
        
        return None
    
    def list_cached_vgs(self, project: str) -> List[Dict[str, Any]]:
        """List all cached variable groups for project.
        
        Args:
            project: Project name.
            
        Returns:
            List of variable group summaries.
        """
        vg_dir = self.get_vg_dir(project)
        vgs = []
        
        for file in vg_dir.glob("vg_*.json"):
            with open(file, 'r') as f:
                data = json.load(f)
                vgs.append({
                    'id': data.get('id'),
                    'name': data.get('name'),
                    'file': file.name,
                    'modified': datetime.fromtimestamp(file.stat().st_mtime)
                })
        
        return vgs
    
    def list_cached_sfs(self, project: str) -> List[Dict[str, Any]]:
        """List all cached secure files for project.
        
        Args:
            project: Project name.
            
        Returns:
            List of secure file summaries.
        """
        sf_dir = self.get_sf_dir(project)
        sfs = []
        
        for file in sf_dir.glob("sf_*"):
            # Parse filename: sf_<id>_<name>
            parts = file.name.split('_', 2)
            if len(parts) >= 3:
                sfs.append({
                    'id': parts[1],
                    'name': parts[2],
                    'file': file.name,
                    'size': file.stat().st_size,
                    'modified': datetime.fromtimestamp(file.stat().st_mtime)
                })
        
        return sfs
    
    def _git_commit(self, filepath: Path, message: str) -> None:
        """Commit file to git.
        
        Args:
            filepath: File to commit.
            message: Commit message.
        """
        try:
            # Make path relative to org dir
            rel_path = filepath.relative_to(self.org_dir)
            
            subprocess.run(['git', 'add', str(rel_path)],
                         cwd=self.org_dir, check=True,
                         capture_output=True)
            subprocess.run(['git', 'commit', '-m', message],
                         cwd=self.org_dir, check=True,
                         capture_output=True)
            logger.debug(f"Git committed: {message}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Git commit failed: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get cache status.
        
        Returns:
            Status dictionary with cache information.
        """
        projects = []
        for project_dir in self.org_dir.iterdir():
            if project_dir.is_dir() and not project_dir.name.startswith('.'):
                vg_count = len(list((project_dir / 'variable-groups').glob('*.json'))) if (project_dir / 'variable-groups').exists() else 0
                sf_count = len(list((project_dir / 'secure-files').glob('sf_*'))) if (project_dir / 'secure-files').exists() else 0
                
                projects.append({
                    'name': project_dir.name,
                    'variable_groups': vg_count,
                    'secure_files': sf_count,
                })
        
        return {
            'organization': self.organization,
            'cache_dir': str(self.org_dir),
            'git_tracking': self.git_tracking,
            'projects': projects,
        }
