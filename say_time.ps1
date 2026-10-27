# Writes a WAV of the HEV suit saying "The time is now ...".
# Uses the sounds from extract_hl_sounds.bat.
#
# Usage: .\say_time.ps1 [-Time "10:47 PM"] [-OutFile file.wav] [-GapMs 100]
param(
    [datetime]$Time = (Get-Date),
    [string]$OutFile = (Join-Path $PSScriptRoot 'current_time.wav'),
    [int]$GapMs = 100
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'wav_tools.ps1')
$soundDir = Join-Path $PSScriptRoot 'hl1-sounds'

$ones = @($null, 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
    'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen')
# "fourty" is the game's spelling.
$tens = @($null, $null, 'twenty', 'thirty', 'fourty', 'fifty')

function Get-NumberWords([int]$Number) {
    if ($Number -lt 20) { return $ones[$Number] }
    $tens[[int][Math]::Floor($Number / 10)]
    if ($Number % 10) { $ones[$Number % 10] }
}

$hour = $Time.Hour % 12
if ($hour -eq 0) { $hour = 12 }

$words = @('bell', 'time_is_now') + @(Get-NumberWords $hour)
if ($Time.Minute -gt 0) {
    if ($Time.Minute -lt 10) { $words += 'oh' }
    $words += @(Get-NumberWords $Time.Minute)
}
if ($Time.Hour -lt 12) { $words += 'am' } else { $words += 'pm' }

$clips = foreach ($word in $words) {
    $path = Join-Path $soundDir "$word.wav"
    if (-not (Test-Path -LiteralPath $path)) { throw "Missing $path. Run extract_hl_sounds.bat first." }
    Read-Wav $path
}

$format = $clips[0].Format
foreach ($clip in $clips) {
    foreach ($field in 'AudioFormat', 'Channels', 'SampleRate', 'BitsPerSample') {
        if ($clip.Format.$field -ne $format.$field) { throw "The clips in $soundDir do not all share the same audio format." }
    }
}
if ($format.AudioFormat -ne 1) { throw "The clips in $soundDir are not uncompressed PCM." }

$blockAlign = $format.Channels * $format.BitsPerSample / 8
$gap = New-Object byte[] ([int]($format.SampleRate * $GapMs / 1000) * $blockAlign)
# 8-bit silence is 128, not 0.
if ($format.BitsPerSample -eq 8) { for ($i = 0; $i -lt $gap.Length; $i++) { $gap[$i] = 128 } }

$audio = New-Object IO.MemoryStream
for ($i = 0; $i -lt $clips.Count; $i++) {
    if ($i -gt 0) { $audio.Write($gap, 0, $gap.Length) }
    $audio.Write($clips[$i].Data, 0, $clips[$i].Data.Length)
}

Write-Wav $OutFile $format $audio.ToArray()

Write-Host ("{0:h:mm tt}: {1}" -f $Time, ($words -join ' '))
Write-Host "Wrote $OutFile"
