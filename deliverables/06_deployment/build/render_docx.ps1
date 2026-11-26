$ErrorActionPreference = 'Stop'
$report = Join-Path (Split-Path -Parent $PSScriptRoot) 'NudgeWell_Group6_HW6_Deployment.docx'
$pdf = [IO.Path]::ChangeExtension($report, '.pdf')
$wordWasOpen = [bool](Get-Process WINWORD -ErrorAction SilentlyContinue)
$word = New-Object -ComObject Word.Application
$document = $null
try {
    if (-not $wordWasOpen) { $word.Visible = $false }
    $document = $word.Documents.Open($report, $false, $true, $false)
    # Export at print quality with document properties, bookmarks, and accessibility tags.
    $document.ExportAsFixedFormat($pdf, 17, $false, 0, 0, 1, 1, 0, $true, $true, 1, $true, $true, $false)
    $pdf
} finally {
    if ($null -ne $document) { $document.Close([ref]$false) }
    if (-not $wordWasOpen) { $word.Quit() }
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}
