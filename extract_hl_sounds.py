#!/usr/bin/env python3
"""Copies the HEV suit sounds from your Half-Life install into hl1-sounds/.

Usage: python3 extract_hl_sounds.py [path/to/Half-Life]
With no path, the usual Steam folders are searched.
"""

import os
import shutil
import sys
import wave
from pathlib import Path

DEST = Path(__file__).resolve().parent / "hl1-sounds"

FILES = """
    bell time_is_now am pm hours minutes _comma _period
    one two three four five six seven eight nine ten
    eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen
    twenty twentyfive thirty fourty fifty sixty seventy eighty ninety onehundred
""".split()

STEAM_DIRS = [
    Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Steam",
    Path.home() / ".steam/steam",
    Path.home() / ".local/share/Steam",
    Path.home() / ".var/app/com.valvesoftware.Steam/.local/share/Steam",
]

# There is no "oh" sound, so cut one from the start of "overload" in
# "Warning: power movement system overload" (3.45s to 3.73s).
OH_SOURCE = "powermove_overload"
OH_START, OH_END = 38000, 41140
FADE_MS = 10
PAD_MS = 80


def find_sounds(game_dir):
    """Returns the game's HEV suit sounds by lowercase name, or None."""
    if game_dir:
        candidates = [Path(game_dir)]
    else:
        candidates = [steam / "steamapps/common/Half-Life" for steam in STEAM_DIRS]
    for game in candidates:
        fvox = game / "valve/sound/fvox"
        if fvox.is_dir():
            sounds = {path.stem.lower(): path for path in fvox.glob("*.wav")}
            if "time_is_now" in sounds:
                return sounds
    return None


def cut_oh(source, dest):
    with wave.open(str(source), "rb") as wav:
        params = wav.getparams()
        if params.nchannels != 1 or params.sampwidth != 1 or wav.getnframes() < OH_END:
            raise ValueError(f"{source} is not the expected recording.")
        wav.setpos(OH_START)
        frames = bytearray(wav.readframes(OH_END - OH_START))

    # Fade both ends to avoid clicks, then add silence at the end.
    # 8-bit silence is 128, not 0.
    fade = min(params.framerate * FADE_MS // 1000, len(frames) // 2)
    for i, sample in enumerate(frames):
        level = min(1.0, min(i, len(frames) - 1 - i) / fade)
        frames[i] = round((sample - 128) * level) + 128
    frames += b"\x80" * (params.framerate * PAD_MS // 1000)

    with wave.open(str(dest), "wb") as wav:
        wav.setnchannels(params.nchannels)
        wav.setsampwidth(params.sampwidth)
        wav.setframerate(params.framerate)
        wav.writeframes(frames)


def main():
    game_dir = sys.argv[1] if len(sys.argv) > 1 else None
    sounds = find_sounds(game_dir)
    if sounds is None:
        where = game_dir or "the usual Steam folders"
        sys.exit(
            f"Could not find the Half-Life HEV suit sounds in {where}.\n"
            "Pass the folder Half-Life is installed in, for example:\n"
            f'  python3 {Path(__file__).name} "D:/SteamLibrary/steamapps/common/Half-Life"'
        )

    DEST.mkdir(exist_ok=True)
    saved = 0
    failed = 0
    for name in FILES:
        if name in sounds:
            shutil.copyfile(sounds[name], DEST / f"{name}.wav")
            saved += 1
        else:
            print(f"Missing: {name}.wav")
            failed += 1

    if OH_SOURCE in sounds:
        try:
            cut_oh(sounds[OH_SOURCE], DEST / "oh.wav")
            saved += 1
        except (ValueError, wave.Error) as error:
            print(f"Failed to make oh.wav: {error}")
            failed += 1
    else:
        print(f"Missing: {OH_SOURCE}.wav")
        failed += 1

    print(f"Saved {saved} files to {DEST}")
    if failed:
        sys.exit(f"{failed} files could not be saved.")


if __name__ == "__main__":
    main()
