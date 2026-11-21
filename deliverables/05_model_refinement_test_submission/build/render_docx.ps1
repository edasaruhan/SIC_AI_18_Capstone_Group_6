$ErrorActionPreference = 'Stop'
$report = Join-Path (Split-Path -Parent $PSScriptRoot) 'NudgeWell_HW5_Model_Refinement_and_Test_Submission.docx'
$pdf = [IO.Path]::ChangeExtension($report, '.pdf')
$wordWasOpen = [bool](Get-Process WINWORD -ErrorAction SilentlyContinue)
$word = New-Object -ComObject Word.Application
$document = $null
try {
    if (-not $wordWasOpen) { $word.Visible = $false }
    $document = $word.Documents.Open($report, $false, $true, $false)
    # Word PDF export at print quality with document properties, bookmarks, and tags.
    $document.ExportAsFixedFormat($pdf, 17, $false, 0, 0, 1, 1, 0, $true, $true, 1, $true, $true, $false)
    $pdf
} finally {
    if ($null -ne $document) { $document.Close([ref]$false) }
    if (-not $wordWasOpen) { $word.Quit() }
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}
