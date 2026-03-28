# Creates .venv in this repo and installs requirements.txt (Siteworks / Streamlit).
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$venv = Join-Path $root ".venv"
$py = Join-Path $venv "Scripts\python.exe"
$pip = Join-Path $venv "Scripts\pip.exe"

if (-not (Test-Path $py)) {
    Write-Host "Creating virtual environment in .venv ..."
    python -m venv $venv
}
Write-Host "Installing dependencies ..."
& $pip install -r (Join-Path $root "requirements.txt")
Write-Host ""
Write-Host "Done. In Cursor/VS Code: Python: Select Interpreter -> .\.venv\Scripts\python.exe"
Write-Host "Then run: streamlit run app.py"
