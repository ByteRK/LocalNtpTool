$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Get-ProjectPython {
  $venvPython = Join-Path $root ".venv\Scripts\python.exe"
  if (Test-Path $venvPython) {
    Write-Host "Using project virtual environment: $venvPython"
    return $venvPython
  }

  $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
  if ($pythonCommand) {
    Write-Host "Using system Python: $($pythonCommand.Source)"
    return $pythonCommand.Source
  }

  throw "Python was not found. Create .venv or install Python first."
}

$pythonExe = Get-ProjectPython
& $pythonExe "run_ntp_tool.py" @args
