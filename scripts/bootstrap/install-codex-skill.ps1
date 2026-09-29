[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$Source,
  [Parameter(Mandatory = $true)]
  [string]$Target,
  # Link one file (CLAUDE.md -> AGENTS.md) with a symbolic link instead of a skill directory junction.
  [switch]$File,
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$conflictHelp = 'resolve it as described in scripts/bootstrap/README.md (Codex 연결 충돌)'

function Normalize-Path([string]$Path) {
  return [IO.Path]::GetFullPath($Path).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
}

function Same-Path([string]$Left, [string]$Right) {
  return [string]::Equals((Normalize-Path $Left), (Normalize-Path $Right), [StringComparison]::OrdinalIgnoreCase)
}

if ($File) {
  if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
    if (Test-Path -LiteralPath $Source) { throw "Codex link source is not a file: $Source" }
    throw "Codex link source missing: $Source"
  }
  $linkType = 'SymbolicLink'
} else {
  if (-not (Test-Path -LiteralPath (Join-Path $Source 'SKILL.md') -PathType Leaf)) {
    throw "Codex skill source missing or invalid: $Source (SKILL.md 없음)"
  }
  $linkType = 'Junction'
}

$sourcePath = Normalize-Path $Source
$parent = Split-Path -Parent $Target
$item = Get-Item -LiteralPath $Target -Force -ErrorAction SilentlyContinue

if ($null -ne $item) {
  $isReparsePoint = (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)
  if (-not $isReparsePoint) {
    throw "Codex link target exists and is not a link; left unchanged: $Target — $conflictHelp"
  }

  $resolvedTarget = @($item.ResolvedTarget, $item.Target, $item.LinkTarget) |
    Where-Object { $_ } | Select-Object -First 1
  if ($resolvedTarget) {
    $resolvedTarget = if ([IO.Path]::IsPathRooted($resolvedTarget)) {
      $resolvedTarget
    } else {
      Join-Path $parent $resolvedTarget
    }
  }
  if ($resolvedTarget -and (Same-Path $resolvedTarget $sourcePath)) {
    Write-Output "Codex link already points to source: $Target"
    exit 0
  }
  throw "Codex link target is an existing link to another or unknown source; left unchanged: $Target — $conflictHelp"
}

if ($DryRun) {
  Write-Output "[dry-run] create $($linkType.ToLower()): $Target -> $sourcePath"
  exit 0
}

New-Item -ItemType Directory -Path $parent -Force | Out-Null
if (-not $File) {
  New-Item -ItemType Junction -Path $Target -Target $sourcePath | Out-Null
} else {
  # A file cannot be a junction. Windows PowerShell 5.1's New-Item asks for admin even in
  # Developer Mode; CreateSymbolicLinkW with ALLOW_UNPRIVILEGED_CREATE (0x2) does not, and
  # calling it directly keeps the paths away from cmd's metacharacters (&, ^, %VAR%).
  Add-Type -Namespace CodexLink -Name Native -MemberDefinition @'
[DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
[return: MarshalAs(UnmanagedType.I1)]
public static extern bool CreateSymbolicLinkW(string link, string target, int flags);
'@
  $made = [CodexLink.Native]::CreateSymbolicLinkW($Target, $sourcePath, 0x2)
  $code = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
  if (-not $made -and $code -eq 87) {  # Windows before 1703 rejects the unprivileged flag
    $made = [CodexLink.Native]::CreateSymbolicLinkW($Target, $sourcePath, 0)
    $code = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
  }
  if (-not $made) {
    if ($code -eq 1314) { throw "Codex link: creating a symbolic link needs Developer Mode or an administrator shell: $Target" }
    throw "Codex link: CreateSymbolicLinkW failed (Win32 error $code): $Target -> $sourcePath"
  }
  $made = Get-Item -LiteralPath $Target -Force
  $madeTarget = @($made.Target) | Select-Object -First 1
  if (-not $madeTarget -or -not (Same-Path $madeTarget $sourcePath)) {
    throw "Codex link: created $Target but it does not point to $sourcePath"
  }
}
Write-Output "Created Codex $($linkType.ToLower()): $Target -> $sourcePath"
