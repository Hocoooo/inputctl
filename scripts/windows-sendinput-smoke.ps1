[CmdletBinding()]
param(
    [string]$PythonExe = "python",
    [string]$Text = "INPUTCTL_SMOKE_OK",
    [string]$InitialContent = "BASELINE",
    [int]$KeyDelayMs = 40,
    [int]$PressDelayMs = 20,
    [int]$LaunchDelayMs = 700,
    [int]$FocusDelayMs = 300,
    [switch]$KeepFile,
    [string]$FilePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($env:OS -ne "Windows_NT") {
    throw "This smoke test is Windows-only."
}

function Invoke-Inputctl {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $commandLine = @("-m", "inputctl", "--key-delay-ms", "$KeyDelayMs", "--press-delay-ms", "$PressDelayMs") + $Arguments
    & $PythonExe @commandLine
    if ($LASTEXITCODE -ne 0) {
        throw "inputctl command failed with exit code ${LASTEXITCODE}: $PythonExe $($commandLine -join ' ')"
    }
}

function Close-Notepad {
    param(
        [Parameter(Mandatory = $true)]
        [System.Diagnostics.Process]$Process,
        [Parameter(Mandatory = $true)]
        [__ComObject]$Shell
    )

    if ($Process.HasExited) {
        return
    }

    $null = $Shell.AppActivate($Process.Id)
    Start-Sleep -Milliseconds 200
    $Process.CloseMainWindow() | Out-Null
    Start-Sleep -Milliseconds 500
    if (-not $Process.HasExited) {
        Stop-Process -Id $Process.Id -Force
    }
}

if (-not $FilePath) {
    $FilePath = Join-Path $env:TEMP "inputctl-smoke.txt"
}

$shell = $null
$process = $null

try {
    Set-Content -LiteralPath $FilePath -Value $InitialContent -Encoding ascii

    $process = Start-Process notepad.exe -ArgumentList $FilePath -PassThru
    Start-Sleep -Milliseconds $LaunchDelayMs

    $shell = New-Object -ComObject WScript.Shell
    if (-not $shell.AppActivate($process.Id)) {
        throw "Failed to activate Notepad window for PID $($process.Id)."
    }

    Start-Sleep -Milliseconds $FocusDelayMs

    Invoke-Inputctl -Arguments @("keyboard", "press", "end")
    Start-Sleep -Milliseconds 150
    Invoke-Inputctl -Arguments @("keyboard", "press", "enter")
    Start-Sleep -Milliseconds 150
    Invoke-Inputctl -Arguments @("keyboard", "type", $Text)
    Start-Sleep -Milliseconds 150
    Invoke-Inputctl -Arguments @("keyboard", "combo", "control", "s")
    Start-Sleep -Milliseconds 600

    $content = Get-Content -LiteralPath $FilePath -Raw
    if ($content -notmatch [regex]::Escape($Text)) {
        throw "Smoke test failed: expected file to contain '$Text'. Actual content:`n$content"
    }

    Write-Host "PASS: Notepad received and saved synthetic input."
    Write-Host "File: $FilePath"
    Write-Host "Content:"
    Write-Host $content
}
finally {
    if ($process) {
        if (-not $shell) {
            $shell = New-Object -ComObject WScript.Shell
        }
        Close-Notepad -Process $process -Shell $shell
    }

    if (-not $KeepFile -and (Test-Path -LiteralPath $FilePath)) {
        Remove-Item -LiteralPath $FilePath -Force
    }
}
