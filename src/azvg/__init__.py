"""Azure DevOps Variable Groups Manager.

A tool for managing Azure DevOps Library items locally with git tracking.

License: MIT OR Apache-2.0
"""

__version__ = "0.1.0"
__author__ = "Azure DevOps Library Manager"

from .config import Config
from .client import AzureDevOpsClient
from .cache import CacheManager
from .project import ProjectContext

__all__ = [
    "Config",
    "AzureDevOpsClient", 
    "CacheManager",
    "ProjectContext",
]
