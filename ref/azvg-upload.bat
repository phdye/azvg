@echo off
REM azvg-upload.bat - Upload/merge Azure DevOps variable groups
REM Usage: azvg-upload <vg-file|vg-name|vg-id> [--new]
REM 
REM Supports specifying variable groups by:
REM   - File path: azvg-upload path/to/file.json
REM   - ID: azvg-upload 23
REM   - Name: azvg-upload "My Variable Group"
REM 
REM Use --new flag to create a new variable group

python "%~dp0azvg-upload" %*
