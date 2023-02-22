from python.download_dependencies import *
import os
import subprocess
import platform
import distro
import threading

def start_syncthing():
    print("Starting Syncthing...")

    subprocess.run([bin_path + "/syncthing/syncthing", "--home", "./syncthing_config"])

def start_playit_cli():
    print("Starting Playit-cli...")

    new_client_connecting()

    subprocess.run([bin_path + "/playit-cli", "launch", "./../playit-cli_config/config.toml"], cwd="./server")

    # cwd used so server fis are generated in the right place
    # final playit-gg command might be: playit-cli --secret 9cdb9e37b46ef10baa7d15f2c1d84b9852ddfc4d7085c5ae7dfe49399f63872a run 9e0a3886-8b6d-403a-9755-1d67987eb440=192.168.1.109:25565
    # Example: ./bin/nixos/playit-cli launch ./playit-cli_config/config.toml

def new_client_connecting():
    print("ok")

def main():
    download_dependencies()
    if not os.path.exists("secrets/secrets.txt"):
        print("secrets.txt doesn't exist")
        # create secrets folder if it doesn't exist
        if not os.path.exists("secrets"):
            os.makedirs("secrets")
        # create secrets.txt file and write nothing inside
        with open('secrets/secrets.txt', 'w') as f:
            pass
        print("creating... put your secret inside ./secrets/secrets.txt and run me again")
        return


    base_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_path)

    system = platform.system()
    global bin_path

    if system == 'Windows':
        bin_path = os.path.join(base_path, 'bin', 'windows')
    elif system == 'Linux':
        if 'NixOS' in distro.name():
            bin_path = os.path.join(base_path, 'bin', 'nixos')
        else:
            bin_path = os.path.join(base_path, 'bin', 'linux')
    else:
        print(f"Unsupported system: {system}")
        return

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


    #threading.Thread(target=start_syncthing).start()
    #threading.Thread(target=start_playit_cli).start()
    
if __name__ == "__main__":
    main()

def mian2(){
    if new_node_and_update_syncthing_common_file():
        if files_exist_in_server_folder(): # this can go inside the function above
            print("files have been found in server folder, if you don't choose to make a new distributed server, they will be deleted in order to sync the server files from the server chain you'll join.")
        if user_wants_to_make_new_distributed_server():
            process_of_making_new_playit-cli_secret()
            if user_wants_minecraft_server:
                download_minecraft_server()
            else
                instructions_on_how_to_set_their_own_server()
                return
            create_common_config_file()
            launch_syncthing_in_seperate_thread()
            i_will_be_host_now()

        else:
            if secrets_file_in_place()
                delete_files_inside_server_folder()
                syncthing_details_to_connect = get_syncthing_details_from_playit-cli_python_server()
                connect_to_syncthing_peer(syncthing_details_to_connect)
                create_common_config_file()
                launch_syncthing_in_seperate_thread()
                i_will_be_host_now()
            else
                print("Add the secrets file")
# ===============================================================                
    else:
        if check_for_active_tunnels():
            if no_tunnels_are_active():
                display_warning_message()
                run_it_has_been_determined_that_I_am_the_host_now()
            elif tunnels_are_active():
                observe_files_and_ports()
                update_sync_file_periodically()
                if observer_is_triggered_and_server_is_not_running():
                    if I_have_highest_value_and_will_be_picked_to_run_server():
                        mark_other_machines_as_not_online()
                        run_it_has_been_determined_that_I_am_the_host_now()
                    else:
                        check_if_server_is_already_running()
                else:
                    pass
        else:
            raise FatalError()
}

def list_folders():
    return os.listdir()

def check_syncthing_file():
    pass

def check_files_in_server_folder():
    pass

def make_new_distributed_minecraft_server():
    pass

def delete_files_inside_server_folder():
    pass

def connect_to_syncthing():
    pass

def launch_syncthing():
    pass

def create_common_config_file():
    pass

def run_it_has_been_determined_that_I_am_the_host_now():
    pass

'''
def main():
    check_and_update_syncthing_common_file()
    if check_if_new_node():
        if check_files_in_server_folder():
            prompt_user_to_make_new_distributed_server()
        else:
            delete_files_inside_server_folder()
            start_distributed_server()
    else:
        if check_for_active_tunnels():
            if no_tunnels_are_active():
                display_warning_message()
                run_it_has_been_determined_that_I_am_the_host_now()
            elif tunnels_are_active():
                observe_files_and_ports()
                update_sync_file_periodically()
                if observer_is_triggered_and_server_is_not_running():
                    if I_have_highest_value_and_will_be_picked_to_run_server():
                        mark_other_machines_as_not_online()
                        run_it_has_been_determined_that_I_am_the_host_now()
                    else:
                        check_if_server_is_already_running()
                else:
                    pass
        else:
            raise FatalError()
    while shutting_down:
        update_syncthing_common_file()
        close_all_threads()

def check_and_update_syncthing_common_file():
    # Check the common syncthing file and update it, if exists, I'm a new node 
    # (this file has the syncthing ID of each machine and a score based on internet speed and hardware power to see how likely it is to be picked to host, and weather each one is online or not, and witch one is running the server) 

def check_if_new_node():
    # Check if I'm a new node by checking the syncthing common file

def check_files_in_server_folder():
    # Check if there are files in the server folder

def prompt_user_to_make_new_distributed_server():
    # Question If I want to make a new distributed minecraft server? 
    # YES - 
    # Walk user through the process of making a new secret with playit-cli: 
    # playit-cli claim generate && playit-cli claim url <CODE> && playit-cli claim exchange <CODE>, 
    # then you can put the secret in the `./secrets/secrets.txt` file 
    # Download minecraft 1.19.3 jar file and put it in the server folder. 
    # Launch syncthing in another thread. 
    # Create the common config file 
    # Run it_has_been_determined_that_I_am_the_host_now()

def delete_files_inside_server_folder():
    # Delete the files inside ./server

def start_distributed_server():
    # Send a message to the playit-cli python tunnel with secret 
    # If no answer, wait, and send a new message every 30 seconds 
    # Get details to connect to syncthing 
    # Send message to connect to syncthing | have syncthing auto accept and sync the folders, and everyone is an introducer 
    # Launch syncthing in another thread. 
    # Create the common config file 
    # Run it_has_been_determined_that_I_am_the_host_now()

def check_for_active_tunnels():
    # Uses secret and checks out tunnels

def no_tunnels_are_active():
    # None of the tunnels are active

def display_warning_message():
    # Warning message saying that it's not possible to confirm that I have the latest version of the server, starting anyways.

def run_it_has_been_determined_that_I_am_the_host_now():
    # Run a thread that checks every 20min for peers that are not Online 
    # and updates them in the common syncthing file if it is not up to date. 
    # Check if all files have been synced, if I have the latest version of the files, if not, wait for them to finish syncing
'''