@echo off
REM azvg-down.bat - Download Azure DevOps variable groups
REM Usage: azvg-down <vg-name|vg-id> [--all]
REM 
REM Supports specifying variable groups by:
REM   - ID: azvg-down 23
REM   - Name: azvg-down "My Variable Group"
REM   - All: azvg-down --all

python "%~dp0azvg-down" %*
