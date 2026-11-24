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

$vistas = @{}
if (Test-Path $Csv) { Import-Csv $Csv | ForEach-Object { $vistas[$_.Id] = $true } }
Write-Host "Vigilando cada $Segundos s. Guardando en $Csv (Ctrl+C para parar)."
while ($true) {
    # Un fallo puntual al leer no debe matar la vigilancia (corre oculta desde el Programador de tareas).
    $lote = try { @(Leer) } catch { Write-Host "Error leyendo: $($_.Exception.GetBaseException().Message)"; @() }
    foreach ($n in $lote) {
        if ($vistas.ContainsKey("$($n.Id)")) { continue }
        if ("$($n.App) $($n.Texto)" -notmatch $Filtro) { continue }
        $vistas["$($n.Id)"] = $true
        $n | Export-Csv $Csv -Append -NoTypeInformation -Encoding UTF8
        Write-Host "$($n.Hora)  $($n.Texto)"
    }
    Start-Sleep -Seconds $Segundos
}
