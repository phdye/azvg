# azvg-upload - Azure DevOps Variable Group Upload/Merge Tool

## Description
Upload or merge Azure DevOps variable groups with intelligent handling of secure variables. Supports flexible identification by file path, variable group name, or ID.

## Prerequisites
1. Python 2.7+ or Python 3.x
2. Environment variables configured:
   - `AZURE_DEVOPS_ORG`: Your Azure DevOps organization name
   - `AZURE_DEVOPS_PROJECT`: Your Azure DevOps project name
   - `AZURE_DEVOPS_PAT`: Your Personal Access Token with "Variable Groups (Read & Manage)" scope

## Usage

### Update/Merge an existing variable group:

```bash
# By file path
azvg-upload variable-groups/vg_23_MyGroup.json

# By ID (finds file automatically)
azvg-upload 23

# By name (finds file automatically)
azvg-upload "My Variable Group"
```

On Windows:
```cmd
azvg-upload.bat "My Variable Group"
```

### Create a new variable group:
```bash
azvg-upload template.json --new
```

## Key Features

### Flexible Identification
- **File Path**: Direct path to JSON file
- **Variable Group ID**: Automatically finds matching file in `variable-groups/`
- **Variable Group Name**: Resolves name to file using local cache
- **Smart Resolution**: If no ID in file, attempts to resolve from name

### Intelligent Merging
The tool uses smart merge rules to handle different variable types safely:

1. **Non-secure variables**: Always overwritten with values from input
2. **Secure variables** (isSecret=true): Only overwritten if new value is not null
3. **New variables**: Added to the variable group
4. **Preserve secrets**: Existing secret values are preserved when uploading null

## Examples

### Upload by name (most user-friendly)
```bash
$ azvg-upload "Production Config"
Using file: variable-groups/vg_23_Production_Config.json
Updating/merging variable group from: variable-groups/vg_23_Production_Config.json
Successfully updated variable group: Production Config (ID: 23)
```

### Upload by ID
```bash
$ azvg-upload 23
Using file: variable-groups/vg_23_Production_Config.json
Updating/merging variable group from: variable-groups/vg_23_Production_Config.json
Successfully updated variable group: Production Config (ID: 23)
```

### Upload by file path
```bash
$ azvg-upload /path/to/custom.json
Using file: /path/to/custom.json
Updating/merging variable group from: /path/to/custom.json
Successfully updated variable group: Custom Group (ID: 123)
```

### Create new from template
```bash
$ azvg-upload template.json --new
Using file: template.json
Creating new variable group from: template.json
Successfully created variable group: New Group (ID: 456)
```

### Handle missing ID in file
```bash
$ azvg-upload my-config.json
Using file: my-config.json
No ID in file, attempting to resolve name "My Config" to ID...
Resolved to ID: 23
Updating/merging variable group from: my-config.json
Successfully updated variable group: My Config (ID: 23)
```

## File Resolution Process

When you specify an identifier, azvg-upload follows this process:

1. **Check if file exists** → Use directly
2. **Search in variable-groups/** → Look for matching files by:
   - ID match in filename (vg_23_*.json)
   - Name match in filename
   - Check file contents for matching ID/name
3. **Error if not found** → Shows where it searched

## Complete Workflow

### 1. Download variable groups
```bash
# Download all to populate cache
azvg-down --all

# Or download specific one
azvg-down "Production Config"
```

### 2. Edit the JSON file
```bash
vi variable-groups/vg_23_Production_Config.json
```

### 3. Upload changes
```bash
# Any of these work for the same group:
azvg-upload 23
azvg-upload "Production Config"
azvg-upload variable-groups/vg_23_Production_Config.json
```

## JSON File Format

The variable group JSON file structure:
```json
{
  "id": 23,
  "name": "Production Config",
  "description": "Production environment configuration",
  "type": "Vsts",
  "variables": {
    "API_ENDPOINT": {
      "value": "https://api.prod.example.com",
      "isSecret": false
    },
    "API_KEY": {
      "value": null,
      "isSecret": true
    },
    "DB_CONNECTION": {
      "value": null,
      "isSecret": true
    }
  }
}
```

**Note**: Set secure variable values to `null` to preserve existing values during merge.

## Merge Behavior Examples

### Original Variable Group
```json
{
  "variables": {
    "VAR1": {"value": "old", "isSecret": false},
    "SECRET1": {"value": "hidden", "isSecret": true}
  }
}
```

### Upload File
```json
{
  "variables": {
    "VAR1": {"value": "new", "isSecret": false},
    "SECRET1": {"value": null, "isSecret": true},
    "VAR2": {"value": "added", "isSecret": false}
  }
}
```

### Result After Merge
```json
{
  "variables": {
    "VAR1": {"value": "new", "isSecret": false},      // Updated
    "SECRET1": {"value": "hidden", "isSecret": true}, // Preserved
    "VAR2": {"value": "added", "isSecret": false}     // Added
  }
}
```

## Security Best Practices

1. **Never commit secrets**: Always use `null` for secret values in files
2. **Use minimal permissions**: PAT should only have required scopes
3. **Review before upload**: Check file contents before uploading
4. **Audit trail**: Azure DevOps tracks all variable group changes

## Troubleshooting

### Variable Group Not Found
```
Error: Variable group with ID 23 not found
Use --new flag to create a new variable group
```
**Solution**: Verify the ID exists or use `--new` flag

### Could Not Find File
```
Error: Could not find variable group file for: MyGroup
Searched in:
  - Direct file path
  - variable-groups/ directory
```
**Solution**: Run `azvg-down "MyGroup"` first or specify correct path

### No ID in File
```
No ID in file, attempting to resolve name "MyGroup" to ID...
Error: Variable group ID not found and could not be resolved
```
**Solution**: Ensure the variable group exists in Azure DevOps

### Permission Errors
```
HTTP Error 403: Forbidden
```
**Solution**: Ensure PAT has "Variable Groups (Read & Manage)" permission

## Integration with Other Tools

### Download → Edit → Upload Cycle
```bash
# Download
azvg-down "Development Config"

# Compare with production
azvg-compare "Development Config" "Production Config"

# Edit
vi variable-groups/vg_345_Development_Config.json

# Upload
azvg-upload "Development Config"
```

### List available groups
```bash
python list-vg-cache.py
```

## Related Tools
- `azvg-down`: Download variable groups (by name or ID)
- `azvg-compare`: Compare two variable groups
- `list-vg-cache.py`: List locally cached variable groups
- `test-azdo.py`: Test Azure DevOps connectivity
