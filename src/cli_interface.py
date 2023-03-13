from src.web3MCserver_logic import Web3MCserverLogic
from .utils.interpreter import Interpreter
from .utils.download_dependencies import download_dependencies
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Cli_interface:
    def __init__(self, web3mcserver):
        self.web3mcserver = web3mcserver
        # constructor logic here

    def instructions_on_how_to_set_their_own_server(self):
        print("[INFO] Put your executable in ./sync/server folder and change the command to run the program in ./playit-cli_config/main_server_config.toml")
        print("[INFO] You just need to change the fields \"command\" and \"command_args\"")

    def ask_question(self, question):
        while True:
            user_input = input("[PROMPT] " + question + " (y/n) ")
            if user_input.lower() == "y":
                return True
            elif user_input.lower() == "n":
                return False
            else:
                print("Invalid input. Please enter 'y' or 'n'.")

    def process_of_making_new_playitcli_secret(self):
        if not self.web3mcserver.file_empty(os.path.join(self.web3mcserver.secrets_path, self.web3mcserver.secret_syncthing_playitcli)):
            print("[WARNING] secrets file not empty, to continue they have to be overridden")
            print(["[INFO] control the number of tunnels and agents in your account as it is limited, it is recommended to delete all existing agents and tunnels before creating a new server with this tool: https://playit.gg/account/overview"])
            if not self.ask_question("continue? the existing secrets will be overridden"):
                print(["[INFO] exiting..."])
                exit()
        print("[INFO] to make a new secret, you'll need to login and accept the agent in your browser")
        playit_sycthing_secret = self.web3mcserver.playitcli_manager.make_new_secret()
        self.web3mcserver.write_secret_playitcli_file(playit_secret = playit_sycthing_secret, syncthing_secret = True)
        print("[INFO] writing hash secret to secret_syncthing_playitcli.txt")
        print("[INFO] We need another secret for the main server")
        playit_main_secret = self.web3mcserver.playitcli_manager.make_new_secret()
        self.web3mcserver.write_secret_playitcli_file(playit_secret = playit_main_secret, syncthing_secret = False)
        print("[INFO] writing hash secret to secret_main_playitcli.txt")

    def running_loop(self, firstTime = False):

        #self.web3mcserver.common_config_file_manager.update_common_config_file(recalculate_server_run_priority = True, Is_Host = False)

        while True:
            self.web3mcserver.common_config_file_manager.update_common_config_file(recalculate_server_run_priority = False, Is_Host = False)
            self.web3mcserver.syncthing_manager.launch_syncthing_in_separate_thread(with_playitgg = False) # with_playitgg = False means it won't be available to the world
            if firstTime: # if it's first time we need to manually connect to the first peer
                firstTime = False
                print("[INFO] Checking remote syncthing server to connect to...")
                while not self.web3mcserver.syncthing_manager.syncthing_active(self.web3mcserver.get_syncthing_server_address()):
                    print("[WARNING] No remote machine online, nowhere to pull server from, checking every 30 seconds...")
                    time.sleep(30)
                syncthing_details_to_connect = self.web3mcserver.syncthing_manager.get_remote_syncthing_ID()
                self.web3mcserver.syncthing_manager.connect_to_syncthing_peer(syncthing_details_to_connect)
            print("[INFO] Setting up observer for common_conf_file changes...")
            self.web3mcserver.observer_of_common_conf_file() # only gets out of here when we are gonna be host
            self.web3mcserver.syncthing_manager.terminate_syncthing(self.web3mcserver.local_syncthing_address, self.web3mcserver.syncthing_process)
            self.web3mcserver.syncthing_process = None

            try:
                self.web3mcserver.syncthing_manager.launch_syncthing_in_separate_thread(with_playitgg = True) # with_playitgg = False means it will be available to the world
                self.web3mcserver.common_config_file_manager.update_common_config_file(recalculate_server_run_priority = False, Is_Host = True)
                self.web3mcserver.i_will_be_host_now(save_main_erver_address_in_secrets = False) # Should only get out of here when won't be/isn't host anymore (there is a better machine)
            except:
                print("[Warning] An exception has ocurred, continuing as cluster member but not becoming host...")
            self.web3mcserver.syncthing_manager.terminate_syncthing(self.web3mcserver.local_syncthing_address, self.web3mcserver.syncthing_process)
            self.web3mcserver.syncthing_process = None

    def start(self):
        download_dependencies()

        # Set Exit function
        self.web3mcserver.set_exit_function()

        # -------- Create Missing Files & Folders -------- #
        self.web3mcserver.create_directories_from_path(self.web3mcserver.server_folder_path)
        # todo check all the missing folders etc...
        if not self.web3mcserver.file_exists(os.path.join(self.web3mcserver.secrets_path, self.web3mcserver.secret_syncthing_playitcli)):
            print("[INFO] secret_syncthing_playitcli.txt doesn't exist\ncreating...")
            self.web3mcserver.write_secret_playitcli_file(syncthing_secret = True)
        # -------- Create Missing Files & Folders -------- #

        # Update Configuration file with my performance every 2 hours
        self.web3mcserver.common_config_file_manager.update_common_config_file_periodically()

        #self.web3mcserver.common_config_file_manager.update_common_config_file()
        #exit()

        if self.web3mcserver.common_config_file_manager.is_new_node():
            print("[INFO] New Node!")
            if self.ask_question("Do you want to create a new distributed server?"):
                if not self.web3mcserver.file_empty(os.path.join(self.web3mcserver.secrets_path, self.web3mcserver.secret_syncthing_playitcli)):
                    if not self.ask_question("secrets file not empty, use current secret?"):
                        self.process_of_making_new_playitcli_secret()
                else:
                    self.process_of_making_new_playitcli_secret()
                if not self.web3mcserver.files_exist_in_server_folder():
                    if self.ask_question("Do you want a Minecraft server? (1.19.3)"):
                        print("[INFO] Downloading Minecraft server...")
                        self.web3mcserver.download_minecraft_server()
                        print("[INFO] Minecraft server downloaded.")
                    else:
                        self.instructions_on_how_to_set_their_own_server()
                else:
                    print("[INFO] Files exist in server folder, make sure the following steps were taken for it to work:")
                    self.instructions_on_how_to_set_their_own_server()
                self.web3mcserver.syncthing_manager.launch_syncthing_in_separate_thread(with_playitgg = True)
                self.web3mcserver.common_config_file_manager.update_common_config_file(recalculate_server_run_priority = False, Is_Host = True)
                self.web3mcserver.i_will_be_host_now(save_main_erver_address_in_secrets = True)
            else:
                if not self.web3mcserver.file_empty(os.path.join(self.web3mcserver.secrets_path, self.web3mcserver.secret_syncthing_playitcli)):
                    '''if self.web3mcserver.files_exist_in_server_folder():
                        if self.ask_question("[WARNING] Files have been found in server folder, they need to be deleted to continue. Proceed?"):
                            self.web3mcserver.delete_files_inside_server_folder()
                        else:
                            print("[INFO] Exiting...")
                            return'''

                    # Next steps:
                    # Make the update common config file also check for errors, like multiple hosts or if the host machine isn't connected.
                    # you should use the endpoint here: curl -X GET -H "X-API-Key: tOGFgTtkLAo7BNlrC6jT" http://released-frames.at.ply.gg:61664/rest/system/connections
                    # to check witch peers are online.
                    # make observer that checks for changes in the confijguration file, if changes are detected then, you should check if we're going to get new host,
                    # if yes, check witch machine is going to be the host.
                    # If I'm not going to be the host, do nothing, else, gotta kill and restart syncthing with playitcli
                    '''


In the thread that's observing the common config file:
If there is a change, check if there is no host OR if we get no response from server, if yes tehn:
    Check from online peers and server_priority who'll be the new host. (If it is me, then the thread should end and I should catch it with a join in the main code to then kill off syncthing and do everything again.)  
If I AM HOST NOW - Call function to kill syncthing and minecraft servers if needed and call i_am_host and other appropriate functions (the I_am_host method should make also a thread that checks if he should keep being host or not, if not, it should call this function with the parameter not-host.

If it isn't me the new host, then timeout 30 * the place in the queu that I am (every 30 seconds should still check, and if the host is active then it should just resume normal work), if server isn't active by the end of the countdown I am gonna be host now 

Also add a tread while running when host that checks if the PlayitHost ip is still responding (it seems like it might dies sometimes?)

                    '''

                    self.running_loop(firstTime = True)

                    while True:
                        time.sleep(86400)

                else:
                    print("Add the secrets file")
        else:
            print("[INFO] Not New Node")
            if not self.web3mcserver.syncthing_manager.exist_tunnels_with_this_secret():
                print("[ERROR] no secrets file found or this account has no tunnels active.")
                print("[ERROR] With this kind of problems you can try to delete the sync folder /sync/, and delete the syncthing files in /syncthing_config/, and check the secret files are correct in /secrets/, and try to connect to the cluster again as a new node.")
                return
            else:
                if not self.web3mcserver.syncthing_manager.there_are_active_tunnels():
                    print("WARNING, no peers active or hosting, it is not possible to confirm that I have the latest version of the server.\nStarting anyways")
                    self.web3mcserver.i_will_be_host_now()
                else:
                    self.web3mcserver.common_config_file_manager.put_observer_for_changes()
                    self.web3mcserver.common_config_file_manager.update_common_config_file_periodically()

