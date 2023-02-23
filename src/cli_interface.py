from .utils.interpreter import Interpreter
from .utils.download_dependencies import download_dependencies

class Cli_interface:
    def __init__(self, web3mcserver):
        self.web3mcserver = web3mcserver
        # constructor logic here

    def instructions_on_how_to_set_their_own_server(self):
        pass

    def user_wants_to_make_new_distributed_server(self):
        pass

    def user_wants_minecraft_server(self):
        pass

    def start(self):
        download_dependencies()

        # this should not go here
        if not self.web3mcserver.secret_file_exists():
            print("secrets.txt doesn't exist\ncreating... put your secret inside ./secrets/secrets.txt and run me again")
            self.web3mcserver.create_secret_file()

        if self.web3mcserver.common_config_file_manager.new_node_and_update_common_config_file():
            if self.web3mcserver.files_exist_in_server_folder():
                print("files have been found in server folder, if you don't choose to make a new distributed server, they will be deleted in order to sync the server files from the server chain you'll join.")
            if self.user_wants_to_make_new_distributed_server():
                self.web3mcserver.process_of_making_new_playitcli_secret()
                if self.user_wants_minecraft_server:
                    self.web3mcserver.download_minecraft_server()
                else:
                    self.instructions_on_how_to_set_their_own_server()
                    return
                self.web3mcserver.common_config_file_manager.create_common_config_file()
                self.web3mcserver.syncthing_manager.launch_syncthing_in_separate_thread()
                self.web3mcserver.i_will_be_host_now()
            else:
                if self.web3mcserver.common_config_file_manager.secrets_file_in_place():
                    self.web3mcserver.delete_files_inside_server_folder()
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

