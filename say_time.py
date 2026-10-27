#!/usr/bin/env python3
"""Writes a WAV of the HEV suit saying "The time is now ...".

Uses the sounds from extract_hl_sounds.py.

Usage: python3 say_time.py [--time "10:47 PM"] [--out file.wav] [--gap-ms 100]
"""

import argparse
import sys
import wave
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOUND_DIR = ROOT / "hl1-sounds"

ONES = [None, "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
        "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
        "eighteen", "nineteen"]
# "fourty" is the game's spelling.
TENS = [None, None, "twenty", "thirty", "fourty", "fifty"]


def number_words(number):
    if number < 20:
        return [ONES[number]]
    words = [TENS[number // 10]]
    if number % 10:
        words.append(ONES[number % 10])
    return words


def time_words(time):
    words = ["bell", "time_is_now"] + number_words(time.hour % 12 or 12)
    if time.minute:
        if time.minute < 10:
            words.append("oh")
        words += number_words(time.minute)
    words.append("am" if time.hour < 12 else "pm")
    return words


def parse_time(text):
    for time_format in ("%I:%M %p", "%H:%M"):
        try:
            return datetime.strptime(text.strip().upper(), time_format)
        except ValueError:
            pass
    raise argparse.ArgumentTypeError(f"expected a time like 10:47 PM or 22:47, not {text!r}")


def format_time(time):
    return f"{time:%I:%M %p}".lstrip("0")


def announcement(time, gap_ms=100):
    """Returns the words, WAV format and audio of the HEV suit saying the time."""
    words = time_words(time)
    clips = []
    for word in words:
        path = SOUND_DIR / f"{word}.wav"
        if not path.is_file():
            sys.exit(f"Missing {path}. Run extract_hl_sounds.py first.")
        with wave.open(str(path), "rb") as wav:
            clips.append((wav.getparams(), wav.readframes(wav.getnframes())))

    params = clips[0][0]
    if any(clip_params[:3] != params[:3] for clip_params, _ in clips):
        sys.exit(f"The clips in {SOUND_DIR} do not all share the same audio format.")

    # 8-bit silence is 128, not 0.
    silence = b"\x80" if params.sampwidth == 1 else b"\x00"
    gap = silence * (params.framerate * gap_ms // 1000 * params.nchannels * params.sampwidth)
    return words, params, gap.join(frames for _, frames in clips)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--time", type=parse_time, default=datetime.now(),
                        help='time to say, like "10:47 PM" or 22:47 (default: now)')
    parser.add_argument("--out", type=Path, default=ROOT / "current_time.wav",
                        help="file to write (default: current_time.wav)")
    parser.add_argument("--gap-ms", type=int, default=100,
                        help="silence between words in milliseconds (default: 100)")
    args = parser.parse_args()

    words, params, frames = announcement(args.time, args.gap_ms)
    with wave.open(str(args.out), "wb") as wav:
        wav.setnchannels(params.nchannels)
        wav.setsampwidth(params.sampwidth)
        wav.setframerate(params.framerate)
        wav.writeframes(frames)

    print(f"{format_time(args.time)}: {' '.join(words)}")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
