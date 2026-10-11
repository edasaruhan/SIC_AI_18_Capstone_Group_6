param(
  [Parameter(Mandatory = $true)][string]$InputPath,
  [Parameter(Mandatory = $true)][string]$OutputPdf
)
# Updates the table of contents and page fields with the installed Word, saves the .docx, and exports a PDF.
# Adapted from Documents/Academic_Archive/IC/render_docx_with_word.ps1.
# Never quits a Word instance the user already had open.
$ErrorActionPreference = "Stop"
$resolvedInput = (Resolve-Path -LiteralPath $InputPath).Path
$resolvedOutput = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputPdf)  # relative to the PowerShell location
New-Item -ItemType Directory -Path (Split-Path -Parent $resolvedOutput) -Force | Out-Null

$wasRunning = [bool](Get-Process WINWORD -ErrorAction SilentlyContinue)
$word = New-Object -ComObject Word.Application
$document = $null
try {
  $word.Visible = $false
  $word.DisplayAlerts = 0
  # Open(FileName, ConfirmConversions=false, ReadOnly=false)
  $document = $word.Documents.Open($resolvedInput, $false, $false)
  foreach ($toc in $document.TablesOfContents) { $toc.Update() | Out-Null }
  $document.Fields.Update() | Out-Null
  $document.Save()
  # 17 = PDF; print quality; whole document; include the title/author properties;
  # 1 = bookmarks from headings (a clickable outline); tagged PDF for screen readers
  $document.ExportAsFixedFormat($resolvedOutput, 17, $false, 0, 0, 1, 1, 0, $true, $true, 1, $true, $true, $false)
  "Pages: " + $document.ComputeStatistics(2)
  "PDF: " + $resolvedOutput
}
finally {
  if ($document -ne $null) { $document.Close([ref]$false) | Out-Null }
  if (-not $wasRunning) { $word.Quit() | Out-Null }
  [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}
