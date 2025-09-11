# azvg-down - Azure DevOps Variable Group Downloader

Download variable groups from Azure DevOps and save them locally under the `./variable-groups/` directory in your current working directory.

## Prerequisites

Set the following environment variables:
```bash
export AZURE_DEVOPS_ORG="your-organization"
export AZURE_DEVOPS_PROJECT="your-project"
export AZURE_DEVOPS_PAT="your-personal-access-token"
```

Your PAT needs to have `Variable Groups (Read)` scope.

## Usage

### Download by ID or Name
```bash
# By ID
azvg-down 23

# By Name
azvg-down "My Variable Group"

# Name with spaces
azvg-down "Production Config"

# Name with underscores (automatically converted)
azvg-down Production_Config
```

### Download All Variable Groups
```bash
azvg-down --all
```

## Key Features

### Flexible Identification
- **ID or Name**: Specify variable groups by either their numeric ID or their name
- **Local Cache**: Resolves names from locally cached groups for faster lookups
- **Smart Matching**: Supports exact match, case-insensitive match, and partial match
- **Bidirectional Mapping**: Maintains unique ID-to-name mappings

### Output Format
Downloaded variable groups are saved to the `./variable-groups/` directory with standardized naming:
```
variable-groups/vg_<ID>_<SafeName>.json  # When ID is known
variable-groups/<SafeName>.json          # When only name is available
```

## Features

- **Current Directory Aware**: Saves files to `./variable-groups/` in your current working directory
- **Intelligent Resolution**: Checks local cache first, then queries remote if needed
- **Bulk Download**: Use `--all` flag to download all variable groups
- **Secure Variables**: Properly handles secret variables (displays as "secret" without values)
- **Python 2/3 Compatible**: Works with both Python 2.7+ and Python 3.x
- **Detailed Output**: Shows variable group details including all variable names

## Examples

### Download a specific variable group by ID
```bash
$ azvg-down 23
Organization: FOOBAR
Project: Project-A
Save directory: ./variable-groups/
Working directory: /home/user/projects
--------------------------------------------------
Downloading variable group ID: 23
Saved to: variable-groups/vg_23_Production_Config.json

Variable Group Details:
  Name: Production Config
  ID: 23
  Description: Production environment configuration
  Variables: 15

  Variable names:
    - API_KEY (secret)
    - DB_CONNECTION = Server=prod-db;Database=...
    - ENVIRONMENT = production
    ...
```

### Download by name (with local cache)
```bash
$ azvg-down "Production Config"
Organization: FOOBAR
Project: Project-A
Save directory: ./variable-groups/
--------------------------------------------------
Resolved "Production Config" to ID 23 from local cache
Downloading variable group ID: 23
Saved to: variable-groups/vg_23_Production_Config.json
...
```

### Download by partial name match
```bash
$ azvg-down prod
Searching for "prod" in remote variable groups...
Found partial match: Production Config
Downloading variable group ID: 23
...
```

### Download all variable groups
```bash
$ azvg-down --all
Downloading all variable groups...
Found 5 variable groups

Downloading: Development Config (ID: 345)
Saved to: variable-groups/vg_34_Development_Config.json

Downloading: Production Config (ID: 23)
Saved to: variable-groups/vg_23_Production_Config.json
...

5 variable groups downloaded to ./variable-groups/
```

## Resolution Process

When you specify a variable group identifier, azvg-down follows this process:

1. **Check if numeric** → Use as ID directly
2. **Check local cache** → Look for name in `./variable-groups/` files
3. **Query remote** → Search all variable groups in Azure DevOps
4. **Match strategy**:
   - Exact name match (highest priority)
   - Case-insensitive match
   - Partial match (if unique)

## Error Handling

- **Authentication Failed**: Check your PAT token has proper permissions
- **Not Found**: Verify the organization, project, and variable group ID/name
- **Multiple Matches**: When searching by name, be more specific if multiple groups match
- **Ambiguous Name**: Use the ID instead or provide the full exact name

## Integration with Other Tools

### With azvg-upload
```bash
# Download by name
azvg-down "Production Config"

# Edit if needed
vi variable-groups/vg_23_Production_Config.json

# Upload by name or ID
azvg-upload "Production Config"    # By name
azvg-upload 23                   # By ID
```

### With azvg-compare
```bash
# Download two groups
azvg-down "Development"
azvg-down "Production"

# Compare them
azvg-compare "Development" "Production"
```

### List cached groups
```bash
# See what's in your local cache
python list-vg-cache.py
```

## File Format

Downloaded files are in JSON format with the Azure DevOps variable group structure:
```json
{
  "id": 23,
  "name": "Production Config",
  "description": "Production environment configuration",
  "type": "Vsts",
  "variables": {
    "API_KEY": {
      "value": null,
      "isSecret": true
    },
    "ENVIRONMENT": {
      "value": "production",
      "isSecret": false
    }
  }
}
```

Note: Secret variable values are always `null` when downloaded for security reasons.

## Tips

- Use `--all` first to populate your local cache for faster name resolution
- Variable group names must be unique within a project for reliable resolution
- The standardized file naming ensures consistent ID-name mapping
- Check `test-azdo.py` to verify your environment setup
