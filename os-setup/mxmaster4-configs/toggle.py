#!/usr/bin/python3
"""One button for the TaskNotes pomodoro (standalone, needs no other files).

running -> pause, paused -> resume, idle -> start a new 100 min work session.
Needs Obsidian open with Settings > TaskNotes > Integrations > HTTP API enabled.
"""
import json
import sys
import urllib.error
import urllib.request

DATA = "/Users/sheikhfahan/Documents/journal/.obsidian/plugins/tasknotes/data.json"
MINUTES = 100  # TaskNotes caps a session at 120

with open(DATA) as f:
    cfg = json.load(f)
BASE = f"http://127.0.0.1:{cfg['apiPort']}/api/pomodoro"
HDR = {"Content-Type": "application/json"}
if cfg.get("apiAuthToken"):
    HDR["Authorization"] = f"Bearer {cfg['apiAuthToken']}"


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=HDR)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try:
            msg = json.load(e).get("error", "")
        except ValueError:
            msg = ""
        sys.exit(f"TaskNotes API error {e.code}: {msg or e.reason}")
    except urllib.error.URLError as e:
        sys.exit(f"Can't reach TaskNotes API ({e.reason}). Is Obsidian open and "
                 "Settings > TaskNotes > Integrations > HTTP API enabled?")


state = call("GET", "/status")["data"]
if state.get("isRunning"):
    call("POST", "/pause")
    print("paused")
elif state.get("currentSession"):
    call("POST", "/resume")
    print("resumed")
else:
    call("POST", "/start", {"duration": MINUTES})
    print(f"started {MINUTES} min session")
