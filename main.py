import os
import threading
import time
from typing import List, Dict
from playit_cli import PlayitCLI
from syncthing_cli import SyncthingCLI
import subprocess

PLAYIT_CLI_PATH = os.path.join('bin', 'nixos', 'playit-cli')
SYNCTHING_PATH = os.path.join('bin', 'nixos', 'syncthing', 'syncthing')
SERVER_PATH = 'server'
SECRETS_PATH = os.path.join('secrets', 'secrets.txt')
COMMON_FILE_PATH = os.path.join('syncthing', 'common.xml')

def list_folders():
    return os.listdir()

def check_syncthing_file():
    # Check if the syncthing file exists
    if not os.path.exists(SYNCTHING_FILE):
        create_syncthing_file()
    
    # Check if the file is up to date
    with open(SYNCTHING_FILE, 'r') as f:
        data = json.load(f)

    # Check if the file has an ID for this machine
    if str(HOST_ID) not in data['machines']:
        data['machines'][HOST_ID] = {
            'score': 0, 
            'status': 'offline', 
            'server': False
        }

    # Update the score of the machine
    data['machines'][HOST_ID]['score'] = get_machine_score()

    # Check if the server is running on this machine
    if playit_cli.check_server():
        data['machines'][HOST_ID]['server'] = True
    else:
        data['machines'][HOST_ID]['server'] = False
    
    # Check the status of the machines
    for machine in data['machines']:
        if machine != str(HOST_ID):
            if data['machines'][machine]['status'] != 'online':
                data['machines'][machine]['status'] = check_machine_status(machine)
    
    # Write the data back to the file
    with open(SYNCTHING_FILE, 'w') as f:
        json.dump(data, f)

def check_files_in_server_folder():
    # Checks if there are files in the server folder
    # If there are files in the server folder, inform the user
    # that they will be deleted if a new server is not made.
    # If there are no files in the server folder, continue silently.

    if os.path.isdir(SERVER_FOLDER):
        files = os.listdir(SERVER_FOLDER)
        if len(files) > 0:
            print("There are files in the server folder.")
            print("If you don't make a new minecraft server,")
            print("these files will be deleted.")
    else:
        os.makedirs(SERVER_FOLDER)  # Creates the server folder if it does not exist.


def make_new_distributed_minecraft_server():
    print('Checking for existing server files')
    if os.path.isdir(SERVER_PATH) and os.listdir(SERVER_PATH):
        print('Server files exist, if we don\'t create a new Minecraft server they will be deleted.')
        while True:
            answer = input('Do you want to make a new distributed Minecraft server? (y/n): ').strip().lower()
            if answer == 'y':
                break
            elif answer == 'n':
                print('Deleting existing server files')
                for root, dirs, files in os.walk(SERVER_PATH):
                    for file in files:
                        os.remove(os.path.join(root, file))
                    for dir in dirs:
                        os.rmdir(os.path.join(root, dir))
                os.rmdir(SERVER_PATH)
                print('Server files deleted')
                return
            else:
                print('Invalid answer. Please try again.')
    print('Generating PlayitCLI claim...')
    playit_cli = PlayitCLI(PLAYIT_CLI_PATH, SECRETS_PATH)
    claim_data = playit_cli.claim.generate()
    print('Go to the following URL to exchange the claim:')
    print(playit_cli.claim.get_url(claim_data['claim_code']))
    while True:
        answer = input('Have you exchanged the claim? (y/n): ').strip().lower()
        if answer == 'y':
            playit_cli.claim.exchange(claim_data['claim_code'])
            with open(SECRETS_PATH, 'w') as secrets_file:
                secrets_file.write(claim_data['secret'])
            print('Secret saved to file:', SECRETS_PATH)
            break
        elif answer == 'n':
            time.sleep(5)
        else:
            print('Invalid answer. Please try again.')
    print('Downloading Minecraft server...')
    os.makedirs(SERVER_PATH, exist_ok=True)
    minecraft_server_url = 'https://launcher.mojang.com/v1/objects/e8ff2fca07ba213c23f352a2367b8d88bfc0b719/server.jar'
    os.system(f'curl -o {os.path.join(SERVER_PATH, "server.jar")} {minecraft_server_url}')
    print('Minecraft server downloaded and saved to:', os.path.join(SERVER_PATH, 'server.jar'))
    print('Launching Syncthing...')
    syncthing_cli = SyncthingCLI(SYNCTHING_PATH)
    syncthing_cli.start()
    print('Syncthing launched')
    create_common_config_file()
    it_has_been_determined_that_I_am_the_host_now()

def delete_files_inside_server_folder():
    server_folder_path = os.path.join(".", "server")
    for filename in os.listdir(server_folder_path):
        file_path = os.path.join(server_folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def connect_to_syncthing():
    syncthing_path = './bin/nixos/syncthing/syncthing'
    syncthing_config = './config/syncthing'
    syncthing_address = '127.0.0.1:8384'
    syncthing_api_key = 'N/A'
    syncthing_auto_accept = 'true'

    # Run syncthing process
    syncthing_process = subprocess.Popen(
        [syncthing_path, f'-home={syncthing_config}', f'-gui-address={syncthing_address}', '-no-browser', '-no-restart', '-logfile=./log/syncthing.log'], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )

    # Wait for syncthing to start
    syncthing_api_key = wait_for_syncthing(syncthing_address)

    # Configure syncthing
    configure_syncthing(syncthing_address, syncthing_api_key, syncthing_auto_accept)

    return syncthing_process, syncthing_api_key

def launch_syncthing():
    syncthing_path = os.path.join(".", "bin", "nixos", "syncthing", "syncthing")
    cmd = [syncthing_path, "-no-browser"]
    subprocess.Popen(cmd)

def create_common_config_file():
    config = {
        "port": 8384,
        "apiKey": "auto",
        "devices": []
    }

    with open("./.config/syncthing/config.xml", "w") as f:
        f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
    <configuration version="33">
        <gui enabled="true" tls="false">
            <address>0.0.0.0:8384</address>
            <apiKey>{config["apiKey"]}</apiKey>
        </gui>
        <options>
            <listenAddress>0.0.0.0:{config["port"]}</listenAddress>
            <globalAnnounceServer>default</globalAnnounceServer>
            <localAnnounceServer>default</localAnnounceServer>
            <autoUpgradeIntervalH>12</autoUpgradeIntervalH>
            <minHomeDiskFree unit="%">1</minHomeDiskFree>
            <reconnectionIntervalS>60</reconnectionIntervalS>
            <startBrowser>false</startBrowser>
            <natEnabled>true</natEnabled>
            <natLeaseMinutes>60</natLeaseMinutes>
            <natRenewalMinutes>30</natRenewalMinutes>
            <urAccepted>1</urAccepted>
            <urUniqueID></urUniqueID>
            <urPostInsecurely>false</urPostInsecurely>
            <urInitialDelayS>300</urInitialDelayS>
            <restartOnWakeup>true</restartOnWakeup>
            <upgradeToPreReleases>false</upgradeToPreReleases>
            <upnpEnabled>true</upnpEnabled>
            <upnpLeaseMinutes>60</upnpLeaseMinutes>
            <upnpRenewalMinutes>30</upnpRenewalMinutes>
            <upnpTimeoutSeconds>5</upnpTimeoutSeconds>
        </options>
        <devices>
        </devices>
    </configuration>""")


def run_it_has_been_determined_that_I_am_the_host_now():
    # Run a thread that checks every 20min for peers that are not Online
    # and updates them in the common syncthing file if it is not up to date.
    threading.Thread(target=check_peers_status).start()

    # Check if all files have been synced, if I have the latest version of the files,
    # if not, wait for them to finish syncing.
    syncthing_folder_path = os.path.join(os.getcwd(), "server")
    syncthing_folder_id = syncthing.get_folder_id(syncthing_folder_path)

    while True:
        syncthing.wait_for_scan(syncthing_folder_id)

        if syncthing.is_folder_synced(syncthing_folder_id):
            break

    # Change the file informing saying that I'm going to host now
    set_i_am_host_now()

    # Launch the playit-cli python server on another thread
    playit_cli.start_server()

    # Launch the playit-cli minecraft server
    playit_cli.start_minecraft_server()


def main():
    # Check the common syncthing file and update it, if exists, I'm a new node
    check_syncthing_file()

    if new_node:
        # Check if there are files in the server folder, and say that if we don't make a new minecraft server they will be deleted.
        check_files_in_server_folder()
        # Question If I want to make a new distributed minecraft server?
        if make_new_distributed_minecraft_server():
            # Walk user through the process of making a new secret with playit-cli
            playit_cli_secret = subprocess.run(["./bin/nixos/playit-cli", "claim", "generate"], capture_output=True)
            playit_cli_secret_code = playit_cli_secret.stdout.decode("utf-8")
            playit_cli_url = subprocess.run(["./bin/nixos/playit-cli", "claim", "url", playit_cli_secret_code], capture_output=True)
            playit_cli_exchange = subprocess.run(["./bin/nixos/playit-cli", "claim", "exchange", playit_cli_secret_code], capture_output=True)
            playit_cli_secret_string = f"{playit_cli_secret_code}\n{playit_cli_url.stdout.decode('utf-8')}\n{playit_cli_exchange.stdout.decode('utf-8')}"
            # Put the secret in the ./secrets/secrets.txt file
            with open("./secrets/secrets.txt", "w") as f:
                f.write(playit_cli_secret_string)
            # Download minecraft 1.19.3 jar file and put it in the server folder.
            minecraft_download_url = "https://launcher.mojang.com/v1/objects/56bd4a2a2a39e7b8d67c3c2c2f246c9fc06a415f/server.jar"
            minecraft_jar_file = "./server/server.jar"
            subprocess.run(["wget", minecraft_download_url, "-O", minecraft_jar_file])
            # Launch syncthing in another thread
            launch_syncthing()
            # Create the common config file
            create_common_config_file()
            # Run it_has_been_determined_that_I_am_the_host_now()
            run_it_has_been_determined_that_I_am_the_host_now()
        else:
            # Delete the files inside ./server
            delete_files_inside_server_folder()
            # Send a message to the playit-cli python tunnel with secret
            # If no answer, wait, and send a new message every 30 seconds
            # Get details to connect to syncthing
            # Send message to connect to syncthing | have syncthing auto accept and sync the folders, and everyone is an introducer
            connect_to_syncthing()
            # Launch syncthing in another thread.
            launch_syncthing()
            # Create the common config file
            create_common_config_file()
            # Run it_has_been_determined_that_I_am_the_host_now()
            run_it_has_been_determined_that_I_am_the_host_now()
    else:
        # Uses secret and checks out tunnels
        # If the tunnels are clear, sends a message to the next location
    # Otherwise, sends a message to the previous location to warn them
    tunnels_clear = check_tunnels(secret)
    if tunnels_clear:
        message = "Tunnels clear. Moving to next location."
        send_message(message, next_location)
    else:
        message = "Tunnels compromised. Warning previous location."
        send_message(message, previous_location)
        # Waits for response from previous location to confirm they received the message
        response = wait_for_response()
        if response == "Message received":
            # Moves to next location once confirmation is received
            message = "Moving to next location."
            send_message(message, next_location)
            # Calls function again to repeat the process at the next location
            run_secret_mission(secret, next_location, previous_location)
        else:
            # If no confirmation is received, aborts the mission
            message = "No confirmation received. Aborting mission."
            send_message(message, "HQ")
            return
