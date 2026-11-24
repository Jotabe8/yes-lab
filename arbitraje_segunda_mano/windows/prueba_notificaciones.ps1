# Prueba: ¿puede Windows leer las notificaciones de Wallapop que llegan del iPhone por Enlace Móvil?
#
# No envía nada a ningún sitio. Solo lee las notificaciones que ya están en el centro de
# notificaciones de Windows y, con -Vigilar, guarda las de Wallapop en un CSV local.
#
# Uso (PowerShell de Windows, el que viene instalado):
#   powershell -ExecutionPolicy Bypass -File .\prueba_notificaciones.ps1            # prueba única
#   powershell -ExecutionPolicy Bypass -File .\prueba_notificaciones.ps1 -Vigilar   # cada 60 s
param(
    [switch]$Vigilar,
    [int]$Segundos = 60,
    [string]$Filtro = "wallapop",
    [string]$Csv = "$PSScriptRoot\avisos_wallapop.csv"
)

# Los tipos WinRT solo se cargan así en Windows PowerShell 5.1 (.NET Framework). En PowerShell 7
# no existe System.Runtime.WindowsRuntime, así que se relanza el script con powershell.exe.
if ($PSVersionTable.PSEdition -ne 'Desktop') {
    Write-Host "PowerShell $($PSVersionTable.PSVersion) no carga WinRT; relanzando con Windows PowerShell 5.1..."
    $argumentos = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PSCommandPath,
                    '-Segundos', $Segundos, '-Filtro', $Filtro, '-Csv', $Csv)
    if ($Vigilar) { $argumentos += '-Vigilar' }
    & powershell.exe @argumentos
    exit $LASTEXITCODE
}

if ($Vigilar) { try { Start-Transcript -Path "$PSScriptRoot\vigilancia.log" -Append | Out-Null } catch {} }

Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.UI.Notifications.Management.UserNotificationListener, Windows.UI.Notifications, ContentType = WindowsRuntime]
$null = [Windows.UI.Notifications.UserNotification, Windows.UI.Notifications, ContentType = WindowsRuntime]
$null = [Windows.UI.Notifications.KnownNotificationBindings, Windows.UI.Notifications, ContentType = WindowsRuntime]

$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Esperar($operacion, [Type]$tipo) {
    $t = $asTask.MakeGenericMethod($tipo).Invoke($null, @($operacion))
    $t.Wait(-1) | Out-Null
    $t.Result
}

try {
    $listener = [Windows.UI.Notifications.Management.UserNotificationListener]::Current
    # GetAccessStatus no muestra nada; RequestAccessAsync solo hace falta si aún no se ha decidido
    # y, fuera de una app con interfaz, puede fallar, así que se captura el error tal cual.
    $acceso = $listener.GetAccessStatus()
    if ("$acceso" -eq 'Unspecified') {
        try {
            $acceso = Esperar ($listener.RequestAccessAsync()) ([Windows.UI.Notifications.Management.UserNotificationListenerAccessStatus])
        } catch {
            Write-Host "RequestAccessAsync ha fallado: $($_.Exception.GetBaseException().Message)"
        }
    }
} catch {
    Write-Host "No se puede usar UserNotificationListener: $($_.Exception.GetBaseException().Message)"
    exit 2
}
Write-Host "Acceso a notificaciones: $acceso"
if ("$acceso" -ne 'Allowed') {
    Write-Host "Windows no deja leer las notificaciones (estado: $acceso)."
    Write-Host "Revisa Configuración > Privacidad y seguridad > Notificaciones: activa el acceso a las"
    Write-Host "notificaciones y 'Permitir que las aplicaciones de escritorio accedan', y vuelve a probar."
    exit 1
}

function Leer {
    $tipoLista = [System.Collections.Generic.IReadOnlyList[Windows.UI.Notifications.UserNotification]]
    $lista = Esperar ($listener.GetNotificationsAsync([Windows.UI.Notifications.NotificationKinds]::Toast)) $tipoLista
    foreach ($n in $lista) {
        $app = try { $n.AppInfo.DisplayInfo.DisplayName } catch { "" }
        if (-not $app) { $app = try { $n.AppInfo.AppUserModelId } catch { "?" } }
        $b = $n.Notification.Visual.GetBinding([Windows.UI.Notifications.KnownNotificationBindings]::ToastGeneric)
        if (-not $b) { $b = @($n.Notification.Visual.Bindings)[0] }
        $texto = if ($b) { ($b.GetTextElements() | ForEach-Object { $_.Text }) -join " | " } else { "" }
        [pscustomobject]@{ Id = $n.Id; Hora = $n.CreationTime.LocalDateTime; App = $app; Texto = $texto }
    }
}

if (-not $Vigilar) {
    $todas = @(Leer)
    Write-Host "Notificaciones en el centro de notificaciones: $($todas.Count)"
    $todas | Format-Table Hora, App, Texto -AutoSize -Wrap
    $todas | Group-Object App | Sort-Object Count -Descending | Format-Table Count, Name -AutoSize
    $enlace = @($todas | Where-Object { $_.App -match 'Enlace|Phone Link|YourPhone|CrossDevice' })
    Write-Host "Desde Enlace Móvil: $($enlace.Count)"
    $wp = @($todas | Where-Object { "$($_.App) $($_.Texto)" -match $Filtro })
    Write-Host "De Wallapop: $($wp.Count)"
    exit 0
}

# ---- Vigilancia (la lanza la tarea programada que crea instalar.ps1) ----
$raiz = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent   # carpeta que contiene arbitraje_segunda_mano

function Buscar-Python {
    $candidatos = @('py', 'python') + @(Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe" `
        -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | ForEach-Object FullName)
    foreach ($c in $candidatos) {
        try { & $c -c "import sys" 2>$null; if ($LASTEXITCODE -eq 0) { return $c } } catch {}
    }
    return $null
}
$python = Buscar-Python
$env:PYTHONIOENCODING = 'utf-8'
Write-Host "Python: $(if ($python) { $python } else { 'no encontrado (solo se guardará el aviso)' })"

function Evaluar-Aviso([string]$texto) {
    # Último importe con € del texto: "350 €", "1.200€", "349,99 €".
    $m = [regex]::Matches($texto, '(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d{1,2}))?\s?€')
    if ($m.Count -eq 0) { return @{ Precio = ''; Decision = 'sin precio' } }
    $u = $m[$m.Count - 1]
    $precio = ($u.Groups[1].Value -replace '\.', '')
    if ($u.Groups[2].Success) { $precio += '.' + $u.Groups[2].Value }
    if (-not $python) { return @{ Precio = $precio; Decision = 'sin python' } }
    Push-Location $raiz
    $arg = ($texto -replace '"', "'") -replace '^-+', ''   # PS 5.1 rompe las comillas al pasarlas a un exe
    try { $salida = (& $python -m arbitraje_segunda_mano.app.evaluar $arg $precio 2>&1) | Out-String }
    finally { Pop-Location }
    $decision = if ($salida -cmatch 'COMPRAR') { 'COMPRAR' } elseif ($salida -match 'no comprar') { 'no comprar' }
                elseif ($salida -match 'descartado') { 'fuera de catálogo' } else { 'error' }
    return @{ Precio = $precio; Decision = $decision; Detalle = $salida.Trim() }
}

function Avisar([string]$titulo, [string]$texto) {
    # Aviso local de Windows; no sale del PC.
    try {
        $null = [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
        $null = [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime]
        $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $e = { param($t) [Security.SecurityElement]::Escape($t) }
        $xml.LoadXml("<toast><visual><binding template='ToastGeneric'><text>$(& $e $titulo)</text><text>$(& $e $texto)</text></binding></visual></toast>")
        $aumid = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($aumid).Show(
            [Windows.UI.Notifications.ToastNotification]::new($xml))
    } catch { Write-Host "No se pudo mostrar el aviso: $($_.Exception.Message)" }
}

$vistas = @{}
if (Test-Path $Csv) { Import-Csv $Csv | ForEach-Object { $vistas[$_.Id] = $true } }
Write-Host "$(Get-Date) Vigilando cada $Segundos s. Guardando en $Csv."
while ($true) {
    # Un fallo puntual no debe matar la vigilancia (corre oculta desde el Programador de tareas).
    $lote = try { @(Leer) } catch { Write-Host "Error leyendo: $($_.Exception.GetBaseException().Message)"; @() }
    foreach ($n in $lote) {
        if ($vistas.ContainsKey("$($n.Id)")) { continue }
        if ($n.App -match 'PowerShell') { continue }   # nuestros propios avisos
        if ("$($n.App) $($n.Texto)" -notmatch $Filtro) { continue }
        $vistas["$($n.Id)"] = $true
        $ev = try { Evaluar-Aviso $n.Texto } catch { @{ Precio = ''; Decision = "error: $($_.Exception.Message)" } }
        $fila = [pscustomobject]@{ Id = $n.Id; Hora = $n.Hora; App = $n.App; Texto = $n.Texto
                                   Precio = $ev.Precio; Decision = $ev.Decision }
        try { $fila | Export-Csv $Csv -Append -NoTypeInformation -Encoding UTF8 } catch { Write-Host "CSV: $_" }
        Write-Host "$($n.Hora)  [$($ev.Decision)]  $($n.Texto)"
        if ($ev.Decision -eq 'COMPRAR') {
            $resumen = ($ev.Detalle -split "`r?`n" | Where-Object { $_ -match 'Margen|Modelo' }) -join ' · '
            Avisar "Arbitraje: COMPRAR ($($ev.Precio) €)" "$($n.Texto)`n$resumen"
        }
    }
    Start-Sleep -Seconds $Segundos
}
