"""Cache management for azvg."""

import json
import subprocess
import logging
import os
import os.path
import time
import glob


logger = logging.getLogger(__name__)


class CacheManager(object):
    """Manages local cache and git tracking."""
    
    def __init__(self, cache_root, organization, git_tracking=True):
        """Initialize cache manager.
        
        Args:
            cache_root: Root cache directory path string.
            organization: Organization name.
            git_tracking: Enable git tracking.
        """
        self.cache_root = cache_root
        self.organization = organization
        self.org_dir = os.path.join(cache_root, organization)
        self.git_tracking = git_tracking
        
        # Ensure directories exist
        if not os.path.exists(self.org_dir):
            os.makedirs(self.org_dir)
        
        # Initialize git if enabled
        if git_tracking:
            self._init_git()
    
    def _init_git(self):
        """Initialize git repository if not exists."""
        git_dir = os.path.join(self.org_dir, '.git')
        if not os.path.exists(git_dir):
            logger.info("Initializing git repo in {0}".format(self.org_dir))
            
            # Initialize git repository
            ret = subprocess.call(['git', 'init'], cwd=self.org_dir)
            if ret != 0:
                logger.warning("Failed to initialize git repository")
                return
            
            # Create initial .gitignore
            gitignore_path = os.path.join(self.org_dir, '.gitignore')
            with open(gitignore_path, 'w') as f:
                f.write("*.tmp\n*.backup\n.DS_Store\n")
            
            # Initial commit
            subprocess.call(['git', 'add', '.gitignore'], cwd=self.org_dir)
            subprocess.call(['git', 'commit', '-m', 'Initial commit'], 
                          cwd=self.org_dir)
    
    def get_project_dir(self, project):
        """Get project directory.
        
        Args:
            project: Project name.
            
        Returns:
            Path to project directory.
        """
        project_dir = os.path.join(self.org_dir, project)
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
        return project_dir
    
    def get_vg_dir(self, project):
        """Get variable groups directory for project.
        
        Args:
            project: Project name.
            
        Returns:
            Path to variable groups directory.
        """
        vg_dir = os.path.join(self.get_project_dir(project), 
                             'variable-groups')
        if not os.path.exists(vg_dir):
            os.makedirs(vg_dir)
        return vg_dir
    
    def get_sf_dir(self, project):
        """Get secure files directory for project.
        
        Args:
            project: Project name.
            
        Returns:
            Path to secure files directory.
        """
        sf_dir = os.path.join(self.get_project_dir(project), 'secure-files')
        if not os.path.exists(sf_dir):
            os.makedirs(sf_dir)
        return sf_dir
    
    def save_variable_group(self, project, vg_data, commit_message=None):
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
        filename = "vg_{0}_{1}.json".format(vg_id, safe_name)
        filepath = os.path.join(vg_dir, filename)
        
        # Save with pretty formatting
        with open(filepath, 'w') as f:
            json.dump(vg_data, f, indent=2, sort_keys=True)
        
        # Git commit if enabled
        if self.git_tracking:
            msg = commit_message or "pull: {0}/{1} (VG:{2})".format(
                project, vg_name, vg_id)
            self._git_commit(filepath, msg)
        
        return filepath
    
    def save_secure_file(self, project, filename, content, file_id,
                       commit_message=None):
        """Save secure file to cache.
        
        Args:
            project: Project name.
            filename: File name.
            content: File content as bytes.
            file_id: Secure file ID.
            commit_message: Optional git commit message.
            
        Returns:
            Path to saved file.
        """
        sf_dir = self.get_sf_dir(project)
        
        # Sanitize name for filesystem
        safe_name = "".join(c if c.isalnum() or c in '-_.' else '_'
                          for c in filename)
        cache_filename = "sf_{0}_{1}".format(file_id, safe_name)
        filepath = os.path.join(sf_dir, cache_filename)
        
        # Save binary content
        with open(filepath, 'wb') as f:
            f.write(content)
        
        # Git commit if enabled
        if self.git_tracking:
            msg = commit_message or "pull: {0}/{1} (SF:{2})".format(
                project, filename, file_id)
            self._git_commit(filepath, msg)
        
        return filepath
    
    def load_variable_group(self, project, vg_name):
        """Load variable group from cache.
        
        Args:
            project: Project name.
            vg_name: Variable group name or pattern.
            
        Returns:
            Variable group data or None if not found.
        """
        vg_dir = self.get_vg_dir(project)
        
        # Try exact match first
        pattern = os.path.join(vg_dir, "vg_*.json")
        for file_path in glob.glob(pattern):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if data.get('name') == vg_name:
                        return data
            except (IOError, ValueError):
                continue
        
        # Try pattern match
        pattern = os.path.join(vg_dir, "*{0}*.json".format(vg_name))
        for file_path in glob.glob(pattern):
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except (IOError, ValueError):
                continue
        
        return None
    
    def list_cached_vgs(self, project):
        """List all cached variable groups for project.
        
        Args:
            project: Project name.
            
        Returns:
            List of variable group summaries.
        """
        vg_dir = self.get_vg_dir(project)
        vgs = []
        
        pattern = os.path.join(vg_dir, "vg_*.json")
        for file_path in glob.glob(pattern):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                stat = os.stat(file_path)
                vgs.append({
                    'id': data.get('id'),
                    'name': data.get('name'),
                    'file': os.path.basename(file_path),
                    'modified': time.ctime(stat.st_mtime)
                })
            except (IOError, ValueError):
                continue
        
        return vgs
    
    def list_cached_sfs(self, project):
        """List all cached secure files for project.
        
        Args:
            project: Project name.
            
        Returns:
            List of secure file summaries.
        """
        sf_dir = self.get_sf_dir(project)
        sfs = []
        
        pattern = os.path.join(sf_dir, "sf_*")
        for file_path in glob.glob(pattern):
            filename = os.path.basename(file_path)
            
            # Parse filename: sf_<id>_<name>
            parts = filename.split('_', 2)
            if len(parts) >= 3:
                stat = os.stat(file_path)
                sfs.append({
                    'id': parts[1],
                    'name': parts[2],
                    'file': filename,
                    'size': stat.st_size,
                    'modified': time.ctime(stat.st_mtime)
                })
        
        return sfs
    
    def _git_commit(self, filepath, message):
        """Commit file to git.
        
        Args:
            filepath: File to commit.
            message: Commit message.
        """
        try:
            # Make path relative to org dir
            rel_path = os.path.relpath(filepath, self.org_dir)
            
            # Git add and commit
            ret1 = subprocess.call(['git', 'add', rel_path], 
                                 cwd=self.org_dir)
            ret2 = subprocess.call(['git', 'commit', '-m', message], 
                                 cwd=self.org_dir)
            
            if ret1 == 0 and ret2 == 0:
                logger.debug("Git committed: {0}".format(message))
            else:
                logger.warning("Git commit failed")
        except OSError as e:
            logger.warning("Git commit failed: {0}".format(str(e)))
    
    def get_status(self):
        """Get cache status.
        
        Returns:
            Status dictionary with cache information.
        """
        projects = []
        
        if os.path.exists(self.org_dir):
            for item in os.listdir(self.org_dir):
                project_dir = os.path.join(self.org_dir, item)
                if os.path.isdir(project_dir) and not item.startswith('.'):
                    
                    # Count variable groups
                    vg_dir = os.path.join(project_dir, 'variable-groups')
                    vg_count = 0
                    if os.path.exists(vg_dir):
                        vg_count = len(glob.glob(
                            os.path.join(vg_dir, '*.json')))
                    
                    # Count secure files
                    sf_dir = os.path.join(project_dir, 'secure-files')
                    sf_count = 0
                    if os.path.exists(sf_dir):
                        sf_count = len(glob.glob(
                            os.path.join(sf_dir, 'sf_*')))
                    
                    projects.append({
                        'name': item,
                        'variable_groups': vg_count,
                        'secure_files': sf_count,
                    })
        
        return {
            'organization': self.organization,
            'cache_dir': self.org_dir,
            'git_tracking': self.git_tracking,
            'projects': projects,
        }
