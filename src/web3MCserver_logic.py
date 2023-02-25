from .playitCliManager import PlayitCliManager
from .syncthingManager import SyncthingManager
from .commonConfigFileManager import CommonConfigFileManager
import time
import os
import distro
import platform
import urllib.request
import toml

class Web3MCserverLogic:
    # Define the directory path
    secrets_path = "./../secrets/"
    secrets_file_name = "secrets.toml"
    server_path = "./../server/"
    minecraft_server_file_name = "server.jar"
    minecraft_server_url = "https://piston-data.mojang.com/v1/objects/c9df48efed58511cdd0213c56b9013a7b5c9ac1f/server.jar"
    playitcli_config_toml = "./../playit-cli_config/main_server_config.toml"
    syncthing_config = "./../syncthing_config"

    def __init__(self):

        # needs to be inside to not share data between instances of class
        self.bin_path = str() # for example ./bin/nixos
        self.common_config_file_manager = CommonConfigFileManager(self)
        self.syncthing_manager = SyncthingManager(self)
        self.playitcli_manager = PlayitCliManager(self)

        # ======= Figuring out witch platform I'm running on ======= #
        base_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(base_path)
        system = platform.system()
        if system == 'Windows':
            self.bin_path = os.path.join(base_path, '..', 'bin', 'windows')
        elif system == 'Linux':
            if 'NixOS' in distro.name():
                self.bin_path = os.path.join(base_path, '..', 'bin', 'nixos')
            else:
                self.bin_path = os.path.join(base_path, '..', 'bin', 'linux')
        else:
            print(f"Unsupported system: {system}")
            return
        # ======= ========================================== ======= #

        print("BIN PATH" + self.bin_path)

    def put_observer_for_changes(self):
        if self.observer_is_triggered_and_server_is_not_running():
            if self.common_config_file_manager.my_priority_position_in_common_config_file() == 0:
                self.i_will_be_host_now()
            else:
                self.check_if_server_started_correctly_or_I_need_to_host()

    def check_if_server_started_correctly_or_I_need_to_host(self):
        time.sleep(30)
        if not self.syncthing_manager.there_are_active_tunnels():
            if self.common_config_file_manager.my_priority_position_in_common_config_file() == 1: #I'm the second option
                self.common_config_file_manager.mark_other_machines_as_not_online()
                self.i_will_be_host_now()

    def shutting_down_now(self):
        self.common_config_file_manager.update_common_config_file(shutting_down = True)
        self.syncthing_manager.wait_for_sync_to_finish()
        self.close_all_threads()

    def i_will_be_host_now(self):
        # Send system notification saying that thes PC will be host now
        print("Becoming Host")
        self.common_config_file_manager.check_periodically_for_online_peers_and_updates_common_sync_file_in_separate_thread()
        self.syncthing_manager.wait_for_sync_to_finish()
        self.common_config_file_manager.update_common_config_file_to_say_that_im_new_host()
        self.playitcli_manager.launch_minecraft_playitcli_server_on_separate_thread()

    def files_exist_in_server_folder(self):
        # Check if the directory exists
        if os.path.exists(self.server_path):
            # List all files and directories in the directory
            contents = os.listdir(self.server_path)

            # Check if there are any files or directories
            if len(contents) == 0:
                return False # print("There are no files or directories in", self.server_path)
            else:
                # Check if any non-hidden files or directories exist and ignore those
                for item in contents:
                    if not item.startswith("."):
                        return True
                return False
        else:
            os.mkdir(self.server_path)
            return False # print(self.server_path, "does not exist")


    def download_minecraft_server(self):
    
        # Download the server file if it doesn't exist
        if not os.path.exists(self.server_path + self.minecraft_server_file_name):
            print("Downloading Minecraft server...")
            urllib.request.urlretrieve(self.minecraft_server_url, self.server_path + self.minecraft_server_file_name)
            print("Minecraft server downloaded.")
        else:
            print("Minecraft server already downloaded.")

# ============== Secrets File Management ==============

    def secrets_file_empty(self):
        if not self.secret_file_exists():
            raise FileNotFoundError(f"{self.secrets_path + self.secrets_file_name} does not exist.")

        with open(self.secrets_path + self.secrets_file_name, "r") as f:
            return len(f.read().strip()) == 0

    def secret_file_exists(self):
        return os.path.exists(self.secrets_path + self.secrets_file_name)

    def write_secrets_file(self, playit_secret=""):
        if not os.path.exists(self.secrets_path):
            os.makedirs(self.secrets_path)
        if playit_secret:
            data = {'playit-secret': playit_secret}
        else:
            data = {}
        with open(os.path.join(self.secrets_path, self.secrets_file_name), 'w') as f:
            toml.dump(data, f)

    def secrets_file_in_place(self):
        pass

# ============== Secrets File Management ==============

    def i_will_be_host_now(self):
        pass

    def delete_files_inside_server_folder(self):
        pass

    def observer_is_triggered_and_server_is_not_running(self):
        pass

    def close_all_threads(self):
        pass

    def there_are_active_tunnels(self):
        pass

    class FatalError(Exception):
        pass
