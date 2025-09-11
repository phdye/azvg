#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Variable Group Utilities Module

Provides common functions for handling variable groups with support for:
- Both ID and name-based references
- Both file naming conventions (vg_<id>_<name>.json and <name>.json)
- Bidirectional unique mapping between IDs and names
- Pattern matching with glob and regex support
"""

import os
import json
import re
import fnmatch

def sanitize_filename(name, preserve_exact=True):
    """
    Sanitize a variable group name for use in a filename.
    
    Args:
        name: Variable group name
        preserve_exact: If True, preserve exact name except OS-forbidden chars
    
    Returns:
        str: Sanitized filename
    """
    if preserve_exact:
        # Only replace characters forbidden by the OS
        # Windows forbidden: < > : " / \ | ? *
        # Unix/Linux forbidden: / and null
        forbidden_chars = '<>:"/\\|?*' if os.name == 'nt' else '/'
        
        # Replace forbidden characters with underscore
        sanitized = name
        for char in forbidden_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Remove control characters and null bytes
        sanitized = ''.join(c for c in sanitized if ord(c) >= 32)
        
        # Trim trailing dots and spaces (Windows requirement)
        if os.name == 'nt':
            sanitized = sanitized.rstrip('. ')
        
        return sanitized
    else:
        # Legacy behavior - replace spaces and slashes
        safe_name = name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c in ('_', '-'))
        return safe_name

def parse_vg_filename(filename):
    """
    Parse a variable group filename to extract ID and name.
    
    Supports formats:
    - vg_<id>_<name>.json
    - <name>.json
    
    Returns:
        tuple: (id, name) or (None, name) if no ID in filename
    """
    # Remove .json extension if present
    if filename.endswith('.json'):
        filename = filename[:-5]
    
    # Check for vg_<id>_<name> pattern
    vg_pattern = r'^vg_(\d+)_(.+)$'
    match = re.match(vg_pattern, filename)
    
    if match:
        vg_id = match.group(1)
        vg_name = match.group(2)
        # Don't auto-replace underscores - the name is exact
        return (vg_id, vg_name)
    else:
        # Just a name
        return (None, filename)

def build_vg_mapping(directory='variable-groups'):
    """
    Build a bidirectional mapping between variable group IDs and names.
    
    Args:
        directory: Directory containing variable group JSON files
    
    Returns:
        tuple: (id_to_name, name_to_id) dictionaries
    """
    id_to_name = {}
    name_to_id = {}
    
    if not os.path.exists(directory):
        return id_to_name, name_to_id
    
    for filename in os.listdir(directory):
        if not filename.endswith('.json'):
            continue
        
        filepath = os.path.join(directory, filename)
        
        # Try to load JSON to get actual ID and name
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                actual_id = str(data.get('id', ''))
                actual_name = data.get('name', '')
                
                if actual_id and actual_name:
                    vg_id = actual_id
                    vg_name = actual_name
                else:
                    # Fall back to filename parsing
                    file_id, file_name = parse_vg_filename(filename)
                    if file_id:
                        vg_id = file_id
                        vg_name = file_name if not actual_name else actual_name
                    else:
                        continue
                
                # Check for uniqueness violations
                if vg_id in id_to_name and id_to_name[vg_id] != vg_name:
                    raise ValueError(
                        "ID '%s' maps to multiple names: '%s' and '%s'" % 
                        (vg_id, id_to_name[vg_id], vg_name)
                    )
                
                if vg_name in name_to_id and name_to_id[vg_name] != vg_id:
                    raise ValueError(
                        "Name '%s' maps to multiple IDs: '%s' and '%s'" % 
                        (vg_name, name_to_id[vg_name], vg_id)
                    )
                
                # Store mappings
                id_to_name[vg_id] = vg_name
                name_to_id[vg_name] = vg_id
                
        except (json.JSONDecodeError, IOError):
            # If we can't read the JSON, skip this file
            pass
    
    return id_to_name, name_to_id

def match_pattern(pattern, names, ignore_case=False, use_regex=False):
    """
    Match a pattern against a list of names.
    
    Args:
        pattern: Glob pattern or regex pattern
        names: List of names to match against
        ignore_case: Case-insensitive matching
        use_regex: Use regex instead of glob
    
    Returns:
        list: Matching names
    """
    matches = []
    
    if use_regex:
        # Compile regex pattern
        flags = re.IGNORECASE if ignore_case else 0
        try:
            regex = re.compile(pattern, flags)
        except re.error:
            return []
        
        for name in names:
            if regex.search(name):
                matches.append(name)
    else:
        # Use glob pattern
        if ignore_case:
            pattern_lower = pattern.lower()
            for name in names:
                if fnmatch.fnmatch(name.lower(), pattern_lower):
                    matches.append(name)
        else:
            for name in names:
                if fnmatch.fnmatch(name, pattern):
                    matches.append(name)
    
    return matches

def resolve_vg_identifier(identifier, directory='variable-groups', ignore_case=False, use_regex=False):
    """
    Resolve a variable group identifier (name, ID, or pattern) to IDs and names.
    
    Args:
        identifier: Variable group name, ID, or pattern
        directory: Directory containing variable group JSON files
        ignore_case: Case-insensitive matching
        use_regex: Treat identifier as regex pattern
    
    Returns:
        list: List of (id, name) tuples for matching groups
    """
    id_to_name, name_to_id = build_vg_mapping(directory)
    
    # Check if identifier is an ID
    if str(identifier) in id_to_name:
        vg_id = str(identifier)
        vg_name = id_to_name[vg_id]
        return [(vg_id, vg_name)]
    
    # Check for exact name match
    if identifier in name_to_id:
        vg_id = name_to_id[identifier]
        vg_name = identifier
        return [(vg_id, vg_name)]
    
    # Check if it's a pattern (contains *, ?, or [ for glob, or regex mode)
    is_pattern = ('*' in identifier or '?' in identifier or '[' in identifier) or use_regex
    
    if is_pattern:
        # Pattern matching
        all_names = list(name_to_id.keys())
        matching_names = match_pattern(identifier, all_names, ignore_case, use_regex)
        
        results = []
        for name in matching_names:
            vg_id = name_to_id[name]
            results.append((vg_id, name))
        return results
    
    # Try case-insensitive name match (single match)
    if ignore_case:
        identifier_lower = identifier.lower()
        for name, vid in name_to_id.items():
            if name.lower() == identifier_lower:
                return [(vid, name)]
    
    # Try replacing underscores with spaces and vice versa
    alt_identifier = identifier.replace('_', ' ')
    if alt_identifier in name_to_id:
        vg_id = name_to_id[alt_identifier]
        return [(vg_id, alt_identifier)]
    
    alt_identifier = identifier.replace(' ', '_')
    if alt_identifier in name_to_id:
        vg_id = name_to_id[alt_identifier]
        return [(vg_id, alt_identifier)]
    
    return []

def find_vg_file(identifier, directory='variable-groups'):
    """
    Find the JSON file for a variable group by name or ID.
    
    Args:
        identifier: Variable group name or ID
        directory: Directory containing variable group JSON files
    
    Returns:
        str: Path to the JSON file, or None if not found
    """
    if not os.path.exists(directory):
        return None
    
    results = resolve_vg_identifier(identifier, directory)
    
    if not results:
        # Try direct file path
        if os.path.isfile(identifier):
            return identifier
        
        # Try in directory
        test_path = os.path.join(directory, identifier)
        if os.path.isfile(test_path):
            return test_path
        
        # Try with .json extension
        if not identifier.endswith('.json'):
            test_path = os.path.join(directory, identifier + '.json')
            if os.path.isfile(test_path):
                return test_path
        
        return None
    
    # Get the first match
    vg_id, vg_name = results[0]
    
    # Look for matching files
    for filename in os.listdir(directory):
        if not filename.endswith('.json'):
            continue
        
        file_id, file_name = parse_vg_filename(filename)
        
        # Match by ID
        if vg_id and file_id == vg_id:
            return os.path.join(directory, filename)
        
        # Match by exact name in filename
        if vg_name and file_name == vg_name:
            return os.path.join(directory, filename)
        
        # Check file content for matching
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                if str(data.get('id')) == vg_id or data.get('name') == vg_name:
                    return filepath
        except:
            pass
    
    return None

def create_vg_filename(vg_id, vg_name, preserve_exact=True):
    """
    Create a standardized filename for a variable group.
    
    Args:
        vg_id: Variable group ID (can be None)
        vg_name: Variable group name
        preserve_exact: If True, preserve exact name except OS-forbidden chars
    
    Returns:
        str: Standardized filename
    """
    # Create safe name
    safe_name = sanitize_filename(vg_name, preserve_exact)
    
    if vg_id:
        return 'vg_%s_%s.json' % (vg_id, safe_name)
    else:
        return '%s.json' % safe_name

def list_variable_groups(directory='variable-groups'):
    """
    List all variable groups in the directory.
    
    Args:
        directory: Directory containing variable group JSON files
    
    Returns:
        list: List of tuples (id, name, filepath)
    """
    groups = []
    
    if not os.path.exists(directory):
        return groups
    
    id_to_name, name_to_id = build_vg_mapping(directory)
    
    # Build list from mappings
    processed_ids = set()
    for vg_id, vg_name in id_to_name.items():
        if vg_id not in processed_ids:
            filepath = find_vg_file(vg_id, directory)
            if filepath:
                groups.append((vg_id, vg_name, filepath))
                processed_ids.add(vg_id)
    
    # Add any name-only entries
    for vg_name, vg_id in name_to_id.items():
        if vg_id not in processed_ids:
            filepath = find_vg_file(vg_name, directory)
            if filepath:
                groups.append((vg_id, vg_name, filepath))
                processed_ids.add(vg_id)
    
    return sorted(groups, key=lambda x: (x[0] or '', x[1]))
