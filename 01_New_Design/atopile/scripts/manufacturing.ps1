$ErrorActionPreference = 'Stop'
$a1 = Split-Path $PSScriptRoot -Parent
$cli = Join-Path $env:LOCALAPPDATA 'Programs/KiCad/10.0/bin/kicad-cli.exe'
$pcb = Join-Path $a1 'board/a1.kicad_pcb'
$dest = Join-Path $a1 'manufacturing/review-only'
New-Item -ItemType Directory -Force $dest | Out-Null
& $cli pcb export gerbers --layers 'F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,Edge.Cuts' --check-zones -o "$dest/" $pcb
if ($LASTEXITCODE) { throw 'Gerber export failed' }
& $cli pcb export drill --format excellon --excellon-units mm --excellon-separate-th --generate-map --map-format pdf --generate-report -o "$dest/" $pcb
if ($LASTEXITCODE) { throw 'Drill export failed' }
& $cli pcb export pos --format csv --units mm --side both -o "$dest/placement.csv" $pcb
if ($LASTEXITCODE) { throw 'Position export failed' }
Copy-Item "$a1/reports/bom.csv" "$dest/bom.csv"
Get-ChildItem $dest -File | Get-FileHash -Algorithm SHA256 | ForEach-Object {
    '{0}  {1}' -f $_.Hash.ToLowerInvariant(), (Split-Path $_.Path -Leaf)
} | Set-Content "$a1/manufacturing/SHA256SUMS.txt" -Encoding utf8
Compress-Archive -Path "$dest/*" -DestinationPath "$a1/manufacturing/A1-REVIEW-ONLY.zip" -Force
