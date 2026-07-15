<#
    Remove o serviço do Windows do Monitor de Páginas (NSSM).
    Rodar como Administrador.
#>

$ErrorActionPreference = "Stop"

$ServiceName = "MonitorPaginasGov"
$Nssm        = "C:\Users\alex.CEOSOFTWAREAD\Documents\Python\NSSM\win64\nssm.exe"

if (-not (Test-Path $Nssm)) {
    throw "nssm.exe não encontrado em $Nssm"
}

& $Nssm stop $ServiceName confirm
& $Nssm remove $ServiceName confirm

Write-Host "Serviço '$ServiceName' removido."
