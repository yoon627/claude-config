[CmdletBinding()]
param(
    [string]$Title = 'Claude Code',
    [string]$Message = 'Done',
    [ValidateSet('Asterisk','Beep','Exclamation','Hand','Question')]
    [string]$Sound = 'Asterisk'
)

$ErrorActionPreference = 'SilentlyContinue'

try { [System.Media.SystemSounds]::$Sound.Play() } catch {}

try {
    Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class WinFlash {
    [StructLayout(LayoutKind.Sequential)]
    public struct FLASHWINFO {
        public uint cbSize;
        public IntPtr hwnd;
        public uint dwFlags;
        public uint uCount;
        public uint dwTimeout;
    }
    [DllImport("user32.dll")]
    public static extern bool FlashWindowEx(ref FLASHWINFO pwfi);
}
"@ -ErrorAction SilentlyContinue

    $hwnd = [IntPtr]::Zero
    $cur = $PID
    for ($i = 0; $i -lt 12; $i++) {
        $p = Get-CimInstance Win32_Process -Filter "ProcessId = $cur" -ErrorAction SilentlyContinue
        if (-not $p) { break }
        $proc = Get-Process -Id $cur -ErrorAction SilentlyContinue
        if ($proc -and $proc.MainWindowHandle -ne [IntPtr]::Zero) {
            $hwnd = $proc.MainWindowHandle
            break
        }
        $cur = [int]$p.ParentProcessId
        if (-not $cur -or $cur -eq 0) { break }
    }

    if ($hwnd -eq [IntPtr]::Zero) {
        $wt = Get-Process -Name WindowsTerminal -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne [IntPtr]::Zero } | Select-Object -First 1
        if ($wt) { $hwnd = $wt.MainWindowHandle }
    }

    if ($hwnd -ne [IntPtr]::Zero) {
        $fi = New-Object WinFlash+FLASHWINFO
        $fi.cbSize = [uint32][System.Runtime.InteropServices.Marshal]::SizeOf($fi)
        $fi.hwnd = $hwnd
        $fi.dwFlags = [uint32]15  # FLASHW_ALL | FLASHW_TIMERNOFG
        $fi.uCount = [uint32]0
        $fi.dwTimeout = [uint32]0
        [WinFlash]::FlashWindowEx([ref]$fi) | Out-Null
    }
} catch {}

try {
    [void][Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
    [void][Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime]

    $titleEsc   = [System.Security.SecurityElement]::Escape($Title)
    $messageEsc = [System.Security.SecurityElement]::Escape($Message)

    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml(@"
<toast>
  <visual>
    <binding template="ToastGeneric">
      <text>$titleEsc</text>
      <text>$messageEsc</text>
    </binding>
  </visual>
</toast>
"@)

    $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Microsoft.PowerShell').Show($toast)
    return
} catch {}

try {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    $ni = New-Object System.Windows.Forms.NotifyIcon
    $ni.Icon = [System.Drawing.SystemIcons]::Information
    $ni.BalloonTipTitle = $Title
    $ni.BalloonTipText  = $Message
    $ni.Visible = $true
    $ni.ShowBalloonTip(5000)
} catch {}
