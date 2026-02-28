[CmdletBinding()]
param(
    [int]$Samples = 5,
    [string[]]$Models = @(
        "ministral-3:8b",
        "qwen3:8b",
        "llama3.1:8b",
        "gemma3:12b"
    ),
    [switch]$VerboseEval
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $repoRoot ".env"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot "reports\schema_eval_$timestamp"
New-Item -ItemType Directory -Path $outDir -Force | Out-Null

$summaryPath = Join-Path $outDir "summary.tsv"
"model`texit_code`trecommendation`tschema_validity`tspeaker_diversity`tmeta_leak_rate`tavg_latency_s`tjson_report`traw_log" | Set-Content -Path $summaryPath -Encoding UTF8

$previousModel = $env:OLLAMA_MODEL
$originalEnvRaw = ""
if (Test-Path $envFile) {
    $originalEnvRaw = Get-Content -Path $envFile -Raw
}

try {
    Set-Location $repoRoot

    foreach ($model in $Models) {
        $safeModel = ($model -replace "[^A-Za-z0-9._-]", "_")
        $jsonPath = Join-Path $outDir "$safeModel.json"
        $logPath = Join-Path $outDir "$safeModel.log"

        Write-Host ""
        Write-Host "=== Running schema eval for model: $model (samples=$Samples) ==="

        # schema_prose_eval imports providers that call load_dotenv(..., override=True).
        # To ensure per-model runs are real, we update OLLAMA_MODEL in .env before each run.
        $updatedEnv = $originalEnvRaw
        if ($updatedEnv -match "(?m)^OLLAMA_MODEL=") {
            $updatedEnv = [regex]::Replace($updatedEnv, "(?m)^OLLAMA_MODEL=.*$", "OLLAMA_MODEL=$model")
        }
        else {
            if ($updatedEnv.Length -gt 0 -and -not $updatedEnv.EndsWith("`n")) {
                $updatedEnv += "`r`n"
            }
            $updatedEnv += "OLLAMA_MODEL=$model`r`n"
        }
        Set-Content -Path $envFile -Value $updatedEnv -Encoding UTF8

        $env:OLLAMA_MODEL = $model

        $args = @(
            "tests/schema_prose_eval.py",
            "--samples", $Samples.ToString(),
            "--output", $jsonPath
        )
        if ($VerboseEval) {
            $args += "--verbose"
        }

        & python @args 2>&1 | Tee-Object -FilePath $logPath
        $exitCode = $LASTEXITCODE

        $recommendation = "ERROR"
        $schemaValidity = ""
        $speakerDiversity = ""
        $metaLeakRate = ""
        $avgLatency = ""

        if (Test-Path $jsonPath) {
            try {
                $report = Get-Content -Path $jsonPath -Raw | ConvertFrom-Json
                $recommendation = [string]$report.recommendation
                $schemaValidity = [string]$report.metrics.schema_validity
                $speakerDiversity = [string]$report.metrics.speaker_diversity
                $metaLeakRate = [string]$report.metrics.meta_leak_rate
                $avgLatency = [string]$report.metrics.avg_latency_s
            }
            catch {
                $recommendation = "REPORT_PARSE_ERROR"
            }
        }

        "$model`t$exitCode`t$recommendation`t$schemaValidity`t$speakerDiversity`t$metaLeakRate`t$avgLatency`t$jsonPath`t$logPath" | Add-Content -Path $summaryPath -Encoding UTF8
    }
}
finally {
    if (Test-Path $envFile) {
        Set-Content -Path $envFile -Value $originalEnvRaw -Encoding UTF8
    }

    if ($null -ne $previousModel) {
        $env:OLLAMA_MODEL = $previousModel
    }
    else {
        Remove-Item Env:\OLLAMA_MODEL -ErrorAction SilentlyContinue
    }
}

Write-Host ""
Write-Host "Model eval matrix complete."
Write-Host "Summary: $summaryPath"
Write-Host "Reports: $outDir"
