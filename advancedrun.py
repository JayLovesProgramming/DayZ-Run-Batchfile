import os
import subprocess
import time
import requests
import threading
import json
import signal  # Import signal for handling shutdown signals

query_response = ""
max_retries = 10
retry_count = 0
SERVER_IP = ""
QUERY_PORT = 27016
SERVER_LOCATION = "/DayZServer/resources"
SERVER_PORT = 2302
SERVER_CONFIG = "serverDZ.cfg"
SERVER_CPU = 2
mod_list = []
server_name = ""
monitor_thread = None
server_process = None
monitordeath_process = None  # Process for monitordeath.py
logsteamids_process = None  # New process for logsteamids.py
stop_monitor = False

def extract_server_name(config_file):
    global server_name
    with open(config_file, 'r') as f:
        for line in f:
            if "hostname" in line.lower():
                server_name = line.split('=')[1].strip().strip('"')
                break

def read_mods(mods_file):
    global mod_list
    with open(mods_file, 'r') as f:
        mod_list = [line.strip() for line in f if line.strip()]

def run_genmods():
    print("Generating the mods.txt via genmods.py")
    process = subprocess.Popen(["python", "Utils/genmods.py"], cwd=SERVER_LOCATION)
    process.wait()  # Wait for it to finish before proceeding

def start_server():
    global monitordeath_process  # Reference to the monitordeath_process
    mod_string = ";".join(mod_list)
    print(f"Starting server: {server_name} with mods: {mod_string}")
    command = [
        "./DayZServer_x64",  # Assuming the server executable is named DayZServer_x64
        "-profiles=Profiles",
        "-maxMem=2048",
        f"-mod={mod_string}",
        f"-config={SERVER_CONFIG}",
        f"-port={SERVER_PORT}",
        f"-cpuCount={SERVER_CPU}",
        "-dologs",
        "-adminlog",
        "-netlog",
        "-freezecheck"
    ]
    
    process = subprocess.Popen(command, cwd=SERVER_LOCATION)
    return process

def query_server():
    try:
        response = requests.get(f'http://dayzsalauncher.com/api/v1/query/{SERVER_IP}/{QUERY_PORT}')
        return response.text
    except requests.RequestException as e:
        print(f"Error querying server: {e}")
        return ""

def stop_server():
    global server_process, monitordeath_process
    if server_process:
        print("Stopping server...")
        server_process.terminate()
        server_process.wait()
        server_process = None
    if monitordeath_process:
        print("Stopping monitordeaths.py...")
        monitordeath_process.terminate()  # Terminate the monitordeath_process
        monitordeath_process = None  # Reset reference

def monitor_server():
    global server_process, stop_monitor
    while not stop_monitor:
        time.sleep(10)  # Check every 10 seconds
        if server_process and server_process.poll() is not None:  # If process is no longer running
            print(f"Server process terminated with exit code {server_process.poll()}. Restarting server...")
            time.sleep(5)  # Wait for 5 seconds before restarting
            stop_server()  # Ensure monitordeath_process is also stopped
            server_process = start_server()  # Restart the server

def input_handler():
    global stop_monitor
    while not stop_monitor:
        stop_confirm = input("Press Enter to stop the server or (Q) to quit monitoring: ").lower()
        if stop_confirm == 'q':
            stop_confirm = input("Are you sure you want to stop the server? (Y/N) [Enter=Yes]: ").lower()
            if stop_confirm in ('y', ''):
                stop_monitor = True
                stop_server()
                time.sleep(5)
                restart_confirm = input("Do you want to restart the batch file? (Y/N) [Enter=Yes]: ").lower()
                if restart_confirm in ('y', ''):
                    main()  # Restart the process
                break
            else:
                print("Server stop cancelled.")
        else:
            print("Server is still running.")

# New function to handle termination signals
def handle_exit_signal(signum, frame):
    print("Signal received, stopping the server...")
    stop_server()
    global stop_monitor
    stop_monitor = True
    if monitor_thread is not None:
        monitor_thread.join()  # Wait for the monitoring thread to exit
    print("Server and monitoring stopped. Exiting.")
    exit(0)

def start_another_script():
    print("Starting another script in a new command prompt...")
    # Use a raw string for the script path
    script_path = r"C:\DayZServer\resources\Utils\monitordeaths.py"

    # Open a new command prompt and run the Python script
    return subprocess.Popen(["cmd.exe", "/c", "start", "cmd.exe", "/k", f"python {script_path}"], shell=True)

def main():
    global server_process, monitordeath_process, stop_monitor, monitor_thread
    os.chdir(SERVER_LOCATION)
    extract_server_name(SERVER_CONFIG)
    read_mods("mods.txt")

    run_genmods()  # Run genmods.py before starting the server

    print(f"Loading {server_name}")
    print(f"Mod List: {', '.join(mod_list)}")

    start_confirm = input("Do you want to start the server with the above mod list? (Y/N) [Enter=Yes]: ").lower()
    if start_confirm in ('y', ''):
        stop_monitor = False
        server_process = start_server()

        print("Waiting a short period of time before querying the server...")
        time.sleep(45)

        # Wait until there is at least one player on the server
        player_found = False
        while not player_found:
            print(f"Querying Server {SERVER_IP}:{QUERY_PORT}")
            query_response = query_server()
            # print(f"Server Query Response: {query_response}")
            # print(f"Players online: {player_count}")

            try:
                # Parse the JSON response
                response_data = json.loads(query_response)
                
                # Check if the server is online and there are players
                if response_data.get("status") == 1:
                    player_count = response_data.get("players", 0)
                    print(f"Current player count: {player_count}")
                    
                    if player_count > 0:
                        print("Players found on the server. Starting monitordeaths.py...")
                        player_found = True  # We found at least one player
            except json.JSONDecodeError:
                print("Failed to decode JSON response. Retrying...")

            time.sleep(15)  # Wait before the next query

        # Start the monitordeath script only when there's at least one player
        monitordeath_process = start_another_script()  # Start monitordeaths.py here

        # Wait for a minute after starting monitordeaths.py
        time.sleep(60)  # Wait for 60 seconds

        # Start the monitor server thread to check for crashes
        monitor_thread = threading.Thread(target=monitor_server)
        monitor_thread.start()

        # Handle user input on the main thread
        input_handler()

        # Stop monitoring when user chooses to quit
        stop_monitor = True
        monitor_thread.join()  # Wait for monitor thread to exit
    else:
        print("Server start cancelled.")

if __name__ == "__main__":
    # Set up signal handlers for graceful termination
    signal.signal(signal.SIGINT, handle_exit_signal)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, handle_exit_signal)  # Handle termination (e.g., window close)
    main()
