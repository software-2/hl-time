# hl-time

Makes the Half-Life HEV suit tell you the time: *"The time is now ten oh five p.m."*

You need Python 3 and your own copy of Half-Life. The game's sounds are not included.
Works on Windows and Linux. On Windows, use `python` or `py` instead of `python3`.

## Usage

1. Copy the sounds from your Half-Life install into `hl1-sounds/`:

   ```
   python3 extract_hl_sounds.py
   ```

   If Half-Life isn't in a default Steam folder, pass its location:

   ```
   python3 extract_hl_sounds.py "D:/SteamLibrary/steamapps/common/Half-Life"
   ```

2. Write the current time to `current_time.wav`:

   ```
   python3 say_time.py
   ```

3. Optionally, put the time into another WAV file. This replaces the audio from 7.8s to 12.69s of
   `insert/goodevening.wav` with `current_time.wav`, turned down 2.5 dB to match, and writes
   `insert/goodevening_with_time.wav`:

   ```
   python3 insert_time.py insert/goodevening.wav 7.8 12.69 --volume -2.5
   ```
