"""Command-line interface for azvg."""

import sys
import logging
from pathlib import Path
from typing import Optional

import click
from tabulate import tabulate

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


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def main(ctx):
    """Azure DevOps Variable Groups Manager.
    
    Manage Azure DevOps Library items locally with git tracking.
    """
    ctx.ensure_object(dict)
    ctx.obj['config'] = Config()


@main.command()
@click.option('--org', required=True, help='Azure DevOps organization')
@click.option('--pat', required=True, help='Personal Access Token')
@click.option('--project', help='Default project')
@click.pass_context
def init(ctx, org: str, pat: str, project: Optional[str]):
    """Initialize azvg configuration."""
    config = ctx.obj['config']
    
    # Set organization
    config.organization = org
    
    # Set project if provided
    if project:
        config.project = project
    
    # Save PAT (support env var reference)
    if pat.startswith('$'):
        pat = '${' + pat[1:] + '}'
    
    config.set_org_config(org, {'pat': pat})
    config.save()
    
    # Initialize cache
    cache_root = Path(config.data['cache']['root'])
    cache = CacheManager(cache_root, org)
    
    click.echo(f"✓ Initialized azvg for organization: {org}")
    if project:
        click.echo(f"✓ Default project set to: {project}")
    click.echo(f"✓ Cache directory: {cache.org_dir}")


@main.group()
@click.pass_context
def project(ctx):
    """Manage projects."""
    pass


@project.command('list')
@click.pass_context
def project_list(ctx):
    """List all projects."""
    config = ctx.obj['config']
    
    if not config.organization:
        click.echo("Error: No organization configured. Run 'azvg init' first.")
        sys.exit(1)
    
    pat = config.get_pat()
    if not pat:
        click.echo("Error: No PAT configured for organization.")
        sys.exit(1)
    
    client = AzureDevOpsClient(config.organization, pat)
    proj_ctx = ProjectContext(config)
    
    try:
        projects = client.list_projects()
        
        # Format output
        table_data = []
        for p in projects:
            name = p['name']
            is_current = '→' if name == config.project else ' '
            is_cached = '✓' if (Path(config.data['cache']['root']) / 
                              config.organization / name).exists() else ' '
            table_data.append([is_current, name, is_cached])
        
        headers = ['', 'Project', 'Cached']
        click.echo(tabulate(table_data, headers=headers, tablefmt='simple'))
        
    except Exception as e:
        click.echo(f"Error: Failed to list projects: {e}")
        sys.exit(1)


@project.command('use')
@click.argument('project_name')
@click.pass_context
def project_use(ctx, project_name: str):
    """Set default project."""
    config = ctx.obj['config']
    proj_ctx = ProjectContext(config)
    
    proj_ctx.use_project(project_name)
    click.echo(f"✓ Switched to project: {project_name}")


@project.command('info')
@click.argument('project_name', required=False)
@click.pass_context
def project_info(ctx, project_name: Optional[str]):
    """Show project information."""
    config = ctx.obj['config']
    proj_ctx = ProjectContext(config)
    
    project_name = project_name or config.project
    if not project_name:
        click.echo("Error: No project specified or configured.")
        sys.exit(1)
    
    # Get cache info
    cache_root = Path(config.data['cache']['root'])
    cache = CacheManager(cache_root, config.organization)
    
    project_dir = cache.get_project_dir(project_name)
    vg_count = len(list(cache.list_cached_vgs(project_name)))
    sf_count = len(list(cache.list_cached_sfs(project_name)))
    
    click.echo(f"Project: {project_name}")
    click.echo(f"Organization: {config.organization}")
    click.echo(f"Cache Directory: {project_dir}")
    click.echo(f"Variable Groups: {vg_count}")
    click.echo(f"Secure Files: {sf_count}")


@main.command()
@click.argument('target', required=False)
@click.option('--project', help='Specific project')
@click.option('--all-projects', is_flag=True, help='Pull from all projects')
@click.option('--type', 'item_type', type=click.Choice(['vg', 'sf', 'all']),
              default='all', help='Item type to pull')
@click.option('--pattern', help='Pattern to match')
@click.pass_context
def pull(ctx, target: Optional[str], project: Optional[str],
         all_projects: bool, item_type: str, pattern: Optional[str]):
    """Pull items from Azure DevOps."""
    config = ctx.obj['config']
    
    if not config.organization:
        click.echo("Error: No organization configured. Run 'azvg init' first.")
        sys.exit(1)
    
    # Determine project(s)
    if all_projects:
        pat = config.get_pat()
        client = AzureDevOpsClient(config.organization, pat)
        projects = [p['name'] for p in client.list_projects()]
    else:
        project = project or config.project
        if not project:
            click.echo("Error: No project specified or configured.")
            sys.exit(1)
        projects = [project]
    
    # Get client and cache
    pat = config.get_pat()
    if not pat:
        click.echo("Error: No PAT configured.")
        sys.exit(1)
    
    client = AzureDevOpsClient(config.organization, pat)
    cache_root = Path(config.data['cache']['root'])
    cache = CacheManager(cache_root, config.organization)
    
    # Process each project
    total_vgs = 0
    total_sfs = 0
    
    for proj in projects:
        click.echo(f"\nPulling from project: {proj}")
        
        # Pull variable groups
        if item_type in ['vg', 'all']:
            try:
                vgs = client.get_variable_groups(proj)
                
                # Filter by target/pattern
                if target or pattern:
                    search = target or pattern
                    vgs = [vg for vg in vgs 
                          if search.lower() in vg['name'].lower()]
                
                for vg in vgs:
                    cache.save_variable_group(proj, vg)
                    click.echo(f"  ✓ {vg['name']} (VG:{vg['id']})")
                    total_vgs += 1
                    
            except Exception as e:
                click.echo(f"  ⚠ Failed to pull variable groups: {e}")
        
        # Pull secure files
        if item_type in ['sf', 'all']:
            try:
                sfs = client.list_secure_files(proj)
                
                # Filter by target/pattern
                if target or pattern:
                    search = target or pattern
                    sfs = [sf for sf in sfs
                          if search.lower() in sf['name'].lower()]
                
                for sf in sfs:
                    content = client.download_secure_file(proj, sf['id'])
                    cache.save_secure_file(proj, sf['name'], content, sf['id'])
                    click.echo(f"  ✓ {sf['name']} (SF:{sf['id']})")
                    total_sfs += 1
                    
            except Exception as e:
                click.echo(f"  ⚠ Failed to pull secure files: {e}")
    
    click.echo(f"\n✓ Pulled {total_vgs} variable groups, {total_sfs} secure files")


@main.command()
@click.argument('target')
@click.option('--project', help='Target project')
@click.option('--type', 'item_type', type=click.Choice(['vg', 'sf']),
              help='Item type (auto-detected if not specified)')
@click.option('--create', is_flag=True, help='Create if does not exist')
@click.pass_context
def push(ctx, target: str, project: Optional[str], 
         item_type: Optional[str], create: bool):
    """Push items to Azure DevOps."""
    config = ctx.obj['config']
    
    project = project or config.project
    if not project:
        click.echo("Error: No project specified or configured.")
        sys.exit(1)
    
    pat = config.get_pat()
    if not pat:
        click.echo("Error: No PAT configured.")
        sys.exit(1)
    
    client = AzureDevOpsClient(config.organization, pat)
    cache_root = Path(config.data['cache']['root'])
    cache = CacheManager(cache_root, config.organization)
    
    # Try to load from cache
    vg_data = cache.load_variable_group(project, target)
    
    if vg_data:
        # Push variable group
        try:
            if vg_data.get('id'):
                # Update existing
                result = client.update_variable_group(project, 
                                                     vg_data['id'], vg_data)
                click.echo(f"✓ Updated {result['name']} (VG:{result['id']})")
            elif create:
                # Create new
                vg_data.pop('id', None)
                result = client.create_variable_group(project, vg_data)
                click.echo(f"✓ Created {result['name']} (VG:{result['id']})")
            else:
                click.echo(f"Error: {target} not found on server. Use --create to create new.")
        except Exception as e:
            click.echo(f"Error: Failed to push variable group: {e}")
    else:
        click.echo(f"Error: {target} not found in cache")


@main.group('sf')
@click.pass_context
def secure_files(ctx):
    """Manage secure files."""
    pass


@secure_files.command('list')
@click.option('--project', help='Project name')
@click.pass_context
def sf_list(ctx, project: Optional[str]):
    """List secure files."""
    config = ctx.obj['config']
    
    project = project or config.project
    if not project:
        click.echo("Error: No project specified or configured.")
        sys.exit(1)
    
    cache_root = Path(config.data['cache']['root'])
    cache = CacheManager(cache_root, config.organization)
    
    sfs = cache.list_cached_sfs(project)
    
    if sfs:
        table_data = []
        for sf in sfs:
            size_kb = sf['size'] / 1024
            table_data.append([sf['name'], f"{size_kb:.1f} KB", 
                             sf['modified'].strftime('%Y-%m-%d %H:%M')])
        
        headers = ['Name', 'Size', 'Modified']
        click.echo(tabulate(table_data, headers=headers, tablefmt='simple'))
    else:
        click.echo("No cached secure files found.")


@main.command()
@click.pass_context
def status(ctx):
    """Show cache status."""
    config = ctx.obj['config']
    
    if not config.organization:
        click.echo("No organization configured. Run 'azvg init' first.")
        return
    
    cache_root = Path(config.data['cache']['root'])
    cache = CacheManager(cache_root, config.organization)
    
    status = cache.get_status()
    
    click.echo(f"Organization: {status['organization']}")
    if config.project:
        click.echo(f"Default Project: {config.project}")
    click.echo(f"Cache Directory: {status['cache_dir']}")
    click.echo(f"Git Tracking: {'✓' if status['git_tracking'] else '✗'}")
    
    if status['projects']:
        click.echo("\nPROJECTS:")
        for proj in status['projects']:
            is_default = ' [default]' if proj['name'] == config.project else ''
            click.echo(f"  {proj['name']}: {proj['variable_groups']} VGs, "
                      f"{proj['secure_files']} SFs{is_default}")
    else:
        click.echo("\nNo cached projects found.")


@main.command()
@click.option('--type', 'item_type', type=click.Choice(['vg', 'sf', 'all']),
              default='all', help='Item type to list')
@click.option('--project', help='Project name')  
@click.pass_context
def list(ctx, item_type: str, project: Optional[str]):
    """List cached items."""
    config = ctx.obj['config']
    
    project = project or config.project
    if not project:
        click.echo("Error: No project specified or configured.")
        sys.exit(1)
    
    cache_root = Path(config.data['cache']['root'])
    cache = CacheManager(cache_root, config.organization)
    
    # List variable groups
    if item_type in ['vg', 'all']:
        vgs = cache.list_cached_vgs(project)
        if vgs:
            click.echo("\nVariable Groups:")
            for vg in vgs:
                click.echo(f"  {vg['name']} (ID: {vg['id']})")
    
    # List secure files
    if item_type in ['sf', 'all']:
        sfs = cache.list_cached_sfs(project)
        if sfs:
            click.echo("\nSecure Files:")
            for sf in sfs:
                size_kb = sf['size'] / 1024
                click.echo(f"  {sf['name']} ({size_kb:.1f} KB)")


if __name__ == '__main__':
    main()
