#!/usr/bin/env python3
"""Replaces part of a WAV file with current_time.wav.

Removes the audio from START to END (in seconds) and puts the announcement
from say_time.py in its place, converted to match the file.

Usage: python3 insert_time.py file.wav START END [--time-file file.wav] [--out file.wav] [--volume DB]
"""

import argparse
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Fade the audio either side of the cut to avoid clicks.
FADE_MS = 5


def read_wav(path):
    if not path.is_file():
        sys.exit(f"Missing {path}.")
    try:
        with wave.open(str(path), "rb") as wav:
            return wav.getparams(), wav.readframes(wav.getnframes())
    except (wave.Error, EOFError) as error:
        sys.exit(f"{path} is not an uncompressed WAV file: {error}")


def decode(frames, params):
    """Returns the samples of each channel, from -1 to 1."""
    width = params.sampwidth
    scale = 1 << (8 * width - 1)
    samples = []
    for i in range(0, len(frames), width):
        if width == 1:
            value = frames[i] - 128  # 8-bit audio is unsigned.
        else:
            value = int.from_bytes(frames[i:i + width], "little", signed=True)
        samples.append(value / scale)
    return [samples[channel::params.nchannels] for channel in range(params.nchannels)]


def encode(channels, width):
    scale = 1 << (8 * width - 1)
    frames = bytearray()
    for frame in zip(*channels):
        for sample in frame:
            value = max(-scale, min(scale - 1, round(sample * scale)))
            if width == 1:
                frames.append(value + 128)
            else:
                frames += value.to_bytes(width, "little", signed=True)
    return bytes(frames)


def convert(channels, rate, target):
    """Converts channels sampled at rate to the channel count and rate of target."""
    if len(channels) == 1:
        channels = channels * target.nchannels
    elif target.nchannels == 1:
        channels = [[sum(frame) / len(frame) for frame in zip(*channels)]]
    elif len(channels) != target.nchannels:
        raise ValueError(f"Can't convert {len(channels)} channels to {target.nchannels}.")
    if rate == target.framerate:
        return channels

    # Resample by drawing a straight line between neighbouring samples.
    step = rate / target.framerate
    count = round(len(channels[0]) / step)
    resampled = []
    for samples in channels:
        last = len(samples) - 1
        out = []
        for i in range(count):
            position = i * step
            j = min(int(position), last)
            k = min(j + 1, last)
            out.append(samples[j] + (samples[k] - samples[j]) * (position - j))
        resampled.append(out)
    return resampled


def fade(frames, params, fade_in):
    channels = decode(frames, params)
    count = len(channels[0])
    for samples in channels:
        for i in range(count):
            samples[i] *= (i + 1) / count if fade_in else (count - i) / count
    return encode(channels, params.sampwidth)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file", type=Path, help="WAV file to insert the time into")
    parser.add_argument("start", type=float, help="start of the audio to replace, in seconds")
    parser.add_argument("end", type=float, help="end of the audio to replace, in seconds")
    parser.add_argument("--time-file", type=Path, default=ROOT / "current_time.wav",
                        help="announcement to insert (default: current_time.wav)")
    parser.add_argument("--out", type=Path,
                        help="file to write (default: the file's name plus _with_time)")
    parser.add_argument("--volume", type=float, default=0,
                        help="change the announcement's volume, in dB (default: 0)")
    args = parser.parse_args()

    if not args.time_file.is_file():
        sys.exit(f"Missing {args.time_file}. Run say_time.py first.")
    params, frames = read_wav(args.file)
    time_params, time_frames = read_wav(args.time_file)

    duration = params.nframes / params.framerate
    if not 0 <= args.start < args.end <= duration:
        sys.exit(f"Start and end must be between 0 and {duration:.2f} seconds, with start first.")

    frame_size = params.nchannels * params.sampwidth
    start = round(args.start * params.framerate) * frame_size
    end = round(args.end * params.framerate) * frame_size
    fade_size = params.framerate * FADE_MS // 1000 * frame_size

    before = frames[:start]
    fade_start = max(0, len(before) - fade_size)
    before = before[:fade_start] + fade(before[fade_start:], params, fade_in=False)
    after = frames[end:]
    after = fade(after[:fade_size], params, fade_in=True) + after[fade_size:]

    announcement = convert(decode(time_frames, time_params), time_params.framerate, params)
    gain = 10 ** (args.volume / 20)
    announcement = [[sample * gain for sample in samples] for samples in announcement]
    out = args.out or args.file.with_name(f"{args.file.stem}_with_time.wav")
    with wave.open(str(out), "wb") as wav:
        wav.setnchannels(params.nchannels)
        wav.setsampwidth(params.sampwidth)
        wav.setframerate(params.framerate)
        wav.writeframes(before + encode(announcement, params.sampwidth) + after)

    print(f"Replaced {args.start:g}s to {args.end:g}s of {args.file.name} with {args.time_file.name}")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
