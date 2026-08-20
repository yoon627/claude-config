[CmdletBinding()]
param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Arguments
)

$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $PSScriptRoot 'jira_worklog.py'
if (Get-Command uv -ErrorAction SilentlyContinue) {
  $uvCacheDir = if ($env:UV_CACHE_DIR) { $env:UV_CACHE_DIR } else { Join-Path $HOME '.claude\.tmp\jira-worklog-uv-cache' }
  & uv --cache-dir $uvCacheDir run --no-project python $scriptPath @Arguments
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  & python $scriptPath @Arguments
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
  & python3 $scriptPath @Arguments
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
  & py -3 $scriptPath @Arguments
} else {
  throw 'jira-worklog 실행기 없음: uv, python, python3, py 중 하나가 필요합니다.'
}

if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}
