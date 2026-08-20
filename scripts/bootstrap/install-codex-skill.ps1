[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$Source,
  [Parameter(Mandatory = $true)]
  [string]$Target,
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

function Normalize-Path([string]$Path) {
  return [IO.Path]::GetFullPath($Path).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
}

function Same-Path([string]$Left, [string]$Right) {
  return [string]::Equals((Normalize-Path $Left), (Normalize-Path $Right), [StringComparison]::OrdinalIgnoreCase)
}

if (-not (Test-Path -LiteralPath (Join-Path $Source 'SKILL.md') -PathType Leaf)) {
  throw "Codex skill source missing or invalid: $Source (SKILL.md 없음)"
}

$sourcePath = Normalize-Path $Source
$parent = Split-Path -Parent $Target
$item = Get-Item -LiteralPath $Target -Force -ErrorAction SilentlyContinue

if ($null -ne $item) {
  $isReparsePoint = (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)
  if (-not $isReparsePoint) {
    throw "Codex skill target exists and is not a link; left unchanged: $Target"
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
    Write-Output "Codex jira-worklog link already points to source: $Target"
    exit 0
  }
  throw "Codex skill target is an existing link to another or unknown source; left unchanged: $Target"
}

if ($DryRun) {
  Write-Output "[dry-run] create junction: $Target -> $sourcePath"
  exit 0
}

New-Item -ItemType Directory -Path $parent -Force | Out-Null
New-Item -ItemType Junction -Path $Target -Target $sourcePath | Out-Null
Write-Output "Created Codex jira-worklog junction: $Target -> $sourcePath"
