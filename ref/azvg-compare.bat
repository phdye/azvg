@echo off
REM azvg-compare.bat - Compare Azure DevOps variable groups
REM Usage: azvg-compare <group_a> <group_b> [options]
REM 
REM Supports specifying variable groups by:
REM   - ID: azvg-compare 23 13
REM   - Name: azvg-compare "Dev" "Prod"
REM   - File path: azvg-compare dev.json prod.json
REM   - Mixed: azvg-compare 23 "Production"
REM 
REM Options:
REM   -n, --names-only    Compare only variable names, not values

python "%~dp0azvg-compare" %*
