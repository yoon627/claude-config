[CmdletBinding()]
param(
    [string]$Event = 'Stop',
    [ValidateSet('Asterisk','Beep','Exclamation','Hand','Question')]
    [string]$Sound = 'Asterisk',
    [switch]$DryRun
)

$ErrorActionPreference = 'SilentlyContinue'

$json = $null
try {
    $raw = [Console]::In.ReadToEnd()
    if ($raw) { $json = $raw | ConvertFrom-Json }
} catch {}

$msg = $null
if ($json -and $json.message) { $msg = [string]$json.message }
if (-not $msg) {
    $msg = if ($Event -eq 'Notification') { '입력 대기' } else { '응답 완료' }
}

$candidates = @()

if ($json -and $json.cwd) {
    try {
        $cwdBase = Split-Path -Path ([string]$json.cwd) -Leaf
        if ($cwdBase) { $candidates += [pscustomobject]@{Source='cwd'; Value=$cwdBase} }
    } catch {}
}

try {
    $cur = $PID
    for ($i = 0; $i -lt 15; $i++) {
        $p = Get-CimInstance Win32_Process -Filter "ProcessId = $cur" -ErrorAction SilentlyContinue
        if (-not $p) { break }
        if ($p.Name -eq 'WindowsTerminal.exe') {
            $proc = Get-Process -Id $cur -ErrorAction SilentlyContinue
            if ($proc -and $proc.MainWindowTitle) {
                $candidates += [pscustomobject]@{Source='wt'; Value=$proc.MainWindowTitle}
                break
            }
        }
        $cur = [int]$p.ParentProcessId
        if (-not $cur -or $cur -eq 0) { break }
    }
} catch {}

$reNoise = '\.exe$|^Administrator:|^bash$|^pwsh$|^powershell$|^cmd$|^Windows PowerShell$|^Command Prompt$'
$tab = $null
$picked = $null
foreach ($c in $candidates) {
    $v = ([string]$c.Value).Trim()
    if ($v -and $v -notmatch $reNoise) {
        $tab = $v
        $picked = $c.Source
        break
    }
}

$title = if ($tab) { $tab } else { 'Claude' }

if ($env:CLAUDE_NOTIFY_DEBUG -eq '1') {
    try {
        $logPath = Join-Path $env:TEMP 'claude-notify-debug.json'
        [pscustomobject]@{
            Timestamp  = (Get-Date).ToString('o')
            Event      = $Event
            Picked     = $picked
            Tab        = $tab
            Title      = $title
            Message    = $msg
            Candidates = $candidates
            Cwd        = if ($json) { $json.cwd } else { $null }
            SessionId  = if ($json) { $json.session_id } else { $null }
            WrapperPID = $PID
        } | ConvertTo-Json -Depth 4 | Set-Content -Path $logPath -Encoding UTF8
    } catch {}
}

if ($DryRun) {
    [pscustomobject]@{
        Event      = $Event
        Sound      = $Sound
        Message    = $msg
        Title      = $title
        Picked     = $picked
        Tab        = $tab
        Candidates = $candidates
        Cwd        = if ($json) { $json.cwd } else { $null }
        SessionId  = if ($json) { $json.session_id } else { $null }
    } | ConvertTo-Json -Depth 4
    return
}

& "$PSScriptRoot/notify.ps1" -Title $title -Message $msg -Sound $Sound
