[CmdletBinding(PositionalBinding=$false)]
param(
    [string]$RebuildRoot = $env:A1_ATOPILE_REBUILD,
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$AtoArguments
)
$ErrorActionPreference = 'Stop'
$a1Root = Split-Path $PSScriptRoot -Parent
if (-not $RebuildRoot) {
    $commonGit = (& git -C $a1Root rev-parse --path-format=absolute --git-common-dir).Trim()
    $RebuildRoot = Join-Path (Split-Path $commonGit -Parent) '.setup-local/atopile-rebuild'
}
$atoExe = Join-Path $RebuildRoot 'runtime-venv/Scripts/ato.exe'
if (-not (Test-Path -LiteralPath $atoExe)) { throw 'Set A1_ATOPILE_REBUILD to the repaired isolated environment.' }
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:NO_COLOR = '1'
$env:WIN_PD_OVERRIDE_LOCAL_APPDATA = Join-Path $a1Root '.local/profile/Local'
$env:WIN_PD_OVERRIDE_APPDATA = Join-Path $a1Root '.local/profile/Roaming'
$env:FBRK_LOG_DIR = Join-Path $a1Root '.local/ato-logs'
$env:FBRK_TELEMETRY = 'false'
$env:KICAD_CONFIG_HOME = Join-Path $a1Root '.local/kicad'
$env:KICAD9_FOOTPRINT_DIR = Join-Path $env:LOCALAPPDATA 'Programs/KiCad/10.0/share/kicad/footprints'
$env:KICAD10_FOOTPRINT_DIR = $env:KICAD9_FOOTPRINT_DIR
Push-Location (Join-Path $a1Root 'board')
try { & $atoExe @AtoArguments; $resultCode = $LASTEXITCODE }
finally { Pop-Location }
exit $resultCode
