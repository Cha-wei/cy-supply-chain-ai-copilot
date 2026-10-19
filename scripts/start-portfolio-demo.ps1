#requires -Version 5.1
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$url = 'http://127.0.0.1:4190/'

try {
    $python = Get-Command python -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $python) {
        throw 'Python was not found on PATH. Install Python >=3.11, reopen PowerShell, and verify: python --version'
    }
    # Running a probe also detects Windows Store aliases and broken installations.
    $probe = & $python.Source -c 'import sys; print(sys.version.split()[0]); sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python >=3.11 is required (pyproject.toml). The Python probe failed: $probe"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot 'portfolio-ui/dist/index.html') -PathType Leaf)) {
        throw "React build missing: portfolio-ui/dist/index.html. First preparation: in '$repoRoot/portfolio-ui', run npm ci and npm run build. See portfolio-ui/README.md. Daily launch never builds or installs dependencies."
    }

    # This is only a bind preflight. The server's actual bind remains authoritative.
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 4190)
    $listener.Server.ExclusiveAddressUse = $true
    try {
        $listener.Start()
    }
    catch {
        throw "Cannot bind 127.0.0.1:4190 (occupied or unavailable). Stop the existing Demo with Ctrl+C, or inspect: Get-NetTCPConnection -LocalPort 4190. Detail: $($_.Exception.Message)"
    }
    finally {
        $listener.Stop()
    }
}
catch {
    [Console]::Error.WriteLine("Demo preflight failed: $($_.Exception.Message)")
    exit 1
}

Write-Host "Python $probe. Starting SIMULATED Portfolio POC at $url"
Write-Host 'Wait for the server confirmation: SIMULATED local runtime. Then open the URL manually.'
Write-Host 'Foreground session; Ctrl+C stops the Demo. Hosted AI disabled; state is memory-only.'
$serverExitCode = 1
Push-Location -LiteralPath $repoRoot
try {
    # Direct foreground invocation: no Node, background job, or detached service.
    # Keep native stderr visible and retain the native exit status on both PS 5.1 and 7.
    $ErrorActionPreference = 'Continue'
    & $python.Source -m snapshot_loader.demo_server --port 4190
    $serverExitCode = $LASTEXITCODE
    if ($serverExitCode -ne 0) {
        [Console]::Error.WriteLine("Demo server exited with code $serverExitCode. See the Python diagnostic above; check build integrity and port availability. See portfolio-ui/README.md.")
    }
}
finally {
    Pop-Location
}
exit $serverExitCode
