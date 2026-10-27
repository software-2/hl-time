# Makes oh.wav from the "o" at the start of "overload" in powermove_overload.wav.
# Run by extract_hl_sounds.bat.
param(
    [Parameter(Mandatory)][string]$Source,
    [Parameter(Mandatory)][string]$OutFile,
    [int]$StartSample = 38000,
    [int]$EndSample = 41140,
    [int]$FadeMs = 10,
    [int]$PadMs = 80,
    [double]$Gain = 1.0
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'wav_tools.ps1')

$wav = Read-Wav $Source
$format = $wav.Format
if ($format.AudioFormat -ne 1 -or $format.Channels -ne 1 -or $format.BitsPerSample -ne 8) {
    throw "$Source is not 8-bit mono PCM."
}
if ($StartSample -lt 0 -or $StartSample -ge $EndSample -or $EndSample -gt $wav.Data.Length) {
    throw "Samples $StartSample to $EndSample are outside $Source."
}

$length = $EndSample - $StartSample
$fade = [Math]::Min([int]($format.SampleRate * $FadeMs / 1000), [int]($length / 2))
$pad = [int]($format.SampleRate * $PadMs / 1000)

# Fade both ends to avoid clicks, then add silence at the end.
$data = New-Object byte[] ($length + $pad)
for ($i = 0; $i -lt $length; $i++) {
    $level = $Gain
    if ($fade -gt 0) { $level *= [Math]::Min(1.0, [Math]::Min($i, $length - 1 - $i) / $fade) }
    $sample = [Math]::Round(($wav.Data[$StartSample + $i] - 128) * $level) + 128
    $data[$i] = [byte][Math]::Max(0, [Math]::Min(255, $sample))
}
for ($i = $length; $i -lt $data.Length; $i++) { $data[$i] = 128 }

Write-Wav $OutFile $format $data
Write-Host "Wrote $OutFile"
