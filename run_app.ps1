$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

# Use installed Python 3.13 launcher directly to avoid broken venv activation on some systems.
& "C:\WINDOWS\py.exe" -3.13 .\main.py
