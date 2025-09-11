"""Azure DevOps API client for azvg."""

import base64
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


class AzureDevOpsClient:
    """Client for Azure DevOps REST API."""
    
    def __init__(self, organization: str, pat: str):
        """Initialize Azure DevOps client.
        
        Args:
            organization: Azure DevOps organization name.
            pat: Personal Access Token.
        """
        self.organization = organization
        self.pat = pat
        self.base_url = f"https://dev.azure.com/{organization}"
        self.auth = HTTPBasicAuth('', pat)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects in organization.
        
        Returns:
            List of project dictionaries.
        """
        url = f"{self.base_url}/_apis/projects?api-version=7.0"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get('value', [])
    
    def get_variable_groups(self, project: str) -> List[Dict[str, Any]]:
        """Get all variable groups for a project.
        
        Args:
            project: Project name.
            
        Returns:
            List of variable group dictionaries.
        """
        url = (f"{self.base_url}/{project}/_apis/distributedtask/"
               f"variablegroups?api-version=7.0")
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get('value', [])
    
    def get_variable_group(self, project: str, 
                          group_id: int) -> Dict[str, Any]:
        """Get specific variable group.
        
        Args:
            project: Project name.
            group_id: Variable group ID.
            
        Returns:
            Variable group dictionary.
        """
        url = (f"{self.base_url}/{project}/_apis/distributedtask/"
               f"variablegroups/{group_id}?api-version=7.0")
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def update_variable_group(self, project: str, group_id: int,
                            data: Dict[str, Any]) -> Dict[str, Any]:
        """Update variable group.
        
        Args:
            project: Project name.
            group_id: Variable group ID.
            data: Variable group data.
            
        Returns:
            Updated variable group dictionary.
        """
        url = (f"{self.base_url}/{project}/_apis/distributedtask/"
               f"variablegroups/{group_id}?api-version=7.0")
        response = self.session.put(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def create_variable_group(self, project: str,
                            data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new variable group.
        
        Args:
            project: Project name.
            data: Variable group data.
            
        Returns:
            Created variable group dictionary.
        """
        url = (f"{self.base_url}/{project}/_apis/distributedtask/"
               f"variablegroups?api-version=7.0")
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def list_secure_files(self, project: str) -> List[Dict[str, Any]]:
        """List all secure files for a project.
        
        Args:
            project: Project name.
            
        Returns:
            List of secure file dictionaries.
        """
        url = (f"{self.base_url}/{project}/_apis/distributedtask/"
               f"securefiles?api-version=7.0")
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get('value', [])
    
    def download_secure_file(self, project: str, 
                           file_id: str) -> bytes:
        """Download secure file content.
        
        Args:
            project: Project name.
            file_id: Secure file ID.
            
        Returns:
            File content as bytes.
        """
        url = (f"{self.base_url}/{project}/_apis/distributedtask/"
               f"securefiles/{file_id}?download=true&api-version=7.0")
        response = self.session.get(url)
        response.raise_for_status()
        return response.content
    
    def upload_secure_file(self, project: str, name: str,
                         content: bytes) -> Dict[str, Any]:
        """Upload secure file.
        
        Args:
            project: Project name.
            name: File name.
            content: File content as bytes.
            
        Returns:
            Created secure file dictionary.
        """
        url = (f"{self.base_url}/{project}/_apis/distributedtask/"
               f"securefiles?name={name}&api-version=7.0")
        
        # Secure files use different content type
        headers = {'Content-Type': 'application/octet-stream'}
        response = self.session.post(url, data=content, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def delete_secure_file(self, project: str, file_id: str) -> None:
        """Delete secure file.
        
        Args:
            project: Project name.
            file_id: Secure file ID.
        """
        url = (f"{self.base_url}/{project}/_apis/distributedtask/"
               f"securefiles/{file_id}?api-version=7.0")
        response = self.session.delete(url)
        response.raise_for_status()
