# azvg-compare - Azure DevOps Variable Groups Comparison Tool

## Overview
`azvg-compare` is a Python script that compares two Azure DevOps variable groups and shows the differences between them. It supports flexible identification by variable group ID, name, or file path.

## Prerequisites
1. Download variable groups first using `azvg-down` to populate the local cache
2. Variable groups are stored in the `variable-groups/` directory

## Usage

### Basic comparison (names and values):
```bash
# Compare by IDs
azvg-compare 23 13

# Compare by names
azvg-compare "Production Variables" "Staging Variables"

# Compare by file paths
azvg-compare variable-groups/prod.json variable-groups/staging.json

# Mixed - ID and name
azvg-compare 23 "Staging Variables"

# On Windows with batch file
azvg-compare.bat "Production Variables" "Staging Variables"
```

### Compare only variable names:
```bash
# Using any of these flags
azvg-compare "Group A" "Group B" -n
azvg-compare "Group A" "Group B" --names
azvg-compare "Group A" "Group B" --names-only
```

## Key Features

### Flexible Identification
- **By ID**: Use numeric variable group IDs
- **By Name**: Use variable group names (exact or partial match)
- **By File Path**: Direct paths to JSON files
- **Mixed Mode**: Compare using different identifier types
- **Local Resolution**: Uses cached files for fast comparison

### Smart Resolution
The tool automatically:
- Resolves IDs to files using `vg_<id>_*.json` pattern
- Resolves names using the local cache mapping
- Handles spaces and underscores in names
- Performs case-insensitive matching

## Output Format

### Full Comparison Mode (default)
Shows:
- Variables only in Group A (marked with `+`)
- Variables only in Group B (marked with `-`)
- Variables with different values (marked with `!`)
- Identical variables (marked with `=`)
- Summary statistics with IDs and names

### Names-Only Mode (-n/--names/--names-only)
Shows:
- Variables only in Group A
- Variables only in Group B
- Variables present in both groups
- Summary statistics

## Examples

### Example 1: Compare by IDs
```bash
$ azvg-compare 23 13
Loading variable groups...
Loaded: variable-groups/vg_23_Production_Config.json
Loaded: variable-groups/vg_13_Staging_Config.json

================================================================================
VARIABLE GROUP COMPARISON
================================================================================
Group A: Production Config (ID: 23)
Group B: Staging Config (ID: 13)
--------------------------------------------------------------------------------

Variables only in 'Production Config':
  + PROD_ONLY_VAR = true
  + PROD_API_KEY = [SECRET]

Variables only in 'Staging Config':
  - STAGING_ONLY_VAR = false
  - DEBUG_MODE = true

Variables with different values:
  ! ENVIRONMENT:
      A: production
      B: staging
  ! API_ENDPOINT:
      A: https://api.prod.example.com
      B: https://api.staging.example.com

Identical variables (5):
  = DATABASE_NAME
  = LOG_LEVEL
  = TIMEOUT_SECONDS
  = API_VERSION
  = SECRET_TOKEN [SECRET]

Summary:
  Total in 'Production Config': 10
  Total in 'Staging Config': 11
  Identical: 5
  Different: 2
  Unique to 'Production Config': 2
  Unique to 'Staging Config': 3
================================================================================
```

### Example 2: Compare by names
```bash
$ azvg-compare "Development" "Production"
Loading variable groups...
Loaded: variable-groups/vg_345_Development.json
Loaded: variable-groups/vg_23_Production.json
...
```

### Example 3: Names-only comparison
```bash
$ azvg-compare "Development" "Production" --names-only
Loading variable groups...
...
Variables only in 'Development':
  + DEBUG_FLAG
  + DEV_TOOLS_ENABLED
  + LOCAL_DATABASE

Variables only in 'Production':
  - PROD_MONITORING
  - SCALE_FACTOR
  - CDN_ENABLED

Variables in both groups (15):
  = API_ENDPOINT
  = DATABASE_NAME
  = LOG_LEVEL
  ...

Summary:
  Total in 'Development': 18
  Total in 'Production': 18
  Common variables: 15
  Unique to 'Development': 3
  Unique to 'Production': 3
```

### Example 4: Mixed comparison
```bash
$ azvg-compare 23 "Staging Config"
Loading variable groups...
Loaded: variable-groups/vg_23_Production_Config.json
Loaded: variable-groups/vg_13_Staging_Config.json
...
```

## Complete Workflow

### 1. Download variable groups
```bash
# Download all to populate cache
azvg-down --all

# Or download specific ones
azvg-down "Production"
azvg-down "Staging"
azvg-down "Development"
```

### 2. List available groups
```bash
python list-vg-cache.py
```

### 3. Compare groups
```bash
# Compare development to production
azvg-compare "Development" "Production"

# See what variables are unique to each environment
azvg-compare "Development" "Production" --names-only
```

### 4. Use comparison for migration
```bash
# See differences
azvg-compare "Old Config" "New Config"

# Download old config
azvg-down "Old Config"

# Edit to match new requirements
vi variable-groups/vg_123_Old_Config.json

# Upload as new config
azvg-upload variable-groups/vg_123_Old_Config.json --new
```

## File Resolution Process

When you specify an identifier, azvg-compare:

1. **Tries direct file path** → If file exists, use it
2. **Uses vg_utils to find file** → Searches by ID or name in cache
3. **Fallback search** → Looks for any matching files in variable-groups/
4. **Error if not found** → Shows where it searched

## Features

- **Secure Variable Handling**: Secret variables shown as [SECRET]
- **Intelligent Matching**: Handles spaces, underscores, and case variations
- **Detailed Comparison**: Shows exact differences in values
- **Summary Statistics**: Quick overview of similarities and differences
- **Cross-platform**: Works on Windows, Linux, and macOS

## Troubleshooting

### File Not Found
```
Error: Could not find variable group file for 'MyGroup'
Searched in:
  - Direct file path
  - variable-groups/ directory
```
**Solution**: Run `azvg-down "MyGroup"` or `azvg-down --all` first

### Multiple Matches
```
Multiple groups found matching "config":
  - Development Config (ID: 345)
  - Production Config (ID: 23)
  - Staging Config (ID: 13)
Please be more specific or use the ID directly.
```
**Solution**: Use the full name or ID instead

### No Local Cache
```
Error: No variable-groups directory found - skipping directory tests
Run './azvg-down --all' to create test data
```
**Solution**: Download variable groups first

## Integration with Other Tools

- **azvg-down**: Download variable groups to compare
- **azvg-upload**: Upload modified variable groups after comparison
- **list-vg-cache.py**: See available groups for comparison
- **test-azdo.py**: Verify environment setup

## Notes

- Variable group names must be unique for reliable resolution
- The script is case-sensitive when comparing variable values
- Secret variable values cannot be compared (always shown as [SECRET])
- Comparison results can help identify configuration drift between environments
