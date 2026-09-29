[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
# Junctions exist only on Windows; verify.sh reads exit 77 as a visible skip.
if ($PSVersionTable.PSEdition -eq 'Core' -and -not $IsWindows) {
  Write-Output 'install-codex-skill.test.ps1: Windows only (junction)'
  exit 77
}
$helper = Join-Path $PSScriptRoot 'install-codex-skill.ps1'
$root = Join-Path ([IO.Path]::GetTempPath()) ('codex-skill-link-test-' + [guid]::NewGuid().ToString('N'))
$source = Join-Path $root 'source with spaces'
$target = Join-Path $root 'nested\target with spaces'
$other = Join-Path $root 'other'

function Invoke-Installer([string]$SourcePath, [string]$TargetPath, [switch]$DryRun, [switch]$File) {
  $global:LASTEXITCODE = 0
  $linkArgs = @{ Source = $SourcePath; Target = $TargetPath }
  if ($DryRun) { $linkArgs.DryRun = $true }
  if ($File) { $linkArgs.File = $true }
  try {
    & $helper @linkArgs | Out-Null
    return @{ Success = ($LASTEXITCODE -eq 0); Error = $null }
  } catch {
    return @{ Success = $false; Error = $_.Exception.Message }
  }
}

function Test-IsLink([string]$Path) {
  $item = Get-Item -LiteralPath $Path -Force
  return (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)
}

try {
  New-Item -ItemType Directory -Path $source,$other -Force | Out-Null
  Set-Content -LiteralPath (Join-Path $source 'SKILL.md') -Value '---`nname: jira-worklog`n---'

  # --- directory mode (junction) ---
  $created = Invoke-Installer $source $target
  if (-not $created.Success) { throw "target creation failed: $($created.Error)" }
  if (-not (Test-IsLink $target)) { throw 'target is not a junction' }

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

  # --- file mode (-File, symbolic link — needs Developer Mode or admin) ---
  $fileSource = Join-Path $root 'CLAUDE with spaces.md'
  Set-Content -LiteralPath $fileSource -Value 'rules'

  $realFile = Join-Path $root 'real-AGENTS.md'
  Set-Content -LiteralPath $realFile -Value 'mine'
  $realConflict = Invoke-Installer $fileSource $realFile -File
  if ($realConflict.Success -or $realConflict.Error -notmatch 'not a link') { throw 'real file conflict was not rejected' }
  if ((Get-Content -LiteralPath $realFile -Raw).Trim() -ne 'mine') { throw 'real file was changed' }

  $devMode = (Get-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock' -Name AllowDevelopmentWithoutDevLicense -ErrorAction SilentlyContinue).AllowDevelopmentWithoutDevLicense -eq 1
  $admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  if (-not ($devMode -or $admin)) {
    Write-Output 'SKIP file mode — symbolic links need Developer Mode or an administrator shell on this machine'
  } else {
    # `&` in the path: nothing may reach cmd's parser
    $fileTarget = Join-Path $root 'codex&home\AGENTS.md'
    $fileCreated = Invoke-Installer $fileSource $fileTarget -File
    if (-not $fileCreated.Success) { throw "file link creation failed: $($fileCreated.Error)" }
    if (-not (Test-IsLink $fileTarget)) { throw 'file target is not a symbolic link' }
    if ((Get-Content -LiteralPath $fileTarget -Raw).Trim() -ne 'rules') { throw 'file link does not read the source' }

    $fileRerun = Invoke-Installer $fileSource $fileTarget -File
    if (-not $fileRerun.Success) { throw "file idempotent rerun failed: $($fileRerun.Error)" }

    $fileDry = Join-Path $root 'dry-AGENTS.md'
    $fileDryRun = Invoke-Installer $fileSource $fileDry -File -DryRun
    if (-not $fileDryRun.Success -or (Test-Path -LiteralPath $fileDry)) { throw 'file dry-run changed the target' }

    $otherFile = Join-Path $root 'other.md'
    Set-Content -LiteralPath $otherFile -Value 'other'
    $otherFileLink = Join-Path $root 'other-AGENTS.md'
    $otherMade = Invoke-Installer $otherFile $otherFileLink -File
    if (-not $otherMade.Success) { throw "other file link creation failed: $($otherMade.Error)" }
    $otherFileConflict = Invoke-Installer $fileSource $otherFileLink -File
    if ($otherFileConflict.Success -or $otherFileConflict.Error -notmatch 'existing link') { throw 'other file link conflict was not rejected' }
  }

  $dirAsFile = Invoke-Installer $source (Join-Path $root 'dir-as-file') -File
  if ($dirAsFile.Success -or $dirAsFile.Error -notmatch 'not a file') { throw 'directory source in file mode was not rejected' }
  $missingFile = Invoke-Installer (Join-Path $root 'missing.md') (Join-Path $root 'missing-AGENTS.md') -File
  if ($missingFile.Success -or $missingFile.Error -notmatch 'source missing') { throw 'missing file source was not rejected' }

  # --- setup.ps1 links the same Codex skills as setup.sh ---
  $shSkills = ([regex]::Match((Get-Content -LiteralPath (Join-Path $PSScriptRoot 'setup.sh') -Raw), 'CODEX_SKILLS="([^"]*)"')).Groups[1].Value -split '\s+' | Where-Object { $_ }
  $psMatch = [regex]::Match((Get-Content -LiteralPath (Join-Path $PSScriptRoot 'setup.ps1') -Raw), '\$CodexSkills\s*=\s*@\(([^)]*)\)')
  $psSkills = [regex]::Matches($psMatch.Groups[1].Value, "'([^']+)'") | ForEach-Object { $_.Groups[1].Value }
  if (-not $shSkills -or ((@($shSkills) -join ' ') -cne (@($psSkills) -join ' '))) {
    throw "setup.ps1 Codex skills ($($psSkills -join ',')) differ from setup.sh CODEX_SKILLS ($($shSkills -join ','))"
  }

  Write-Output 'install-codex-skill.ps1 state matrix passed'
} finally {
  Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
