param(
    [Parameter(Mandatory)][string]$Session,
    [Parameter(Mandatory)][string]$Script,
    [Parameter(Mandatory)][string]$Evidence,
    [int]$TimeoutMs = 60000
)
$ErrorActionPreference = 'Stop'
$a3Root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$scriptPath = [IO.Path]::GetFullPath((Join-Path $a3Root $Script))
$evidencePath = [IO.Path]::GetFullPath((Join-Path $a3Root $Evidence))
foreach ($a3Path in @($scriptPath, $evidencePath)) {
    if (-not $a3Path.StartsWith($a3Root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'All script and evidence paths must be inside the A-3 directory.'
    }
}
$raw = & 'C:/Program Files/EasyEDA-Pro/easyeda-pro.exe' invoke --session $Session --ext-uuid eda --timeout $TimeoutMs --code-file $scriptPath | Out-String
[IO.File]::WriteAllText($evidencePath, $raw, [Text.UTF8Encoding]::new($false))
$result = $raw | ConvertFrom-Json
if (-not $result.ok) { throw $raw }
$raw
