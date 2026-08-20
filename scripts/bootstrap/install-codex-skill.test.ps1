[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$helper = Join-Path $PSScriptRoot 'install-codex-skill.ps1'
$root = Join-Path ([IO.Path]::GetTempPath()) ('codex-skill-link-test-' + [guid]::NewGuid().ToString('N'))
$source = Join-Path $root 'source with spaces'
$target = Join-Path $root 'nested\target with spaces'
$other = Join-Path $root 'other'

function Invoke-Installer([string]$SourcePath, [string]$TargetPath, [switch]$DryRun) {
  $global:LASTEXITCODE = 0
  try {
    if ($DryRun) {
      & $helper -Source $SourcePath -Target $TargetPath -DryRun | Out-Null
    } else {
      & $helper -Source $SourcePath -Target $TargetPath | Out-Null
    }
    return @{ Success = ($LASTEXITCODE -eq 0); Error = $null }
  } catch {
    return @{ Success = $false; Error = $_.Exception.Message }
  }
}

try {
  New-Item -ItemType Directory -Path $source,$other -Force | Out-Null
  Set-Content -LiteralPath (Join-Path $source 'SKILL.md') -Value '---`nname: jira-worklog`n---'

  $created = Invoke-Installer $source $target
  if (-not $created.Success) { throw "target creation failed: $($created.Error)" }
  $targetItem = Get-Item -LiteralPath $target -Force
  if (($targetItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) { throw 'target is not a junction' }

  $rerun = Invoke-Installer $source $target
  if (-not $rerun.Success) { throw "idempotent rerun failed: $($rerun.Error)" }

  $dryRunTarget = Join-Path $root 'dry-run-target'
  $dryRun = Invoke-Installer $source $dryRunTarget -DryRun
  if (-not $dryRun.Success -or (Test-Path -LiteralPath $dryRunTarget)) { throw 'dry-run changed the target' }

  $dirTarget = Join-Path $root 'real-directory'
  New-Item -ItemType Directory -Path $dirTarget -Force | Out-Null
  $directoryConflict = Invoke-Installer $source $dirTarget
  if ($directoryConflict.Success -or $directoryConflict.Error -notmatch 'not a link') { throw 'real directory conflict was not rejected' }

  $otherLink = Join-Path $root 'other-link'
  New-Item -ItemType Junction -Path $otherLink -Target $other | Out-Null
  $linkConflict = Invoke-Installer $source $otherLink
  if ($linkConflict.Success -or $linkConflict.Error -notmatch 'existing link') { throw 'other link conflict was not rejected' }

  $danglingSource = Join-Path $root 'dangling-source'
  $danglingLink = Join-Path $root 'dangling-link'
  New-Item -ItemType Directory -Path $danglingSource -Force | Out-Null
  New-Item -ItemType Junction -Path $danglingLink -Target $danglingSource | Out-Null
  Remove-Item -LiteralPath $danglingSource -Recurse -Force
  $danglingConflict = Invoke-Installer $source $danglingLink
  if ($danglingConflict.Success -or $danglingConflict.Error -notmatch 'existing link') { throw 'dangling link conflict was not rejected' }

  $missingSource = Join-Path $root 'missing-source'
  $missing = Invoke-Installer $missingSource (Join-Path $root 'missing-target')
  if ($missing.Success -or $missing.Error -notmatch 'source missing') { throw 'missing source was not rejected' }

  Write-Output 'install-codex-skill.ps1 state matrix passed'
} finally {
  Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
