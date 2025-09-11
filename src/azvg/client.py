"""Azure DevOps API client for azvg."""

import base64
import json
import logging
try:
    # Python 2
    import urllib2
    import urlparse
except ImportError:
    # Python 3
    import urllib.request as urllib2
    import urllib.parse as urlparse


logger = logging.getLogger(__name__)


class AzureDevOpsClient(object):
    """Client for Azure DevOps REST API."""
    
    def __init__(self, organization, pat):
        """Initialize Azure DevOps client.
        
        Args:
            organization: Azure DevOps organization name.
            pat: Personal Access Token.
        """
        self.organization = organization
        self.pat = pat
        self.base_url = "https://dev.azure.com/{0}".format(organization)
        
        # Create basic auth header (empty username, PAT as password)
        auth_string = base64.b64encode(
            ":{0}".format(pat).encode('utf-8')
        ).decode('ascii')
        self.auth_header = "Basic {0}".format(auth_string)
    
    def _make_request(self, url, method='GET', data=None):
        """Make HTTP request to Azure DevOps API.
        
        Args:
            url: Request URL.
            method: HTTP method.
            data: Request data (for POST/PUT).
            
        Returns:
            Parsed JSON response.
            
        Raises:
            Exception: If request fails.
        """
        request = urllib2.Request(url)
        request.add_header("Authorization", self.auth_header)
        request.add_header("Content-Type", "application/json")
        request.add_header("Accept", "application/json")
        
        if data and method in ['POST', 'PUT']:
            request.add_data(json.dumps(data))
            
        # Set method for non-GET requests
        if method != 'GET':
            request.get_method = lambda: method
        
        try:
            response = urllib2.urlopen(request)
            response_text = response.read()
            return json.loads(response_text) if response_text else {}
        except urllib2.HTTPError as e:
            error_msg = "HTTP {0}: {1}".format(e.code, e.msg)
            try:
                error_detail = e.read()
                if error_detail:
                    error_data = json.loads(error_detail)
                    if 'message' in error_data:
                        error_msg = "{0} - {1}".format(
                            error_msg, error_data['message'])
            except (ValueError, KeyError):
                pass
            raise Exception(error_msg)
        except urllib2.URLError as e:
            raise Exception("URL Error: {0}".format(str(e.reason)))
        except ValueError as e:  # JSON decode errors
            raise Exception("Invalid JSON response: {0}".format(str(e)))
    
    def list_projects(self):
        """List all projects in organization.
        
        Returns:
            List of project dictionaries.
        """
        url = "{0}/_apis/projects?api-version=7.0".format(self.base_url)
        response = self._make_request(url)
        return response.get('value', [])
    
    def get_variable_groups(self, project):
        """Get all variable groups for a project.
        
        Args:
            project: Project name.
            
        Returns:
            List of variable group dictionaries.
        """
        url = ("{0}/{1}/_apis/distributedtask/"
               "variablegroups?api-version=7.0").format(self.base_url, project)
        response = self._make_request(url)
        return response.get('value', [])
    
    def get_variable_group(self, project, group_id):
        """Get specific variable group.
        
        Args:
            project: Project name.
            group_id: Variable group ID.
            
        Returns:
            Variable group dictionary.
        """
        url = ("{0}/{1}/_apis/distributedtask/"
               "variablegroups/{2}?api-version=7.0").format(
                   self.base_url, project, group_id)
        return self._make_request(url)
    
    def update_variable_group(self, project, group_id, data):
        """Update variable group.
        
        Args:
            project: Project name.
            group_id: Variable group ID.
            data: Variable group data.
            
        Returns:
            Updated variable group dictionary.
        """
        url = ("{0}/{1}/_apis/distributedtask/"
               "variablegroups/{2}?api-version=7.0").format(
                   self.base_url, project, group_id)
        return self._make_request(url, method='PUT', data=data)
    
    def create_variable_group(self, project, data):
        """Create new variable group.
        
        Args:
            project: Project name.
            data: Variable group data.
            
        Returns:
            Created variable group dictionary.
        """
        url = ("{0}/{1}/_apis/distributedtask/"
               "variablegroups?api-version=7.0").format(self.base_url, project)
        return self._make_request(url, method='POST', data=data)
    
    def list_secure_files(self, project):
        """List all secure files for a project.
        
        Args:
            project: Project name.
            
        Returns:
            List of secure file dictionaries.
        """
        url = ("{0}/{1}/_apis/distributedtask/"
               "securefiles?api-version=7.0").format(self.base_url, project)
        response = self._make_request(url)
        return response.get('value', [])
    
    def download_secure_file(self, project, file_id):
        """Download secure file content.
        
        Args:
            project: Project name.
            file_id: Secure file ID.
            
        Returns:
            File content as bytes.
        """
        url = ("{0}/{1}/_apis/distributedtask/"
               "securefiles/{2}?download=true&api-version=7.0").format(
                   self.base_url, project, file_id)
        
        request = urllib2.Request(url)
        request.add_header("Authorization", self.auth_header)
        
        try:
            response = urllib2.urlopen(request)
            return response.read()
        except urllib2.HTTPError as e:
            raise Exception("HTTP {0}: {1}".format(e.code, e.msg))
        except urllib2.URLError as e:
            raise Exception("URL Error: {0}".format(str(e.reason)))
    
    def upload_secure_file(self, project, name, content):
        """Upload secure file.
        
        Args:
            project: Project name.
            name: File name.
            content: File content as bytes.
            
        Returns:
            Created secure file dictionary.
        """
        url = ("{0}/{1}/_apis/distributedtask/"
               "securefiles?name={2}&api-version=7.0").format(
                   self.base_url, project, name)
        
        request = urllib2.Request(url, data=content)
        request.add_header("Authorization", self.auth_header)
        request.add_header("Content-Type", "application/octet-stream")
        request.get_method = lambda: 'POST'
        
        try:
            response = urllib2.urlopen(request)
            response_text = response.read()
            return json.loads(response_text) if response_text else {}
        except urllib2.HTTPError as e:
            raise Exception("HTTP {0}: {1}".format(e.code, e.msg))
        except urllib2.URLError as e:
            raise Exception("URL Error: {0}".format(str(e.reason)))
    
    def delete_secure_file(self, project, file_id):
        """Delete secure file.
        
        Args:
            project: Project name.
            file_id: Secure file ID.
        """
        url = ("{0}/{1}/_apis/distributedtask/"
               "securefiles/{2}?api-version=7.0").format(
                   self.base_url, project, file_id)
        
        request = urllib2.Request(url)
        request.add_header("Authorization", self.auth_header)
        request.get_method = lambda: 'DELETE'
        
        try:
            urllib2.urlopen(request)
        except urllib2.HTTPError as e:
            raise Exception("HTTP {0}: {1}".format(e.code, e.msg))
        except urllib2.URLError as e:
            raise Exception("URL Error: {0}".format(str(e.reason)))
