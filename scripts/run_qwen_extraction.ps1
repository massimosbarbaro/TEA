param(
    [Parameter(Mandatory = $true)][string]$Texts,
    [Parameter(Mandatory = $true)][string]$Output,
    [string]$Model = 'qwen3.5:9b-q4_K_M'
)

$ErrorActionPreference = 'Stop'
$template = Get-Content -Raw -LiteralPath 'extraction_prompt.txt'
$records = Get-Content -Raw -LiteralPath $Texts | ConvertFrom-Json -AsHashtable

$raw = [ordered]@{}
if (Test-Path -LiteralPath $Output) {
    $prior = Get-Content -Raw -LiteralPath $Output | ConvertFrom-Json -AsHashtable
    foreach ($key in $prior.Keys) { $raw[$key] = $prior[$key] }
}

$index = 0
foreach ($rec in $records.Keys) {
    $index++
    if ($raw.Contains($rec)) {
        Write-Output "[$index/$($records.Count)] record $rec already complete"
        continue
    }

    $text = $records[$rec]['text']
    $prompt = $template.Replace('<<<TEXT>>>', $text)
    $body = @{
        model = $Model
        prompt = $prompt
        stream = $false
        think = $false
        keep_alive = '30m'
        options = @{ temperature = 0; seed = 42; num_ctx = 8192 }
    } | ConvertTo-Json -Depth 6

    $response = Invoke-RestMethod `
        -Uri 'http://localhost:11434/api/generate' `
        -Method Post `
        -ContentType 'application/json' `
        -Body $body `
        -TimeoutSec 600

    if (-not $response.done -or [string]::IsNullOrWhiteSpace($response.response)) {
        throw "Incomplete Qwen response for record $rec"
    }
    $raw[$rec] = $response.response
    $raw | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $Output -Encoding utf8
    Write-Output "[$index/$($records.Count)] record ${rec}: $($response.eval_count) output tokens"
}

Write-Output "written: $Output ($($raw.Count) records)"
