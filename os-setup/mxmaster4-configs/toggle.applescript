on run
    toggle()
end run

on toggle()
    try
        set r to do shell script "/usr/bin/python3 /Users/sheikhfahan/bin/pomodoro/toggle.py 2>&1"
    on error e number n
        set r to "ERROR " & n & ": " & e
    end try
    try
        display notification r with title "Pomodoro"
    end try
end toggle
