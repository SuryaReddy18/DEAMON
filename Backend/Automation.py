from AppOpener import close, open as appopen
from webbrowser import open as webopen
from pywhatkit import search, playonyt
from dotenv import dotenv_values
import subprocess
import keyboard
import asyncio
import os
import screen_brightness_control as sbc
import pyttsx3
import psutil
import pygetwindow as gw
import re
import shutil

# Load environment variables
env_vars = dotenv_values(".env")

# Initialize text-to-speech engine
engine = pyttsx3.init()

def speak(text):
    """Convert text to speech."""
    engine.say(text)
    engine.runAndWait()

def OpenYouTube():
    """Open YouTube in the default web browser."""
    webopen("https://www.youtube.com")
    return True

def CheckBattery():
    """Check the battery percentage and give a warning if it's low."""
    battery = psutil.sensors_battery()
    if battery is None:
        return "Battery information is not available on this system."

    percent = battery.percent
    charging = "charging" if battery.power_plugged else "not charging"

    # ✅ Warn if battery is below 20%
    if percent < 20 and not battery.power_plugged:
        return f"⚠️ Battery low! Only {percent}% remaining. Please charge it up!"
    
    return f"Battery is at {percent}% and is currently {charging}."

def CheckCPU():
    """Check CPU usage and system load status."""
    cpu_usage = psutil.cpu_percent(interval=1)  # Get CPU usage over 1 second

    # ✅ Warn if CPU usage is high
    if cpu_usage > 80:
        return f"⚠️ High CPU usage detected! Currently at {cpu_usage}%."
    elif cpu_usage < 20:
        return f"✅ CPU usage is low, currently at {cpu_usage}%."
    else:
        return f"🔄 CPU usage is moderate at {cpu_usage}%."

def CreateFileOrFolder(command):
    """Create a file or folder based on the command."""
    try:
        print(f"🛠️ Processing command: {command}")  # ✅ Debugging log

        # ✅ Remove special characters (like "?")
        command = re.sub(r"[^\w\s]", "", command)

        if " on " not in command and " inside " not in command:
            print("❌ Invalid format! Use 'create file <name> inside <folder>' or 'create folder <name> on <directory>'.")
            return None

        # ✅ Detect whether to use "on" or "inside"
        if " on " in command:
            action_part, location = command.lower().split(" on ", 1)
        elif " inside " in command:
            action_part, location = command.lower().split(" inside ", 1)
        else:
            print("❌ Invalid format! Use 'create file <name> inside <folder>' or 'create folder <name> on <directory>'.")
            return None

        action_words = action_part.split()

        if len(action_words) < 3:
            print("❌ Invalid command structure! Use 'create file <name>' or 'create folder <name>'.")
            return None

        action = " ".join(action_words[:2])  # "create file" or "create folder"
        name = " ".join(action_words[2:])   # Extract file/folder name

        # ✅ Correctly Map "Desktop" and Other Paths
        if location.strip().lower() == "desktop":
            location = os.path.join(os.path.expanduser("~"), "Desktop")
        else:
            location = os.path.join(os.path.expanduser("~"), "Desktop", location)

        # ✅ Ensure parent folder exists
        if not os.path.exists(location):
            print(f"⚠️ Directory '{location}' does not exist. Creating it...")
            os.makedirs(location, exist_ok=True)

        target_path = os.path.join(location, name)

        if action == "create file":
            # ✅ Check if file already exists
            if os.path.exists(target_path):
                print(f"⚠️ File '{name}' already exists inside '{location}'.")
                return None
            with open(target_path, "w", encoding="utf-8") as file:
                file.write("")  # Create an empty file
            print(f"✅ File '{name}' created inside '{location}'")

        elif action == "create folder":
            # ✅ Check if folder already exists
            if os.path.exists(target_path):
                print(f"⚠️ Folder '{name}' already exists inside '{location}'.")
                return None
            os.makedirs(target_path, exist_ok=True)
            print(f"✅ Folder '{name}' created inside '{location}'")

        else:
            print(f"❌ Unknown action: {action}")
            return None

        return target_path

    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def CopyOrDeleteFileOrFolder(command):
    """Copy or delete files/folders based on the command."""
    try:
        print(f"🛠️ Processing command: {command}")  # ✅ Debugging log

        # ✅ Remove special characters
        command = re.sub(r"[^\w\s.]", "", command)  # Allow dots for file extensions

        if "copy" in command and "to" in command:
            # ✅ Handling copy operation
            parts = command.split(" to ")
            if len(parts) != 2:
                print("❌ Invalid format! Use 'copy <file/folder> to <destination>'.")
                return None

            source_input = parts[0].replace("copy ", "").strip()
            destination_folder = parts[1].strip()

            # ✅ Handling "copy <file> from <folder> to <destination>"
            if " from " in source_input:
                file_name, folder_name = source_input.split(" from ")
                folder_path = os.path.join(os.path.expanduser("~"), "Desktop", folder_name.strip())

                # ✅ Ensure folder exists
                if not os.path.exists(folder_path):
                    print(f"⚠️ Folder '{folder_name}' does not exist on Desktop.")
                    return None

                # ✅ Find the file inside the folder (even if it has an extension)
                matched_files = [f for f in os.listdir(folder_path) if f.startswith(file_name.strip())]

                if not matched_files:
                    print(f"❌ File '{file_name}' not found inside folder '{folder_name}'.")
                    return None

                # ✅ Use the first matching file
                source_file = os.path.join(folder_path, matched_files[0])

            else:
                # ✅ Normal file/folder case
                source_file = os.path.join(os.path.expanduser("~"), "Desktop", source_input)

            # ✅ Ensure source exists before copying
            if not os.path.exists(source_file):
                print(f"❌ Source '{source_file}' does not exist! Please check the name.")
                return None

            # ✅ Destination Path
            destination_path = os.path.join(os.path.expanduser("~"), "Desktop", destination_folder)

            # ✅ Ensure destination exists
            if not os.path.exists(destination_path):
                print(f"⚠️ Destination folder '{destination_path}' does not exist. Creating it...")
                os.makedirs(destination_path, exist_ok=True)

            # ✅ Copying file or folder
            if os.path.isdir(source_file):
                shutil.copytree(source_file, os.path.join(destination_path, os.path.basename(source_file)), dirs_exist_ok=True)
            else:
                shutil.copy2(source_file, destination_path)

            print(f"✅ '{source_file}' successfully copied to '{destination_path}'.")
            return destination_path

        elif "delete" in command:
            # ✅ Handling delete operation
            target = command.replace("delete ", "").strip()
            target_path = os.path.join(os.path.expanduser("~"), "Desktop", target)

            # ✅ Check if file/folder exists before deleting
            if not os.path.exists(target_path):
                print(f"Target '{target_path}' does not exist.")
                return None

            # ✅ Deleting file or folder
            if os.path.isdir(target_path):
                shutil.rmtree(target_path)  # Remove entire folder
            else:
                os.remove(target_path)  # Remove file

            print(f"✅ '{target_path}' has been deleted.")
            return True

        else:
            print("❌ Invalid command! Use 'copy <file/folder> to <destination>' or 'delete <file/folder>'.")
            return None

    except Exception as e:
        print(f"❌ Error: {e}")
        return None




def OpenApp(app):
    """Open an application, folder, or file."""
    app = app.strip()
    user_desktop = os.path.join(os.path.expanduser("~"), "Desktop")

    # Handle "create file" or "create folder" commands
    if app.startswith("create file") or app.startswith("create folder"):
        created_path = CreateFileOrFolder(app)
        if created_path:
            print(f"Opening created path: {created_path}")
            subprocess.Popen(["explorer", created_path], shell=True)
            return True
        else:
            return False

    # Handle "open <folder> on desktop"
    if app.endswith(" on desktop"):
        folder_name = app.replace(" on desktop", "").strip()
        target_path = os.path.join(user_desktop, folder_name)
        if os.path.exists(target_path):
            print(f"Opening {target_path}...")
            subprocess.Popen(["explorer", target_path], shell=True)
            return True
        else:
            print(f"Folder '{folder_name}' does not exist on the desktop.")
            return False

    # Handle folder or file paths
    if os.path.exists(app):
        print(f"Opening folder or file: {app}")
        subprocess.Popen(["explorer", app], shell=True)
        return True

    # Handle YouTube
    if app.lower() == "youtube":
        return OpenYouTube()

    # Handle other applications
    try:
        print(f"Trying to open {app} as an application...")
        appopen(app, match_closest=True, throw_error=True)
        return True
    except Exception as e:
        print(f"Error opening app {app}: {e}")
        print(f"Searching for {app} on Google...")
        search(app)
        return False

def GoogleSearch(Topic):
    """Perform a Google search."""
    search(Topic)
    return True

def CloseApp(app):
    """Close an application by name."""
    app = app.lower().strip()  # Normalize input

    try:
        print(f"Attempting to close: {app}")

        # Step 1: Try closing by window title
        for window in gw.getWindowsWithTitle(app):
            print(f"✅ Found window: {window.title}, closing it...")
            window.close()
            return True

        # Step 2: Auto-detect if it's a UWP (Windows Store) app
        print(f"🔍 Checking if '{app}' is a UWP app...")
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 f"Get-AppxPackage *{app}* | Select-Object -ExpandProperty PackageFamilyName"],
                capture_output=True, text=True, shell=True
            )
            uwp_package = result.stdout.strip()
            if uwp_package:
                app_name = uwp_package.split('_')[0]  # Extract the process name
                print(f"✅ Found UWP app: {uwp_package}. Closing '{app_name}' via PowerShell...")
                subprocess.run(["powershell", "-Command", f"Stop-Process -Name {app_name} -Force"], shell=True)
                return True
        except Exception as e:
            print(f"⚠️ UWP detection error: {e}")

        # Step 3: If running inside a browser, close the browser
        browsers = ["chrome", "msedge", "firefox", "opera", "brave"]
        for browser in browsers:
            if app in browser:
                print(f"🔍 {app.capitalize()} might be running in {browser}. Closing {browser}...")
                return CloseApp(browser + ".exe")

        # Step 4: Check if it's a normal desktop app (EXE) and close it
        for process in psutil.process_iter(attrs=['pid', 'name']):
            process_name = process.info['name'].lower()
            if app in process_name:
                print(f"✅ Found process {process.info['name']} (PID {process.info['pid']}), closing it...")
                psutil.Process(process.info['pid']).terminate()
                return True

        print(f"❌ No running process or window found for: {app}")
        return False

    except Exception as e:
        print(f"Error closing {app}: {e}")
        return False

def System(command):
    """Execute system commands like volume control or brightness adjustment."""
    command = command.strip().lower()
    actions = {
        "mute": lambda: keyboard.press_and_release("volume mute"),
        "unmute": lambda: keyboard.press_and_release("volume unmute"),
        "volume up": lambda: keyboard.press_and_release("volume up"),
        "volume down": lambda: keyboard.press_and_release("volume down"),
        "brightness up": lambda: sbc.set_brightness(min(sbc.get_brightness()[0] + 10, 100)),
        "brightness low": lambda: sbc.set_brightness(max(sbc.get_brightness()[0] - 10, 0)),
    }
    if command in actions:
        try:
            actions[command]()
            print(f"Executed: {command}")
            return True
        except Exception as e:
            print(f"Error executing '{command}': {e}")
            return False
    else:
        print(f"System command '{command}' not recognized.")
        return False

def PlaySong(song_name, platform="youtube"):
    """Play a song on YouTube or Spotify."""
    try:
        if platform.lower() == "spotify":
            print(f"🎵 Playing {song_name} on Spotify...")
            webopen(f"https://open.spotify.com/search/{song_name.replace(' ', '%20')}")
        else:
            print(f"🎵 Playing {song_name} on YouTube...")
            playonyt(song_name)  # ✅ Play the song using pywhatkit
        return True
    except Exception as e:
        print(f"⚠️ Error playing song '{song_name}': {e}")
        return False

def RunMouseControl():
    """Run the mouse control script (mouse.py)."""
    try:
        # Provide the full path to mouse.py
        script_path = "C:\DAEMON\Backend\mouse_control.py"  # Update this path
        
        # Check if the file exists
        if not os.path.exists(script_path):
            print(f"⚠️ Error: 'mouse_control.py' not found at {script_path}.")
            return False

        # Run the mouse.py script
        print(f"🖱️ Starting mouse control from {script_path}...")
        subprocess.run(["python", script_path], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Error running mouse control: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")
        return False

async def TranslateAndExecute(commands: list[str]):
    """Translate and execute commands asynchronously."""
    funcs = []
    for command in commands:
        print(f"🔍 Processing command: {command}")
        if command.startswith("copy"):
            # ✅ Handle 'copy <file> from <folder> to <destination>'
            match = re.match(r"copy (\S+) from (\S+) to (\S+)", command)
            if match:
                file_name, source_folder, destination_folder = match.groups()
                funcs.append(asyncio.to_thread(CopyOrDeleteFileOrFolder, f"copy {file_name} from {source_folder} to {destination_folder}"))
            else:
                print(f"⚠️ Invalid copy format: {command}")
                continue

        if command.startswith("open"):
            funcs.append(asyncio.to_thread(OpenApp, command.removeprefix("open ")))
        elif command.startswith("close"):
            funcs.append(asyncio.to_thread(CloseApp, command.removeprefix("close ")))
        elif command.endswith("search on google"):
            funcs.append(asyncio.to_thread(GoogleSearch, command.removesuffix("search on google")))
        elif command.startswith("system"):
            funcs.append(asyncio.to_thread(System, command.removeprefix("system ")))
        elif command.startswith("play"):
            song_name = command.replace("play ", "").strip()
            funcs.append(asyncio.to_thread(PlaySong, song_name))
        elif command.startswith("create file") or command.startswith("create folder"):
            print(f"🛠️ Creating file/folder: {command}")  # ✅ Debugging log
            funcs.append(asyncio.to_thread(CreateFileOrFolder, command))  # ✅ FIXED
        elif "battery percent" in command or "battery status" in command:
            funcs.append(asyncio.to_thread(CheckBattery))  # ✅ Get battery info
        elif command.startswith("system cpu"):
            funcs.append(asyncio.to_thread(CheckCPU))
        elif  command.startswith("delete"):
            print(f"🛠️ Deleting file/folder: {command}") 
            funcs.append(asyncio.to_thread(CopyOrDeleteFileOrFolder, command))   
        elif command == "run mouse control":
            funcs.append(asyncio.to_thread(RunMouseControl))  # ✅ Run mouse control
        else:
            print(f"⚠️ No function found for {command}")

    results = await asyncio.gather(*funcs)
    return results

async def Automation(commands: list[str]):
    """Automate the execution of commands."""
    results = await TranslateAndExecute(commands)
    for result in results:
        if isinstance(result, str):
            print(result)
    return True

if __name__ == "__main__":
    asyncio.run(Automation([
        "copy Model from major to minor"
    ]))