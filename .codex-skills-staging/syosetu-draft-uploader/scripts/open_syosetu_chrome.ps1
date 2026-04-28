param(
  [string]$Url = "https://syosetu.com/usernovelmanage/top/ncode/3144848/?filter=draft",
  [int]$Port = 9223,
  [string]$ProfileDir = "$env:LOCALAPPDATA\Codex\syosetu-draft-profile",
  [string]$ChromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
)

if (-not (Test-Path -LiteralPath $ChromePath)) {
  throw "Chrome not found at $ChromePath"
}

New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null

$args = @(
  "--remote-debugging-port=$Port",
  "--user-data-dir=$ProfileDir",
  "--profile-directory=Default",
  "--new-window",
  $Url
)

Start-Process -FilePath $ChromePath -ArgumentList $args
Write-Output "Opened Chrome on remote debugging port $Port with profile $ProfileDir"
