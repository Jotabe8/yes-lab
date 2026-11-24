# Instalador de los avisos de Wallapop en Windows (todo en local; no envía datos fuera del PC).
#
# Qué hace, en orden:
#   1. Descarga (o actualiza) los archivos del repositorio en Documents\arbitraje.
#   2. Comprueba Enlace Móvil y Python; si faltan, los instala con winget.
#   3. Evita que el PC se suspenda enchufado (las notificaciones solo llegan con el PC despierto).
#   4. Prueba el acceso a las notificaciones; si Windows no lo da, abre los ajustes y espera.
#   5. Crea la tarea programada "Arbitraje - avisos Wallapop": al iniciar sesión (y cada 15 min
#      si se hubiera parado) ejecuta prueba_notificaciones.ps1 -Vigilar en una ventana oculta.
#
# Uso:   powershell -ExecutionPolicy Bypass -File .\instalar.ps1
# Quitar: powershell -ExecutionPolicy Bypass -File .\instalar.ps1 -Quitar
param(
    [switch]$Quitar,
    [string]$Rama = 'claude/inspiring-heisenberg-crznlw',
    [string]$Destino = "$env:USERPROFILE\Documents\arbitraje",
    [switch]$SinPython,
    [switch]$PermitirSuspension
)

if ($PSVersionTable.PSEdition -ne 'Desktop') {
    $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PSCommandPath, '-Rama', $Rama, '-Destino', $Destino)
    if ($Quitar) { $a += '-Quitar' }; if ($SinPython) { $a += '-SinPython' }
    if ($PermitirSuspension) { $a += '-PermitirSuspension' }
    & powershell.exe @a; exit $LASTEXITCODE
}

$Tarea = 'Arbitraje - avisos Wallapop'
$win = Join-Path $Destino 'arbitraje_segunda_mano\windows'
$script = Join-Path $win 'prueba_notificaciones.ps1'

function Parar-Vigilancia {
    Stop-ScheduledTask -TaskName $Tarea -ErrorAction SilentlyContinue
    Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'prueba_notificaciones\.ps1.*-Vigilar' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}
function Paso($t) { Write-Host ""; Write-Host "== $t" -ForegroundColor Cyan }

if ($Quitar) {
    Parar-Vigilancia
    Unregister-ScheduledTask -TaskName $Tarea -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Tarea '$Tarea' quitada. Los archivos de $Destino no se han tocado."
    exit 0
}

$log = Join-Path $env:TEMP 'instalar_arbitraje.log'
try { Start-Transcript -Path $log | Out-Null } catch {}

# ---- 1. Archivos ----
Paso "1. Archivos en $Destino"
if (Test-Path (Join-Path $Destino '.git')) {
    Write-Host "Es un clon de git: no descargo nada. Actualízalo con: git -C `"$Destino`" pull"
} else {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $base = "https://raw.githubusercontent.com/jotabe8/yes-lab/$Rama"
    $archivos = @(
        'arbitraje_segunda_mano/__init__.py',
        'arbitraje_segunda_mano/app/__init__.py',
        'arbitraje_segunda_mano/app/catalogo.py',
        'arbitraje_segunda_mano/app/puntuacion.py',
        'arbitraje_segunda_mano/app/evaluar.py',
        'arbitraje_segunda_mano/app/catalogo.csv',
        'arbitraje_segunda_mano/windows/prueba_notificaciones.ps1',
        'arbitraje_segunda_mano/windows/instalar.ps1'
    )
    foreach ($f in $archivos) {
        $local = Join-Path $Destino ($f -replace '/', '\')
        # El catálogo se rellena a mano: si ya existe, no se pisa.
        if ($f -like '*catalogo.csv' -and (Test-Path $local)) { Write-Host "  (se conserva) $f"; continue }
        New-Item -ItemType Directory -Force -Path (Split-Path $local) | Out-Null
        try {
            Invoke-WebRequest -UseBasicParsing -Uri "$base/$f" -OutFile $local
            Write-Host "  ok  $f"
        } catch {
            Write-Host "  ERROR descargando $f : $($_.Exception.Message)" -ForegroundColor Red
            exit 3
        }
    }
}

# ---- 2. Enlace Móvil y Python ----
Paso "2. Enlace Móvil y Python"
$winget = Get-Command winget -ErrorAction SilentlyContinue
$enlace = Get-AppxPackage -Name Microsoft.YourPhone -ErrorAction SilentlyContinue
if (-not $enlace) { $enlace = Get-AppxPackage -Name *CrossDevice* -ErrorAction SilentlyContinue }
if ($enlace) {
    Write-Host "Enlace Móvil instalado: $($enlace[0].Name) $($enlace[0].Version)"
} elseif ($winget) {
    Write-Host "Enlace Móvil no está instalado: instalando desde Microsoft Store..."
    & winget install --id 9NMPJ99VJBWV --source msstore --accept-package-agreements --accept-source-agreements
} else {
    Write-Host "Enlace Móvil no está instalado y no hay winget: abro la Store para instalarlo."
    Start-Process 'ms-windows-store://pdp/?productid=9NMPJ99VJBWV'
}

function Hay-Python {
    foreach ($c in @('py', 'python') + @(Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe" -ErrorAction SilentlyContinue | ForEach-Object FullName)) {
        try { & $c -c "import sys" 2>$null; if ($LASTEXITCODE -eq 0) { return $c } } catch {}
    }
}
$py = Hay-Python
if ($py) { Write-Host "Python: $py" }
elseif ($SinPython) { Write-Host "Sin Python: los avisos se guardarán, pero sin evaluar el margen." }
elseif ($winget) {
    Write-Host "Python no está: instalando Python 3.12 para este usuario (sirve para calcular el margen)..."
    & winget install --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
    $py = Hay-Python; Write-Host "Python: $(if ($py) { $py } else { 'no se ha podido instalar' })"
} else { Write-Host "Python no está y no hay winget: instálalo desde python.org si quieres el cálculo de margen." }

# ---- 3. Que el PC no se duerma enchufado ----
Paso "3. Suspensión"
if ($PermitirSuspension) { Write-Host "Se deja como está (-PermitirSuspension)." }
else {
    & powercfg /change standby-timeout-ac 0; & powercfg /change hibernate-timeout-ac 0
    Write-Host "Enchufado, el PC ya no se suspende (la pantalla sí puede apagarse)."
}

# ---- 4. Acceso a las notificaciones ----
Paso "4. Prueba de acceso a las notificaciones"
for ($intento = 1; $intento -le 3; $intento++) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $script
    $codigo = $LASTEXITCODE
    if ($codigo -eq 0) { break }
    if ($codigo -eq 2) {
        Write-Host "La API de notificaciones no funciona en este Windows (ver el error de arriba). No creo la tarea." -ForegroundColor Red
        exit 2
    }
    Write-Host ""
    Write-Host "Windows no da acceso todavía. Abro los ajustes: activa 'Acceso a las notificaciones'" -ForegroundColor Yellow
    Write-Host "y 'Permitir que las aplicaciones de escritorio accedan a tus notificaciones'." -ForegroundColor Yellow
    Start-Process 'ms-settings:privacy-notifications'
    Read-Host "Pulsa Intro cuando lo hayas activado (intento $intento de 3)"
}
if ($codigo -ne 0) { Write-Host "Sigue sin acceso. Creo la tarea igualmente: empezará a funcionar en cuanto lo actives." -ForegroundColor Yellow }

# ---- 5. Tarea programada ----
Paso "5. Tarea programada '$Tarea'"
Parar-Vigilancia
# wscript con estilo 0 = sin ventana. Espera (True) para que la tarea siga "en ejecución" mientras
# vigila y la repetición cada 15 min no lance una segunda copia (MultipleInstances IgnoreNew).
$vbs = Join-Path $win 'lanzar_oculto.vbs'
$cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$script`" -Vigilar"
Set-Content -Path $vbs -Encoding Unicode -Value ('CreateObject("WScript.Shell").Run "' + ($cmd -replace '"', '""') + '", 0, True')

$usuario = "$env:USERDOMAIN\$env:USERNAME"
$accion = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument "`"$vbs`"" -WorkingDirectory $win
$alIniciar = New-ScheduledTaskTrigger -AtLogOn -User $usuario
$alIniciar.Repetition = (New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 15)).Repetition
$ajustes = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
    -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero)
$quien = New-ScheduledTaskPrincipal -UserId $usuario -LogonType Interactive -RunLevel Limited
try {
    Register-ScheduledTask -TaskName $Tarea -Action $accion -Trigger $alIniciar -Settings $ajustes -Principal $quien `
        -Description 'Lee las notificaciones de Wallapop (Enlace Móvil) y las guarda en avisos_wallapop.csv. Solo local.' -Force | Out-Null
    Start-ScheduledTask -TaskName $Tarea
} catch {
    Write-Host "No se pudo crear la tarea: $($_.Exception.Message)" -ForegroundColor Red
    exit 4
}
Start-Sleep -Seconds 8
$estado = (Get-ScheduledTask -TaskName $Tarea).State
$vivo = @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object { $_.CommandLine -match 'prueba_notificaciones\.ps1.*-Vigilar' }).Count -gt 0

Paso "Resumen"
Write-Host "Tarea: $estado  ·  vigilancia en marcha: $(if ($vivo) { 'sí' } else { 'no (mira vigilancia.log)' })"
Write-Host "Avisos:   $win\avisos_wallapop.csv"
Write-Host "Registro: $win\vigilancia.log"
Write-Host "Este informe: $log"
try { Stop-Transcript | Out-Null } catch {}
