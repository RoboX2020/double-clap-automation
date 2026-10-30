# ============================================================================
# Double Clap Automation - clap twice near your laptop and it fires off a
# little celebration sequence: opens VS Code, runs cmatrix (the Matrix
# falling-code screensaver) in a new Terminal window, and plays the
# Iron Man / Back In Black video on YouTube.
#
# HOW IT WORKS, IN PLAIN WORDS:
#   The program listens to the microphone nonstop. Every split second it
#   measures how loud the room is. A loud spike = maybe a clap. Two spikes
#   that land between 0.15 and 1.0 seconds apart = a double clap, and the
#   automation sequence fires.
#
# IMPORTANT: this program is macOS-only. It uses the Mac commands "open"
# and "osascript" to launch apps. It will not work on Windows/Linux without
# changing those parts.
#
# BEFORE YOU RUN:
#   - Install the libraries: pip install pyaudio numpy
#     (pyaudio can be stubborn on a fresh Mac: brew install portaudio first)
#   - Install cmatrix if you want the Matrix effect: brew install cmatrix
#   - Give your terminal app microphone permission when macOS asks.
#
# WHEN DEBUGGING:
#   - It triggers on random noise: raise THRESHOLD below.
#   - It misses your claps: lower THRESHOLD.
#   - One clap counts as many: raise CLAP_MIN_DELAY a little.
# ============================================================================

# microphone access
import pyaudio
# number arrays: the microphone audio arrives as numbers
import numpy as np
# built-in: measures the gap between claps
import time
# built-in: launches other programs (VS Code, Terminal)
import subprocess
# built-in: opens a URL in your default browser
import webbrowser

# Audio stream parameters
# how many audio measurements we read at a time
CHUNK = 1024
# each measurement is a 16-bit whole number (standard CD-style audio)
FORMAT = pyaudio.paInt16
# mono: one ear is enough for clap detection
CHANNELS = 1
# 44,100 measurements per second (CD quality)
RATE = 44100
THRESHOLD = 800  # Sensitivity threshold, may need adjustment
CLAP_MAX_DELAY = 1.0  # Max seconds between claps to be considered a double clap
CLAP_MIN_DELAY = 0.15 # Min seconds between claps (debounce)

# Fun action 1: play the theme song in the browser.
def play_ironman_theme():
    # Opens the YouTube Back in Black Iron Man video
    print("Opening YouTube: Back In Black...")
    webbrowser.open("https://www.youtube.com/watch?v=pAgnJENN4L8")

# Fun action 2: open VS Code in the current folder.
def open_vscode():
    print("Opening VS Code...")
    import sys
    import os
    # Assuming code is installed, or try using macOS 'open'
    try:
        # Using open -b to launch via Bundle ID so it works even if 'code' isn't in PATH
        subprocess.run(["open", "-b", "com.microsoft.VSCode", "."], check=True)
    except Exception as e:
        print(f"Could not open VS Code: {e}")

# Fun action 3: open a new Terminal window and run cmatrix in it.
def run_cmatrix():
    print("Running cmatrix in a new Terminal...")
    # AppleScript is macOS's built-in way to boss other apps around. This
    # snippet tells the Terminal app to run the cmatrix command.
    applescript_code = """
    tell application "Terminal"
        do script "export PATH=/opt/homebrew/bin:$PATH && cmatrix"
        activate
    end tell
    """
    try:
        subprocess.run(["osascript", "-e", applescript_code])
    except Exception as e:
        print(f"Could not open Terminal to run cmatrix: {e}")

# Runs the whole celebration once a double clap is confirmed.
def trigger_automations():
    print("Double clap detected! Triggering automations 🔥")
    open_vscode()
    run_cmatrix()
    play_ironman_theme()
    print("Automations deployed. Resuming listening...")

# The main loop: listen to the microphone and watch for double claps.
# Runs forever until you press Ctrl+C.
def listen_for_claps():
    p = pyaudio.PyAudio()

    try:
        # Open the microphone stream with the settings from the top of the file.
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
    except OSError as e:
        print(f"Failed to open microphone: {e}")
        return

    print("==================================================")
    print("Listening for Double Claps...")
    print("Clap twice within 1 second to trigger the sequence.")
    print("Press Ctrl+C to stop.")
    print("==================================================")

    # when the most recent clap happened (0 = no clap yet)
    last_clap_time = 0

    try:
        while True:
            # Read chunk of audio
            data = stream.read(CHUNK, exception_on_overflow=False)
            
            # Convert string to numpy array format
            audio_data = np.frombuffer(data, dtype=np.int16)
            
            # Calculate RMS (volume level)
            # Need to handle potential warnings if array is empty
            if len(audio_data) > 0:
                rms = np.sqrt(np.mean(np.square(audio_data.astype(np.float32))))
            else:
                rms = 0

            # Detect a clap
            if rms > THRESHOLD:
                current_time = time.time()
                time_since_last_clap = current_time - last_clap_time

                # Check if it was a double clap
                if CLAP_MIN_DELAY < time_since_last_clap < CLAP_MAX_DELAY:
                    trigger_automations()
                    # Reset last_clap_time to prevent immediate re-trigger
                    last_clap_time = 0
                    
                    # Sleep slightly to prevent immediate bounce back
                    time.sleep(2.0)
                    # Clear out the stream buffer to avoid processing old data
                    stream.read(stream.get_read_available(), exception_on_overflow=False)
                elif time_since_last_clap >= CLAP_MAX_DELAY:
                    # First clap
                    # print("Single clap detected") # Uncomment for debugging
                    last_clap_time = current_time
                
                # If time_since_last_clap <= CLAP_MIN_DELAY, ignore (debounce, same clap continuous loud noise)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        # Whatever happens, release the microphone politely on the way out.
        stream.stop_stream()
        stream.close()
        p.terminate()

# Only start listening when this file is run directly.
if __name__ == "__main__":
    listen_for_claps()
