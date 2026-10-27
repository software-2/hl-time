# hl-time

Makes the Half-Life HEV suit tell you the time: *"The time is now ten oh five p.m."*

You need Windows and your own copy of Half-Life. The game's sounds are not included.

## Usage

1. Run `windows\extract_hl_sounds.bat` to copy the sounds from your Half-Life install into `hl1-sounds\`.
   If Half-Life isn't in the default Steam folder, pass its location:

   ```
   windows\extract_hl_sounds.bat "D:\SteamLibrary\steamapps\common\Half-Life"
   ```

2. Run `windows\say_time.bat`. It writes the current time to `current_time.wav`.
