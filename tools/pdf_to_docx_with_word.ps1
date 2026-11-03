<#
.SYNOPSIS
Converts PDFs to .docx with Microsoft Word's own PDF import, for comparing with the converter's PDF output.

.DESCRIPTION
A developer tool, not part of the converter: ADR 0008 keeps Word out of conversion.
Windows only, and needs Word installed. Word opens each PDF read-only and
rebuilds it as a document; the result is taken from Word as XML
(Document.WordOpenXML) and packaged as a .docx beside the PDF, or in -OutDir.

Word asks before converting each PDF unless that notice is turned off. In
Word: File > Options > General, or set the DWORD
HKCU\Software\Microsoft\Office\16.0\Word\Options\DisableConvertPdfWarning to 1.

Word runs hidden, so any question it asks stops the script without showing.
After Word was closed abruptly, it asks on its next start whether to open in
safe mode: start Word once by hand and answer No before running this script.

.EXAMPLE
powershell -ExecutionPolicy Bypass -File tools\pdf_to_docx_with_word.ps1 "C:\Reports\plan.pdf"

.EXAMPLE
powershell -ExecutionPolicy Bypass -File tools\pdf_to_docx_with_word.ps1 "C:\Reports" -OutDir "C:\Compare" -Force
#>
param(
    [Parameter(Mandatory = $true)][string]$Path,  # a PDF, or a folder of PDFs (not searched recursively)
    [string]$OutDir,                              # where to write the .docx files; beside each PDF if omitted
    [switch]$Force                                # replace .docx files that already exist
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression

$PackageNamespace = "http://schemas.microsoft.com/office/2006/xmlPackage"

function Write-Docx([string]$FlatXml, [string]$Destination) {
    # Word's XML is a Flat OPC package: every part of the .docx inline, binary parts as base64.
    $document = New-Object System.Xml.XmlDocument
    $document.PreserveWhitespace = $true
    $document.LoadXml($FlatXml)
    $names = New-Object System.Xml.XmlNamespaceManager($document.NameTable)
    $names.AddNamespace("pkg", $PackageNamespace)
    $overrides = New-Object System.Text.StringBuilder
    $stream = [IO.File]::Open($Destination, [IO.FileMode]::Create)
    $zip = New-Object System.IO.Compression.ZipArchive($stream, [IO.Compression.ZipArchiveMode]::Create)
    try {
        foreach ($part in $document.SelectNodes("//pkg:part", $names)) {
            $name = $part.GetAttribute("name", $PackageNamespace).TrimStart("/")
            $contentType = $part.GetAttribute("contentType", $PackageNamespace)
            $xmlData = $part.SelectSingleNode("pkg:xmlData", $names)
            if ($xmlData) {
                $bytes = [Text.Encoding]::UTF8.GetBytes(
                    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + $xmlData.FirstChild.OuterXml)
            } else {
                $bytes = [Convert]::FromBase64String($part.SelectSingleNode("pkg:binaryData", $names).InnerText)
            }
            $entry = $zip.CreateEntry($name).Open()
            $entry.Write($bytes, 0, $bytes.Length)
            $entry.Dispose()
            [void]$overrides.Append("<Override PartName=`"/$name`" ContentType=`"$contentType`"/>")
        }
        $types = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' + $overrides + '</Types>'
        $bytes = [Text.Encoding]::UTF8.GetBytes($types)
        $entry = $zip.CreateEntry("[Content_Types].xml").Open()
        $entry.Write($bytes, 0, $bytes.Length)
        $entry.Dispose()
    } finally {
        $zip.Dispose()
        $stream.Dispose()
    }
}

$item = Get-Item -LiteralPath $Path
$pdfs = if ($item.PSIsContainer) { @(Get-ChildItem -LiteralPath $item.FullName -Filter *.pdf -File) } else { @($item) }
if (-not $pdfs) { Write-Host "No PDFs found in $Path."; exit 1 }
if ($OutDir) { New-Item -ItemType Directory -Force -Path $OutDir | Out-Null }

$options = Get-ItemProperty "HKCU:\Software\Microsoft\Office\16.0\Word\Options" -ErrorAction SilentlyContinue
if (-not $options -or $options.DisableConvertPdfWarning -ne 1) {
    Write-Host "Note: Word's 'convert this PDF' notice is on, so Word may wait for a click on each PDF (see Get-Help on this script)."
}

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0  # wdAlertsNone
$failed = 0
try {
    foreach ($pdf in $pdfs) {
        $folder = if ($OutDir) { $OutDir } else { $pdf.DirectoryName }
        $destination = Join-Path $folder ($pdf.BaseName + ".docx")
        if ((Test-Path -LiteralPath $destination) -and -not $Force) {
            Write-Host "$($pdf.Name): skipped, $destination exists (use -Force to replace)"
            continue
        }
        $timer = [Diagnostics.Stopwatch]::StartNew()
        try {
            # ConfirmConversions off, read-only, not added to Word's recent files.
            $document = $word.Documents.Open($pdf.FullName, $false, $true, $false)
            try {
                $flatXml = $document.WordOpenXML
            } finally {
                $document.Close(0)  # wdDoNotSaveChanges
            }
            Write-Docx $flatXml $destination
            Write-Host ("{0}: ok, {1} ({2}s)" -f $pdf.Name, $destination, [int]$timer.Elapsed.TotalSeconds)
        } catch {
            $failed++
            Write-Host "$($pdf.Name): failed, $($_.Exception.Message)"
        }
    }
} finally {
    $word.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}
exit $(if ($failed) { 1 } else { 0 })
