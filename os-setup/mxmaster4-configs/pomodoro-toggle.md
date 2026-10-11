# Pomodoro toggle

One MX Master 4 mouse button that controls the pomodoro timer of the **TaskNotes** plugin in Obsidian.

## Use case

Start, pause and resume a focus session from the mouse, without switching to Obsidian or
opening the command palette. A macOS notification confirms what happened.

## What it does

Each press checks the current pomodoro state through the TaskNotes HTTP API:

- running -> pause
- paused -> resume
- idle -> start a new 100 min work session (TaskNotes caps a session at 120)

## Files

Both live in `~/bin/pomodoro/`.

- [`toggle.applescript`](https://github.com/SheikhFahan/notes/blob/main/os-setup/mxmaster4-configs/toggle.applescript) — runs `toggle.py` and shows the result as a notification
- [`toggle.py`](https://github.com/SheikhFahan/notes/blob/main/os-setup/mxmaster4-configs/toggle.py) — talks to the TaskNotes API; reads the port and auth token from
  `~/Documents/journal/.obsidian/plugins/tasknotes/data.json`

## Requirements

- Obsidian open with the TaskNotes plugin installed
- Settings > TaskNotes > Integrations > HTTP API enabled

## Automation (Logi Options+)

The button is a Logi Options+ action on the MX Master 4 Actions Ring:

- Action: **Run AppleScript** (Execute AppleScript), display name `Pomodoro`
- Script file: `~/bin/pomodoro/toggle.scpt`
- Subroutine: `toggle`
- Placed on slot 1 of the Actions Ring (Default General Profile)

The action needs a compiled `.scpt`, so recompile after editing `toggle.applescript`:

```
osacompile -o ~/bin/pomodoro/toggle.scpt ~/bin/pomodoro/toggle.applescript
```
