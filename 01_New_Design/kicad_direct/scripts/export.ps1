$ErrorActionPreference = 'Stop'
$designRoot = Split-Path $PSScriptRoot -Parent
$cli = Join-Path $env:LOCALAPPDATA 'Programs/KiCad/10.0/bin/kicad-cli.exe'
$sch = Join-Path $designRoot 'a2_usb_uart.kicad_sch'
$pcb = Join-Path $designRoot 'a2_usb_uart.kicad_pcb'
$report = Join-Path $designRoot 'reports'
$fab = Join-Path $designRoot 'manufacturing_review'
New-Item -ItemType Directory -Force -Path $fab | Out-Null
$log = Join-Path $report 'export_log.txt'
Set-Content $log 'KiCad CLI validation and local review exports; no upload/order.'
function Invoke-KiCad([string[]]$Arguments) {
    Add-Content $log ('kicad-cli ' + ($Arguments -join ' '))
    $output = & $cli @Arguments 2>> (Join-Path $report 'cli_stderr.txt')
    $exit = $LASTEXITCODE
    $output | Tee-Object -FilePath $log -Append
    Add-Content $log "Exit code: $exit"
    if ($exit -ne 0) { throw "KiCad exited with $exit" }
}
Invoke-KiCad @('sch','erc','--format','json','--exit-code-violations','-o',"$report/erc_final.json",$sch)
Invoke-KiCad @('pcb','drc','--format','json','--schematic-parity','--exit-code-violations','-o',"$report/drc_final.json",$pcb)
Invoke-KiCad @('sch','export','netlist','--format','kicadxml','-o',"$report/schematic.net.xml",$sch)
Invoke-KiCad @('sch','export','pdf','-o',"$report/schematic.pdf",$sch)
Invoke-KiCad @('sch','export','svg','-o',"$report/schematic/",$sch)
Invoke-KiCad @('pcb','export','gerbers','--layers','F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,F.Paste,Edge.Cuts','--use-drill-file-origin','--check-zones','-o',"$fab/gerbers/",$pcb)
Invoke-KiCad @('pcb','export','drill','--drill-origin','plot','--excellon-separate-th','--generate-map','--map-format','pdf','--generate-report','--report-path',"$fab/drill_report.txt",'-o',"$fab/drill/",$pcb)
Invoke-KiCad @('pcb','export','pos','--format','csv','--units','mm','--side','front','--use-drill-file-origin','-o',"$fab/positions_front.csv",$pcb)
Invoke-KiCad @('pcb','export','pdf','--mode-multipage','--scale','0','--layers','F.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Fab,Edge.Cuts','-o',"$report/pcb_layers.pdf",$pcb)
Copy-Item -LiteralPath "$report/bom.csv" -Destination "$fab/bom.csv" -Force
Get-ChildItem -LiteralPath $fab -File -Recurse | Get-FileHash -Algorithm SHA256 |
    Select-Object @{n='File';e={$_.Path.Substring($fab.Length+1)}},Hash |
    Export-Csv -LiteralPath "$report/manufacturing_sha256.csv" -NoTypeInformation
