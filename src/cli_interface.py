from .utils.interpreter import Interpreter
from .utils.download_dependencies import download_dependencies

class Cli_interface:
    def __init__(self, web3mcserver):
        self.web3mcserver = web3mcserver
        # constructor logic here

    def instructions_on_how_to_set_their_own_server(self):
        print("[INFO] Put your executable in ./server folder and change the command to run the program in ./playit-cli_config/config.toml")

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
        if not self.web3mcserver.secrets_file_empty():
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

        # self.web3mcserver.syncthing_manager.launch_syncthing_in_separate_thread(save_syncthing_server_address_in_secrets = True) # todo implement

        # Set Exit function
        self.web3mcserver.set_exit_function()

        # this should not go here
        if not self.web3mcserver.secret_file_exists():
            print("secret_syncthing_playitcli.txt doesn't exist\ncreating... put your secret inside ./secrets/secret_syncthing_playitcli.txt and run me again")
            self.web3mcserver.write_secret_playitcli_file()

        if self.web3mcserver.common_config_file_manager.is_new_node_and_update_common_config_file(): # todo implement
            if self.ask_question("Do you want to create a new distributed server?"):
                if not self.web3mcserver.secrets_file_empty():
                    if not self.ask_question("secrets file not empty, use current secret?"):
                        self.process_of_making_new_playitcli_secret()
                else:
                    self.process_of_making_new_playitcli_secret()
                if not self.web3mcserver.files_exist_in_server_folder():
                    if self.ask_question("Do you want a Minecraft server?"):
                        self.web3mcserver.download_minecraft_server()
                    else:
                        self.instructions_on_how_to_set_their_own_server()
                else:
                    self.instructions_on_how_to_set_their_own_server()
                self.web3mcserver.common_config_file_manager.create_common_config_file() # todo implement

                self.web3mcserver.syncthing_manager.launch_syncthing_in_separate_thread(save_syncthing_server_address_in_secrets = True) # todo implement
                self.web3mcserver.i_will_be_host_now(save_main_erver_address_in_secrets = True) # todo implement
            else:
                if self.web3mcserver.secrets_file_in_place():
                    if self.web3mcserver.files_exist_in_server_folder():
                        if self.ask_question("Files have been found in server folder, they need to be deleted to continue. Proceed?"):
                            self.web3mcserver.delete_files_inside_server_folder()
                        else:
                            return
                    syncthing_details_to_connect = self.web3mcserver.syncthing_manager.get_syncthing_details_from_playit_cli_python_server()
                    self.web3mcserver.syncthing_manager.connect_to_syncthing_peer(syncthing_details_to_connect)
                    self.web3mcserver.common_config_file_manager.create_common_config_file()
                    self.web3mcserver.syncthing_manager.launch_syncthing_in_separate_thread()
                    self.web3mcserver.i_will_be_host_now()
                else:
                    print("Add the secrets file")
        else:
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

