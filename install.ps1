# Installs the animation pack into OpenCode's global plugin directory.
$src = $PSScriptRoot
$dst = Join-Path $env:USERPROFILE ".config\opencode\plugins\animation-pack"

New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item (Join-Path $src "index.ts") $dst -Force
Copy-Item (Join-Path $src "tui.tsx") $dst -Force

Write-Host "Installed to $dst"
Write-Host "OpenCode reloads plugins automatically; use /reload if the animations do not show up."
