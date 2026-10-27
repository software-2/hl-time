# Functions for reading and writing WAV files.

# Returns a WAV file's format and audio data.
function Read-Wav([string]$Path) {
    $Path = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Path)
    $bytes = [IO.File]::ReadAllBytes($Path)
    $ascii = [Text.Encoding]::ASCII
    if ($bytes.Length -lt 12 -or $ascii.GetString($bytes, 0, 4) -ne 'RIFF' -or $ascii.GetString($bytes, 8, 4) -ne 'WAVE') {
        throw "$Path is not a WAV file."
    }

    $format = $null
    $pos = 12
    while ($pos + 8 -le $bytes.Length) {
        $id = $ascii.GetString($bytes, $pos, 4)
        $size = [BitConverter]::ToInt32($bytes, $pos + 4)
        $body = $pos + 8
        if ($id -eq 'fmt ') {
            $format = [pscustomobject]@{
                AudioFormat   = [BitConverter]::ToUInt16($bytes, $body)
                Channels      = [BitConverter]::ToUInt16($bytes, $body + 2)
                SampleRate    = [BitConverter]::ToUInt32($bytes, $body + 4)
                BitsPerSample = [BitConverter]::ToUInt16($bytes, $body + 14)
            }
        } elseif ($id -eq 'data') {
            if (-not $format) { throw "$Path has no format chunk before its audio data." }
            $size = [Math]::Min($size, $bytes.Length - $body)
            $data = New-Object byte[] $size
            [Array]::Copy($bytes, $body, $data, 0, $size)
            return [pscustomobject]@{ Format = $format; Data = $data }
        }
        $pos = $body + $size + ($size % 2)
    }
    throw "$Path has no audio data."
}

# Writes audio data to a WAV file.
function Write-Wav([string]$Path, $Format, [byte[]]$Data) {
    $Path = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Path)
    $blockAlign = $Format.Channels * $Format.BitsPerSample / 8
    $ascii = [Text.Encoding]::ASCII
    $out = New-Object IO.BinaryWriter([IO.File]::Create($Path))
    try {
        $out.Write($ascii.GetBytes('RIFF'))
        $out.Write([uint32](36 + $Data.Length + ($Data.Length % 2)))
        $out.Write($ascii.GetBytes('WAVEfmt '))
        $out.Write([uint32]16)
        $out.Write([uint16]1)
        $out.Write([uint16]$Format.Channels)
        $out.Write([uint32]$Format.SampleRate)
        $out.Write([uint32]($Format.SampleRate * $blockAlign))
        $out.Write([uint16]$blockAlign)
        $out.Write([uint16]$Format.BitsPerSample)
        $out.Write($ascii.GetBytes('data'))
        $out.Write([uint32]$Data.Length)
        $out.Write($Data)
        if ($Data.Length % 2) { $out.Write([byte]0) }
    } finally {
        $out.Dispose()
    }
}
