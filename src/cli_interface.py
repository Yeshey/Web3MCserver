from src.web3MCserver_logic import Web3MCserverLogic
from .utils.interpreter import Interpreter
from .utils.download_dependencies import download_dependencies
import os
import time

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

        #self.web3mcserver.common_config_file_manager.update_common_config_file()
        #exit()

        if self.web3mcserver.common_config_file_manager.is_new_node(): # todo implement
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
                # Thread that updates configuration file every 2 hours
                self.web3mcserver.i_will_be_host_now(save_main_erver_address_in_secrets = True)
            else:
                if not self.web3mcserver.file_empty(os.path.join(self.web3mcserver.secrets_path, self.web3mcserver.secret_syncthing_playitcli)):
                    if self.web3mcserver.files_exist_in_server_folder():
                        if self.ask_question("[WARNING] Files have been found in server folder, they need to be deleted to continue. Proceed?"):
                            self.web3mcserver.delete_files_inside_server_folder()
                        else:
                            print("[INFO] Exiting...")
                            return

                    print("[INFO] Checking remote syncthing server to connect to...")
                    while not self.web3mcserver.syncthing_manager.syncthing_active(self.web3mcserver.get_syncthing_server_address()):
                        print("[WARNING] No remote machine online, nowhere to pull server from, checking every 30 seconds...")
                        time.sleep(30)

                    self.web3mcserver.syncthing_manager.launch_syncthing_in_separate_thread(with_playitgg = False)

                    syncthing_details_to_connect = self.web3mcserver.syncthing_manager.get_remote_syncthing_ID()
                    self.web3mcserver.syncthing_manager.connect_to_syncthing_peer(syncthing_details_to_connect)

                    # 2 threads, one to update the configuration file every 2 hours, one that is an observer that checks for changes in the confijguration file
                    
                    while True:
                        self.web3mcserver.common_config_file_manager.update_common_config_file(recalculate_server_run_priority = False, Is_Host = True)
                        time.sleep(30)
                else:
                    print("Add the secrets file")
        else:
            print("[INFO] Not New Node")
            if not self.web3mcserver.syncthing_manager.exist_tunnels_with_this_secret():
                print("no secrets file found or this account has no tunnels active, exiting")
                return
            else:
                if not self.web3mcserver.syncthing_manager.there_are_active_tunnels():
                    print("WARNING, no peers active or hosting, it is not possible to confirm that I have the latest version of the server.\nStarting anyways")
                    self.web3mcserver.i_will_be_host_now()
                else:
                    self.web3mcserver.common_config_file_manager.put_observer_for_changes()
                    self.web3mcserver.common_config_file_manager.update_common_config_file_periodically()

