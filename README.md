# azvg - Azure DevOps Variable Groups Manager

Local management tool for Azure DevOps Library items (Variable Groups and 
Secure Files) with multi-project support and git tracking.

## Installation

```bash
pip install -e .
```

## Quick Start

```bash
# Configure your organization and PAT
azvg init --org MyOrg --pat $AZURE_DEVOPS_PAT

# Set default project
azvg project use Project-A

# Pull all variable groups from current project
azvg pull

# Pull specific variable group
azvg pull "Production_Config"

# Push changes back to Azure DevOps
azvg push Production_Config
```

## Features

- Multi-project support within organizations
- Local git tracking of all changes
- Pull/push variable groups and secure files
- Project context management
- Pattern-based operations
- Full Azure DevOps Library integration

## Usage Examples

### Project Management

```bash
# List all projects
azvg project list

# Switch to different project
azvg project use Project-B

# Show project info
azvg project info
```

### Variable Groups

```bash
# Pull all variable groups
azvg pull --type vg

# Pull with pattern
azvg pull "Prod*"

# Push changes
azvg push Production_Config
```

### Secure Files

```bash
# List secure files
azvg sf list

# Pull secure file
azvg sf pull cert.pfx

# Push secure file
azvg sf push signing.key
```

## Contributing

See CONTRIBUTING.md for development setup and guidelines.

## License

Licensed under either of

 * Apache License, Version 2.0
   ([LICENSE-APACHE](LICENSE-APACHE) or http://www.apache.org/licenses/LICENSE-2.0)
 * MIT license
   ([LICENSE-MIT](LICENSE-MIT) or http://opensource.org/licenses/MIT)

at your option.

## Contribution

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in the work by you, as defined in the Apache-2.0 license, shall be
dual licensed as above, without any additional terms or conditions.
