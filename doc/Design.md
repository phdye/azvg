Excellent choice! Let's design for **multi-project** and **full Library support** from the start. This makes `azvg` an enterprise-grade tool.

## Multi-Project & Full Library Design

### Conceptual Model
```
Organization
├── Project-A
│   └── Library
│       ├── Variable Groups
│       │   ├── Production_Config
│       │   └── Staging_Config
│       └── Secure Files
│           ├── prod.pfx
│           └── signing.key
├── Project-B
│   └── Library
│       ├── Variable Groups
│       └── Secure Files
└── Project-C
    └── Library
```

### Cache Structure
```bash
.azvg/
├── config.yaml                    # Global config
├── MyOrg/                         # Organization level
│   ├── .git/                      # Single git repo for entire org
│   ├── Project-A/
│   │   ├── variable-groups/
│   │   │   ├── vg_347_Production_Config.json
│   │   │   └── vg_348_Staging_Config.json
│   │   ├── secure-files/
│   │   │   ├── sf_123_prod.pfx
│   │   │   └── sf_124_signing.key
│   │   └── .metadata.json         # Project metadata
│   ├── Project-B/
│   │   ├── variable-groups/
│   │   └── secure-files/
│   └── Project-C/
│       ├── variable-groups/
│       └── secure-files/
└── OtherOrg/                      # Support multiple orgs
    ├── .git/
    └── Project-X/
```

### Command Structure with Project/Library Support

```bash
# Project context commands
azvg project list                          # List all projects
azvg project use <project>                 # Set default project
azvg project info [<project>]              # Show project details

# Pull operations (Library-aware)
azvg pull [<target>] [options]
  --project <name>          # Specific project (overrides default)
  --all-projects           # Pull from all projects
  --type vg|sf|all         # Variable groups, secure files, or all
  --pattern <glob>         # Pattern matching
  
# Examples
azvg pull                                   # All library items, current project
azvg pull "Prod*"                          # Pattern match VGs
azvg pull --type sf                        # All secure files
azvg pull --all-projects "Production*"     # From all projects
azvg pull cert.pfx --type sf               # Specific secure file

# Push operations
azvg push [<target>] [options]
  --project <name>         # Target project
  --type vg|sf            # Type (auto-detected if not specified)
  --create                # Create if doesn't exist
  --to-project <name>     # Push to different project (copy)
  
# Examples  
azvg push Production_Config                # Push VG to current project
azvg push prod.pfx --type sf              # Push secure file
azvg push Config --to-project Project-B    # Copy to another project
```

### Library-Level Commands

```bash
# Library operations
azvg library list [--project <name>]       # List entire library
azvg library stats [--all-projects]        # Statistics
azvg library export --project <name>       # Export entire library
azvg library import --project <name>       # Import library backup
azvg library clean                         # Remove orphaned items

# Secure files specific
azvg sf list [--project]                   # List secure files
azvg sf pull <name> [--project]            # Download secure file
azvg sf push <file> [--project]            # Upload secure file
azvg sf delete <name> [--project]          # Delete secure file
azvg sf info <name>                        # Show file details

# Variable groups (aliased from main commands)
azvg vg list                               # Same as 'azvg list --type vg'
azvg vg pull                               # Same as 'azvg pull --type vg'
```

### Cross-Project Operations

```bash
# Copy between projects
azvg copy Production_Config --from Project-A --to Project-B
azvg copy cert.pfx --from Project-A --to Project-C --type sf

# Sync between projects
azvg sync Config --source Project-A --target Project-B
azvg sync --all --source Project-Template --target Project-New

# Compare across projects
azvg compare Project-A:Config Project-B:Config
azvg compare Project-A/library Project-B/library

# Diff across projects
azvg diff Production_Config --projects Project-A,Project-B
```

### Project Templates & Bulk Operations

```bash
# Template operations
azvg template create --from-project Project-Template
azvg template apply --to-project New-Project

# Bulk project operations
azvg bulk pull --projects Project-A,Project-B,Project-C
azvg bulk push Config --to-projects Project-*

# Migration commands
azvg migrate --from-project Old --to-project New
azvg archive --project Deprecated-Project
```

### Enhanced Status Command

```bash
$ azvg status
Organization: MyOrg
Default Project: Project-A

PROJECTS:
  Project-A:    23 variable groups, 5 secure files [default]
  Project-B:    15 variable groups, 3 secure files
  Project-C:    8 variable groups, 0 secure files

CURRENT PROJECT (Project-A):
  Variable Groups:
    Production_Config:     ✓ synced
    Staging_Config:        ↑ local changes
    Development_Config:    ↓ remote updated
  
  Secure Files:
    prod.pfx:             ✓ synced
    signing.key:          ⚠ not pulled

RECENT ACTIVITY:
  2024-01-10 15:30  push: Project-A/Production_Config
  2024-01-10 15:25  pull: Project-B/* (18 items)
  2024-01-10 15:20  copy: Project-A/Config → Project-B/Config
```

### Project Context Management

```bash
# Set default project (stored in config)
$ azvg project use Project-B
Switched to project: Project-B

# Override per command
$ azvg pull Config --project Project-A

# Work with multiple projects
$ azvg pull --all-projects

# List available projects
$ azvg project list
PROJECTS IN MyOrg:
  * Project-A (23 VGs, 5 SFs) [cached]
    Project-B (15 VGs, 3 SFs) [cached]
    Project-C (8 VGs, 0 SFs)  [not cached]
    Project-D (unknown)        [not cached]
```

### Configuration for Multi-Project

```yaml
# ~/.azvg/config.yaml
default:
  organization: MyOrg
  project: Project-A        # Default project

organizations:
  MyOrg:
    pat: ${AZURE_DEVOPS_PAT}
    projects:
      Project-A:
        aliases:
          prod: "Production*"
          stage: "Staging*"
      Project-B:
        default_type: vg    # Focus on variable groups
      Project-C:
        auto_pull: true     # Always pull before push
  
  OtherOrg:
    pat: ${OTHER_PAT}
    projects:
      Project-X: {}

cache:
  root: ~/.azvg
  git_tracking: true
  auto_commit: true
```

### Git Commits with Project Context

```bash
# Git commits include project context
$ cd ~/.azvg/MyOrg
$ git log --oneline
a1b2c3d pull: Project-A/Production_Config (VG:347)
b2c3d4e push: Project-B/staging.pfx (SF:124)  
c3d4e5f copy: Project-A/Config → Project-B/Config (VG:347→350)
d4e5f6g bulk: pulled 45 items from Project-A,Project-B
e5f6g7h sync: Project-Template → Project-New (23 items)
```

### Smart Project Detection

```python
class ProjectContext:
    def detect_project_from_target(self, target):
        """Auto-detect project from target notation"""
        # Support explicit project notation
        if ':' in target:
            # "Project-A:Config" or "Project-A/Config"
            project, item = target.split(':', 1)
            return project, item
        elif '/' in target:
            parts = target.split('/', 1)
            if self.is_project(parts[0]):
                return parts[0], parts[1]
        
        # Use default project
        return self.default_project, target
```

### Why This Design is Powerful

1. **Enterprise Ready**: Handles multiple projects/orgs naturally
2. **Complete Library**: Manages both VGs and secure files
3. **Flexible Context**: Easy project switching and overrides
4. **Cross-Project Ops**: Copy, sync, compare between projects
5. **Bulk Operations**: Handle many projects at once
6. **Template System**: Standardize project setups
7. **Hierarchical Cache**: Organized by org/project
8. **Rich Git History**: Tracks operations across projects

### Implementation Priority

Phase 1 (Core):
- Multi-project pull/push
- Project context management
- Basic secure file support

Phase 2 (Enhanced):
- Cross-project operations
- Template system
- Bulk operations

Phase 3 (Advanced):
- Library-level import/export
- Migration tools
- Archive operations

This design makes `azvg` a comprehensive Azure DevOps Library management tool, not just a variable group tool. Is this the direction you envision?