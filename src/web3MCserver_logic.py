from .playitCliManager import PlayitCliManager
from .syncthingManager import SyncthingManager
from .commonConfigFileManager import CommonConfigFileManager
import time
import os
import distro
import platform
import urllib.request
import toml
from notifypy import Notify
import subprocess
import atexit
import signal

class Web3MCserverLogic:
    # Define the directory path
    secrets_path = "./../secrets/"
    secrets_file_name = "secret_addresses.toml"
    secret_playitcli = "secret_syncthing_playitcli.txt"
    server_path = "./../server/"
    minecraft_server_file_name = "server.jar"
    minecraft_server_url = "https://piston-data.mojang.com/v1/objects/c9df48efed58511cdd0213c56b9013a7b5c9ac1f/server.jar"
    playitcli_toml_config_main_server = "./../playit-cli_config/main_server_config.toml"
    playitcli_toml_config_syncthing_server = "./playit-cli_config/syncthing_server_config.toml"
    syncthing_config = "./../syncthing_config"

    def __init__(self):

        # needs to be inside to not share data between instances of class
        self.bin_path = str() # for example ./bin/nixos
        self.common_config_file_manager = CommonConfigFileManager(self)
        self.syncthing_manager = SyncthingManager(self)
        self.playitcli_manager = PlayitCliManager(self)

        self.syncthing_process = None # needs to be a list so it is a muttable object

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

    def set_exit_function(self):
        atexit.register(self.shutting_down_now)

    def shutting_down_now(self):
        print ('[DEBUG] Terminating...')
        self.common_config_file_manager.update_common_config_file(shutting_down = True)
        self.syncthing_manager.wait_for_sync_to_finish()

        # Kill all related processes
        if self.syncthing_process != None:
            print("[DEBUG] Killing syncthing")
            # https://stackoverflow.com/questions/4789837/how-to-terminate-a-python-subprocess-launched-with-shell-true/4791612#4791612
            print(self.syncthing_process)
            os.killpg(os.getpgid(self.syncthing_process), signal.SIGTERM)

    def i_will_be_host_now(self, save_main_erver_address_in_secrets = False):
        # Send system notification saying that thes PC will be host now
        print("Becoming Host")
        self.common_config_file_manager.check_periodically_for_online_peers_and_updates_common_sync_file_in_separate_thread() # todo
        self.syncthing_manager.wait_for_sync_to_finish() # todo, check https://man.archlinux.org/man/community/syncthing/syncthing-rest-api.7.en
        self.common_config_file_manager.update_common_config_file_to_say_that_im_new_host() # todo

        # Send desktop notification
        notification = Notify()
        notification.title = "This computer will be host for the Minecraft server now"
        notification.message = "server address: "
        notification.send()

        self.playitcli_manager.launch_minecraft_playitcli_server_on_separate_thread()

        if save_main_erver_address_in_secrets:
            pass

    def execute(self, cmd, cwd = ""):
        # https://stackoverflow.com/questions/4417546/constantly-print-subprocess-output-while-process-is-running
        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=cwd, universal_newlines=True)
        print(F"[DEBUG] PID: {popen.pid}")
        self.syncthing_process = popen.pid
        for stdout_line in iter(popen.stdout.readline, ""):
            yield stdout_line 
        popen.stdout.close()    
        return_code = popen.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, cmd)

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
            raise FileNotFoundError(f"{self.secrets_path + self.secret_playitcli} does not exist.")

        with open(self.secrets_path + self.secret_playitcli, "r") as f:
            return len(f.read().strip()) == 0

    def secret_file_exists(self):
        return os.path.exists(self.secrets_path + self.secret_playitcli)

    def write_secret_addresses_toml_file(self, syncthing_address="", main_server_address=""):
        if not os.path.exists(self.secrets_path):
            os.makedirs(self.secrets_path)
        data = {}
        if syncthing_address:
            data['syncthing_server_address'] = syncthing_address
        if main_server_address:
            data['main_server_address'] = main_server_address
        with open(os.path.join(self.secrets_path, self.secrets_file_name), 'w') as f:
            toml.dump(data, f)

    def write_secret_playitcli_file(self, playit_secret=""):
        if not os.path.exists(self.secrets_path):
            os.makedirs(self.secrets_path)

        if self.secret_file_exists():
            mode = 'w'  # override existing file
        else:
            mode = 'x'  # create new file

        with open(os.path.join(self.secrets_path, self.secret_playitcli), mode) as f:
            f.write(playit_secret)

    def get_secrets_playitcli_file(self):
        if self.secret_file_exists():
            with open(os.path.join(self.secrets_path, self.secret_playitcli), 'r') as f:
                return f.read()
        else:
            return ""

    def secrets_file_in_place(self):
        pass

# ============== Secrets File Management ==============

    def delete_files_inside_server_folder(self):
        pass

    def observer_is_triggered_and_server_is_not_running(self):
        pass

    def there_are_active_tunnels(self):
        pass

    class FatalError(Exception):
        pass
