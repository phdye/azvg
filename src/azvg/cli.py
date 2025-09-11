# -*- coding: utf-8 -*-
"""Command-line interface for azvg."""

import sys
import logging
import os.path
import argparse

from . import __version__
from .config import Config
from .client import AzureDevOpsClient
from .cache import CacheManager
from .project import ProjectContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def simple_table(data, headers):
    """Simple table formatter for Python 3.2.5.
    
    Args:
        data: List of lists containing table data.
        headers: List of column headers.
        
    Returns:
        Formatted table string.
    """
    if not data:
        return ""
    
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in data:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))
    
    # Format header
    header_line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    separator = "  ".join("-" * w for w in widths)
    
    # Format rows
    lines = [header_line, separator]
    for row in data:
        line = "  ".join(str(cell).ljust(w) 
                        for cell, w in zip(row, widths))
        lines.append(line)
    
    return "\n".join(lines)


def create_argument_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description='Azure DevOps Variable Groups Manager',
        prog='azvg'
    )
    
    parser.add_argument('--version', action='version', 
                       version='azvg {0}'.format(__version__))
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # init command
    init_parser = subparsers.add_parser('init', 
                                       help='Initialize azvg configuration')
    init_parser.add_argument('--org', required=True,
                            help='Azure DevOps organization')
    init_parser.add_argument('--pat', required=True,
                            help='Personal Access Token')
    init_parser.add_argument('--project',
                            help='Default project')
    
    # project commands
    project_parser = subparsers.add_parser('project',
                                          help='Manage projects')
    project_subs = project_parser.add_subparsers(dest='project_command')
    
    # project list
    project_subs.add_parser('list', help='List all projects')
    
    # project use
    project_use = project_subs.add_parser('use', 
                                         help='Set default project')
    project_use.add_argument('project_name', help='Project name')
    
    # project info
    project_info = project_subs.add_parser('info',
                                          help='Show project information')
    project_info.add_argument('project_name', nargs='?',
                             help='Project name')
    
    # pull command
    pull_parser = subparsers.add_parser('pull', 
                                       help='Pull items from Azure DevOps')
    pull_parser.add_argument('target', nargs='?',
                            help='Variable group name or pattern')
    pull_parser.add_argument('--project',
                            help='Specific project')
    pull_parser.add_argument('--all-projects', action='store_true',
                            help='Pull from all projects')
    pull_parser.add_argument('--type', dest='item_type',
                            choices=['vg', 'sf', 'all'], default='all',
                            help='Item type to pull')
    pull_parser.add_argument('--pattern',
                            help='Pattern to match')
    
    # push command
    push_parser = subparsers.add_parser('push',
                                       help='Push items to Azure DevOps')
    push_parser.add_argument('target', help='Variable group name')
    push_parser.add_argument('--project', help='Target project')
    push_parser.add_argument('--type', dest='item_type',
                            choices=['vg', 'sf'],
                            help='Item type (auto-detected if not specified)')
    push_parser.add_argument('--create', action='store_true',
                            help='Create if does not exist')
    
    # sf commands
    sf_parser = subparsers.add_parser('sf', help='Manage secure files')
    sf_subs = sf_parser.add_subparsers(dest='sf_command')
    
    # sf list
    sf_list = sf_subs.add_parser('list', help='List secure files')
    sf_list.add_argument('--project', help='Project name')
    
    # status command
    subparsers.add_parser('status', help='Show cache status')
    
    # list command
    list_parser = subparsers.add_parser('list', help='List cached items')
    list_parser.add_argument('--type', dest='item_type',
                            choices=['vg', 'sf', 'all'], default='all',
                            help='Item type to list')
    list_parser.add_argument('--project', help='Project name')
    
    return parser


def handle_init(args, config):
    """Handle init command."""
    # Set organization
    config.organization = args.org
    
    # Set project if provided
    if args.project:
        config.project = args.project
    
    # Save PAT (support env var reference)
    pat = args.pat
    if pat.startswith('$'):
        pat = '${' + pat[1:] + '}'
    
    config.set_org_config(args.org, {'pat': pat})
    config.save()
    
    # Initialize cache
    cache_root = config.data['cache']['root']
    cache = CacheManager(cache_root, args.org)
    
    print("✓ Initialized azvg for organization: {0}".format(args.org))
    if args.project:
        print("✓ Default project set to: {0}".format(args.project))
    print("✓ Cache directory: {0}".format(cache.org_dir))


def handle_project_list(args, config):
    """Handle project list command."""
    if not config.organization:
        print("Error: No organization configured. Run 'azvg init' first.")
        sys.exit(1)
    
    pat = config.get_pat()
    if not pat:
        print("Error: No PAT configured for organization.")
        sys.exit(1)
    
    client = AzureDevOpsClient(config.organization, pat)
    
    try:
        projects = client.list_projects()
        
        # Format output
        table_data = []
        for p in projects:
            name = p['name']
            is_current = '→' if name == config.project else ' '
            
            # Check if cached
            cache_root = config.data['cache']['root']
            project_dir = os.path.join(cache_root, config.organization, name)
            is_cached = '✓' if os.path.exists(project_dir) else ' '
            
            table_data.append([is_current, name, is_cached])
        
        headers = ['', 'Project', 'Cached']
        print(simple_table(table_data, headers))
        
    except Exception as e:
        print("Error: Failed to list projects: {0}".format(str(e)))
        sys.exit(1)


def handle_project_use(args, config):
    """Handle project use command."""
    proj_ctx = ProjectContext(config)
    proj_ctx.use_project(args.project_name)
    print("✓ Switched to project: {0}".format(args.project_name))


def handle_project_info(args, config):
    """Handle project info command."""
    proj_ctx = ProjectContext(config)
    
    project_name = args.project_name or config.project
    if not project_name:
        print("Error: No project specified or configured.")
        sys.exit(1)
    
    # Get cache info
    cache_root = config.data['cache']['root']
    cache = CacheManager(cache_root, config.organization)
    
    project_dir = cache.get_project_dir(project_name)
    vg_count = len(cache.list_cached_vgs(project_name))
    sf_count = len(cache.list_cached_sfs(project_name))
    
    print("Project: {0}".format(project_name))
    print("Organization: {0}".format(config.organization))
    print("Cache Directory: {0}".format(project_dir))
    print("Variable Groups: {0}".format(vg_count))
    print("Secure Files: {0}".format(sf_count))


def handle_project(args, config):
    """Handle project commands."""
    if args.project_command == 'list':
        handle_project_list(args, config)
    elif args.project_command == 'use':
        handle_project_use(args, config)
    elif args.project_command == 'info':
        handle_project_info(args, config)
    else:
        print("Error: No project subcommand specified")
        sys.exit(1)

def handle_pull(args, config):
    """Handle pull command."""
    if not config.organization:
        print("Error: No organization configured. Run 'azvg init' first.")
        sys.exit(1)
    
    # Determine project(s)
    if args.all_projects:
        pat = config.get_pat()
        client = AzureDevOpsClient(config.organization, pat)
        try:
            projects = [p['name'] for p in client.list_projects()]
        except Exception as e:
            print("Error: Failed to list projects: {0}".format(str(e)))
            sys.exit(1)
    else:
        project = args.project or config.project
        if not project:
            print("Error: No project specified or configured.")
            sys.exit(1)
        projects = [project]
    
    # Get client and cache
    pat = config.get_pat()
    if not pat:
        print("Error: No PAT configured.")
        sys.exit(1)
    
    client = AzureDevOpsClient(config.organization, pat)
    cache_root = config.data['cache']['root']
    cache = CacheManager(cache_root, config.organization)
    
    # Process each project
    total_vgs = 0
    total_sfs = 0
    
    for proj in projects:
        print("\nPulling from project: {0}".format(proj))
        
        # Pull variable groups
        if args.item_type in ['vg', 'all']:
            try:
                vgs = client.get_variable_groups(proj)
                
                # Filter by target/pattern
                if args.target or args.pattern:
                    search = args.target or args.pattern
                    vgs = [vg for vg in vgs 
                          if search.lower() in vg['name'].lower()]
                
                for vg in vgs:
                    cache.save_variable_group(proj, vg)
                    print("  ✓ {0} (VG:{1})".format(vg['name'], vg['id']))
                    total_vgs += 1
                    
            except Exception as e:
                print("  ⚠ Failed to pull variable groups: {0}".format(str(e)))
        
        # Pull secure files
        if args.item_type in ['sf', 'all']:
            try:
                sfs = client.list_secure_files(proj)
                
                # Filter by target/pattern
                if args.target or args.pattern:
                    search = args.target or args.pattern
                    sfs = [sf for sf in sfs
                          if search.lower() in sf['name'].lower()]
                
                for sf in sfs:
                    content = client.download_secure_file(proj, sf['id'])
                    cache.save_secure_file(proj, sf['name'], content, sf['id'])
                    print("  ✓ {0} (SF:{1})".format(sf['name'], sf['id']))
                    total_sfs += 1
                    
            except Exception as e:
                print("  ⚠ Failed to pull secure files: {0}".format(str(e)))
    
    print("\n✓ Pulled {0} variable groups, {1} secure files".format(
        total_vgs, total_sfs))


def handle_push(args, config):
    """Handle push command."""
    project = args.project or config.project
    if not project:
        print("Error: No project specified or configured.")
        sys.exit(1)
    
    pat = config.get_pat()
    if not pat:
        print("Error: No PAT configured.")
        sys.exit(1)
    
    client = AzureDevOpsClient(config.organization, pat)
    cache_root = config.data['cache']['root']
    cache = CacheManager(cache_root, config.organization)
    
    # Try to load from cache
    vg_data = cache.load_variable_group(project, args.target)
    
    if vg_data:
        # Push variable group
        try:
            if vg_data.get('id'):
                # Update existing
                result = client.update_variable_group(project, 
                                                     vg_data['id'], vg_data)
                print("✓ Updated {0} (VG:{1})".format(result['name'], 
                                                      result['id']))
            elif args.create:
                # Create new
                vg_data.pop('id', None)
                result = client.create_variable_group(project, vg_data)
                print("✓ Created {0} (VG:{1})".format(result['name'], 
                                                      result['id']))
            else:
                print("Error: {0} not found on server. Use --create to create new.".format(args.target))
        except Exception as e:
            print("Error: Failed to push variable group: {0}".format(str(e)))
    else:
        print("Error: {0} not found in cache".format(args.target))


def handle_sf_list(args, config):
    """Handle sf list command."""
    project = args.project or config.project
    if not project:
        print("Error: No project specified or configured.")
        sys.exit(1)
    
    cache_root = config.data['cache']['root']
    cache = CacheManager(cache_root, config.organization)
    
    sfs = cache.list_cached_sfs(project)
    
    if sfs:
        table_data = []
        for sf in sfs:
            size_kb = sf['size'] / 1024.0
            table_data.append([sf['name'], "{0:.1f} KB".format(size_kb), 
                             sf['modified']])
        
        headers = ['Name', 'Size', 'Modified']
        print(simple_table(table_data, headers))
    else:
        print("No cached secure files found.")


def handle_sf(args, config):
    """Handle sf commands."""
    if args.sf_command == 'list':
        handle_sf_list(args, config)
    else:
        print("Error: No sf subcommand specified")
        sys.exit(1)


def handle_status(args, config):
    """Handle status command."""
    if not config.organization:
        print("No organization configured. Run 'azvg init' first.")
        return
    
    cache_root = config.data['cache']['root']
    cache = CacheManager(cache_root, config.organization)
    
    status = cache.get_status()
    
    print("Organization: {0}".format(status['organization']))
    if config.project:
        print("Default Project: {0}".format(config.project))
    print("Cache Directory: {0}".format(status['cache_dir']))
    print("Git Tracking: {0}".format('✓' if status['git_tracking'] else '✗'))
    
    if status['projects']:
        print("\nPROJECTS:")
        for proj in status['projects']:
            is_default = ' [default]' if proj['name'] == config.project else ''
            print("  {0}: {1} VGs, {2} SFs{3}".format(
                proj['name'], proj['variable_groups'], 
                proj['secure_files'], is_default))
    else:
        print("\nNo cached projects found.")


def handle_list(args, config):
    """Handle list command."""
    project = args.project or config.project
    if not project:
        print("Error: No project specified or configured.")
        sys.exit(1)
    
    cache_root = config.data['cache']['root']
    cache = CacheManager(cache_root, config.organization)
    
    # List variable groups
    if args.item_type in ['vg', 'all']:
        vgs = cache.list_cached_vgs(project)
        if vgs:
            print("\nVariable Groups:")
            for vg in vgs:
                print("  {0} (ID: {1})".format(vg['name'], vg['id']))
    
    # List secure files
    if args.item_type in ['sf', 'all']:
        sfs = cache.list_cached_sfs(project)
        if sfs:
            print("\nSecure Files:")
            for sf in sfs:
                size_kb = sf['size'] / 1024.0
                print("  {0} ({1:.1f} KB)".format(sf['name'], size_kb))


def main():
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Load configuration
    config = Config()
    
    # Route to appropriate handler
    if args.command == 'init':
        handle_init(args, config)
    elif args.command == 'project':
        handle_project(args, config)
    elif args.command == 'pull':
        handle_pull(args, config)
    elif args.command == 'push':
        handle_push(args, config)
    elif args.command == 'sf':
        handle_sf(args, config)
    elif args.command == 'status':
        handle_status(args, config)
    elif args.command == 'list':
        handle_list(args, config)
    else:
        print("Error: Unknown command: {0}".format(args.command))
        sys.exit(1)


if __name__ == '__main__':
    main()
