<#
    Registra o Monitor de Páginas como Serviço do Windows via NSSM.
    Rodar como Administrador, uma única vez (ou após reinstalar/mudar caminhos).
#>

$ErrorActionPreference = "Stop"

$ServiceName = "MonitorPaginasGov"
$Nssm        = "C:\Users\alex.CEOSOFTWAREAD\Documents\Python\NSSM\win64\nssm.exe"
$BackendDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe   = Join-Path $BackendDir "venv\Scripts\python.exe"
$LogFile     = Join-Path $BackendDir "data\service.log"

if (-not (Test-Path $Nssm)) {
    throw "nssm.exe não encontrado em $Nssm"
}
if (-not (Test-Path $PythonExe)) {
    throw "venv não encontrado em $PythonExe. Crie o venv antes (veja README.md)."
}

# remove instalação anterior, se existir, para permitir reinstalar com segurança
$prevErrorPref = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
& $Nssm status $ServiceName *> $null
$statusExitCode = $LASTEXITCODE
$ErrorActionPreference = $prevErrorPref

if ($statusExitCode -eq 0) {
    & $Nssm stop $ServiceName confirm | Out-Null
    & $Nssm remove $ServiceName confirm | Out-Null
}

& $Nssm install $ServiceName $PythonExe "-m uvicorn main:app --host 0.0.0.0 --port 8000"
& $Nssm set $ServiceName AppDirectory $BackendDir
& $Nssm set $ServiceName AppStdout $LogFile
& $Nssm set $ServiceName AppStderr $LogFile
& $Nssm set $ServiceName AppRotateFiles 1
& $Nssm set $ServiceName AppRotateBytes 1048576
& $Nssm set $ServiceName Start SERVICE_AUTO_START
& $Nssm set $ServiceName AppExit Default Restart
& $Nssm set $ServiceName AppRestartDelay 5000
& $Nssm set $ServiceName DisplayName "Monitor de paginas GOV"
& $Nssm set $ServiceName Description "Dashboard + agendador de monitoramento de páginas governamentais (FastAPI/Uvicorn + APScheduler)."

& $Nssm start $ServiceName

Write-Host ""
Write-Host "Serviço '$ServiceName' instalado e iniciado."
Write-Host "Dashboard: http://localhost:8000"
Write-Host "Logs: $LogFile"
Write-Host "Gerenciar em: services.msc"
