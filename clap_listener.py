import pyaudio
import numpy as np
import time
import subprocess
import webbrowser

# Audio stream parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
THRESHOLD = 800  # Sensitivity threshold, may need adjustment
CLAP_MAX_DELAY = 1.0  # Max seconds between claps to be considered a double clap
CLAP_MIN_DELAY = 0.15 # Min seconds between claps (debounce)

def play_ironman_theme():
    # Opens the YouTube Back in Black Iron Man video
    print("Opening YouTube: Back In Black...")
    webbrowser.open("https://www.youtube.com/watch?v=pAgnJENN4L8")

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

def run_cmatrix():
    print("Running cmatrix in a new Terminal...")
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

def trigger_automations():
    print("Double clap detected! Triggering automations 🔥")
    open_vscode()
    run_cmatrix()
    play_ironman_theme()
    print("Automations deployed. Resuming listening...")

def listen_for_claps():
    p = pyaudio.PyAudio()

    try:
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
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    listen_for_claps()
