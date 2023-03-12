from enum import Flag
from .playitCliManager import PlayitCliManager
from .syncthingManager import SyncthingManager
from .commonConfigFileManager import CommonConfigFileManager
import time
import os
import distro
import platform
import requests
import toml
from notifypy import Notify
import subprocess
import atexit
import signal
import speedtest
import psutil
import random
import string

class Web3MCserverLogic:
    # Define the directory path
    secrets_path = "./../secrets/"
    secret_addresses_file_name = "secret_addresses.toml"
    secret_syncthing_playitcli = "secret_syncthing_playitcli.txt"
    secret_main_playitcli = "secret_main_playitcli.txt"
    server_path = "./../sync/server/"
    minecraft_server_file_name = "server.jar"
    minecraft_server_url = "https://piston-data.mojang.com/v1/objects/c9df48efed58511cdd0213c56b9013a7b5c9ac1f/server.jar"
    playitcli_toml_config_syncthing_server = "./playit-cli_config/syncthing_server_config.toml"
    playitcli_toml_config_syncthing_server2 = "./../playit-cli_config/syncthing_server_config.toml"
    syncthing_config = "./../syncthing_config"

    def __init__(self):

        # needs to be inside to not share data between instances of class
        self.bin_path = str() # for example ./bin/linux
        self.common_config_file_manager = CommonConfigFileManager(self)
        self.syncthing_manager = SyncthingManager(self)
        self.playitcli_manager = PlayitCliManager(self)

        self.syncthing_process = None # needs to be a list so it is a muttable object
        self.local_syncthing_address = None

        self.server_folder_path = os.path.abspath("./sync/server/")
        self.playitcli_toml_config_main_server = os.path.abspath("./playit-cli_config/main_server_config.toml")
        self.sync_folder_path = os.path.abspath("./sync/")
        self.common_config_file_path = os.path.abspath("./sync/common_conf.toml")
        #print(f"[DEBUG] {self.playitcli_toml_config_main_server}")


        # ======= Figuring out witch platform I'm running on ======= #
        base_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(base_path)
        system = platform.system()
        if system == 'Windows':
            self.bin_path = os.path.join(base_path, '..', 'bin', 'windows')
        elif system == 'Linux':
            self.bin_path = os.path.join(base_path, '..', 'bin', 'linux')
        else:
            print(f"Unsupported system: {system}")
            return
        # ======= ========================================== ======= #

        print("BIN PATH" + self.bin_path)

    def create_directories_from_path(self, path):
        # Split the path into its component directories
        directories = os.path.split(path)
        # Iterate over the directories and check/create each one
        for i in range(len(directories)):
            directory = os.path.join(*directories[:i+1])
            if not os.path.exists(directory):
                os.mkdir(directory)

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

    def file_has_field(self, file, field):
        # Load the TOML file into a dictionary
        with open(file, 'r') as f:
            secrets = toml.load(f)

        # Check if the "syncthing_server_command" field is present in the dictionary
        if field in secrets:
            return True
        else:
            return False

    def shutting_down_now(self):
        print ('[DEBUG] Terminating...')
        self.common_config_file_manager.update_common_config_file(recalculate_server_run_priority = False, Is_Host = False)

        # killing remaining processes
        if self.file_has_field(file = os.path.join(self.secrets_path, self.secret_addresses_file_name), field = "syncthing_server_command"):
            if self.syncthing_manager.syncthing_active(self.local_syncthing_address):
                print("[DEBUG] waiting to finish sync")
                self.syncthing_manager.wait_for_sync_to_finish()
                print("[DEBUG] Killing syncthing")
                self.syncthing_manager.terminate_syncthing(self.local_syncthing_address, self.syncthing_process)
        else:
            print("Syncthing server address doesn't exist yet!")

    def i_will_be_host_now(self, save_main_erver_address_in_secrets = False):
        # Send system notification saying that thes PC will be host now
        print("Becoming Host")

        self.syncthing_manager.wait_for_sync_to_finish() # todo, check https://man.archlinux.org/man/community/syncthing/syncthing-rest-api.7.en

        # Send desktop notification
        notification = Notify()
        notification.title = "This computer will be host for the Minecraft server now"
        try:
            server_address = self.get_main_server_address()
        except Exception:
            server_address = "/First time running, please check secrets/secret_addresses.toml/"
        notification.message = f"server address: {server_address}"
        notification.send()

        # Start the server
        address_added = False # Make it save the address

        for path in self.execute([self.bin_path + "/playit-cli", 
            "launch", 
            self.playitcli_toml_config_main_server],
            cwd=self.server_folder_path):

            if save_main_erver_address_in_secrets:
                if not address_added:
                    address_added = True
                    tunnels_list = self.get_existing_tunnels(self.get_secrets_playitcli_file(self.secret_main_playitcli))
                    print(f"[DEBUG] Tunnels_list: {tunnels_list}")
                    port_of_first_tunnel = tunnels_list.split()[4]
                    address_of_first_tunnel = tunnels_list.split()[3]
                    print(f"[DEBUG] You can access the minecraft server with: http://{address_of_first_tunnel} or if that doesn't work: http://{address_of_first_tunnel}:{port_of_first_tunnel}")
                    self.write_secret_addresses_toml_file(main_server_address=f"{address_of_first_tunnel}:{port_of_first_tunnel}")
            print(path, end="")

    def get_existing_tunnels(self, secret_to_use):
        tunnels_list = subprocess.check_output([self.bin_path + "/playit-cli", 
            "--secret", 
            secret_to_use,
            "tunnels", 
            "list"])
        return tunnels_list.decode().strip()

    def execute(self, cmd, cwd = ""):
        # https://stackoverflow.com/questions/4417546/constantly-print-subprocess-output-while-process-is-running
        print(f"[DEBUG] CWD: {cwd}")
        print("cmd")
        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=cwd, universal_newlines=True)
        print(F"[DEBUG] PID: {popen.pid}")
        self.syncthing_process = popen

        for stdout_line in iter(popen.stdout.readline, ""):
            if "Error: Broken pipe" in stdout_line:
                popen.stdout.close()    
                return_code = popen.wait()
                if return_code:
                    raise subprocess.CalledProcessError(return_code, cmd)
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

            try:
                resp = requests.get(self.minecraft_server_url).content
                with open(self.server_path + self.minecraft_server_file_name, "wb") as f:
                    f.write(resp)
                print("image is saved")
            except Exception as e:
                raise e

            
        else:
            print("Minecraft server already downloaded.")

# ============== Secrets File Management ==============

    def file_empty(self, file_path_to_check):
        if not self.file_exists(file_path_to_check):
            return True

        with open(file_path_to_check, "r") as f:
            return len(f.read().strip()) == 0

    def file_exists(self, file_path_to_check):
        return os.path.exists(file_path_to_check)

    def write_secret_addresses_toml_file(self, syncthing_address="", main_server_address=""):
        if not os.path.exists(self.secrets_path):
            os.makedirs(self.secrets_path)

        data = {}
        if os.path.isfile(os.path.join(self.secrets_path, self.secret_addresses_file_name)):
            with open(os.path.join(self.secrets_path, self.secret_addresses_file_name), 'r') as f:
                data = toml.load(f)

        if syncthing_address:
            data['syncthing_server_address'] = syncthing_address

        if main_server_address:
            data['main_server_address'] = main_server_address

        with open(os.path.join(self.secrets_path, self.secret_addresses_file_name), 'w') as f:
            toml.dump(data, f)


    def get_main_server_address(self):
        # Read the secrets file
        with open(os.path.join(self.secrets_path, self.secret_addresses_file_name), 'r') as f:
            secrets_data = toml.load(f)

        # Check if main server address exists in secrets file
        if 'main_server_address' in secrets_data:
            return secrets_data['main_server_address']
        else:
            raise Exception('Main server address not found.')

    def get_syncthing_server_address(self):
        # Read the secrets file
        with open(os.path.join(self.secrets_path, self.secret_addresses_file_name), 'r') as f:
            secrets_data = toml.load(f)

        # Check if main server address exists in secrets file
        if 'syncthing_server_address' in secrets_data:
            return secrets_data['syncthing_server_address']
        else:
            raise Exception('Syncthing server address not found.')

    def write_secret_playitcli_file(self, syncthing_secret, playit_secret=""):
        if syncthing_secret:
            to_save = self.secret_syncthing_playitcli
        else:
            to_save = self.secret_main_playitcli

        if not os.path.exists(self.secrets_path):
            os.makedirs(self.secrets_path)

        if self.file_exists(os.path.join(self.secrets_path, to_save)):
            mode = 'w'  # override existing file
        else:
            mode = 'x'  # create new file

        with open(os.path.join(self.secrets_path, to_save), mode) as f:
            f.write(playit_secret)

    def get_secrets_playitcli_file(self, secret_file_to_check):
        if self.file_exists(os.path.join(self.secrets_path, secret_file_to_check)):
            with open(os.path.join(self.secrets_path, secret_file_to_check), 'r') as f:
                return f.read()
        else:
            return ""

    def update_playit_syncthing_config_command_from_secrets(self):
        
        secrets_file_path = os.path.join(self.secrets_path, self.secret_addresses_file_name)
        #if not self.file_exists(secrets_file_path):
        #    print(f"[INFO] {secrets_file_path} doesn't exist\ncreating...")
        #    self.write_secret_playitcli_file(syncthing_secret = True)
        
        if os.path.exists(secrets_file_path):
            with open(secrets_file_path, "r") as f:
                secrets = toml.load(f)
        else:
            secrets = {}
        

        server_command_field = "syncthing_server_command"
        server_command = secrets.get(server_command_field, "")
        
        playitcli_toml_config = self.playitcli_toml_config_syncthing_server2
        

        # Generate a random string of 20 characters
        api_key = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(20))
        # Use the random string as the API key in the default command
        if platform.system() == 'Windows':
            default_command = f"./bin/windows/syncthing/syncthing.exe --home ./syncthing_config --gui-apikey={api_key} --no-default-folder --no-browser --gui-address=0.0.0.0:23840"
        else:
            default_command = f"./bin/linux/syncthing/syncthing --home ./syncthing_config --gui-apikey={api_key} --no-default-folder --no-browser --gui-address=0.0.0.0:23840"

        # there was no command there, we need to create a new key
        if not server_command:
            server_command = default_command
            secrets[server_command_field] = default_command
            with open(secrets_file_path, "w") as f:
                toml.dump(secrets, f)
        else:
            if server_command.split()[0] != default_command.split()[0]: # you're in windows running this script that's set for linux?
                server_command_words = server_command.split()
                server_command = f"{default_command.split()[0]} {' '.join(server_command_words[1:])}"
                secrets[server_command_field] = server_command
                with open(secrets_file_path, "w") as f:
                    toml.dump(secrets, f)


        # Extract the port number from the --gui-address argument
        gui_address_arg = [arg for arg in server_command.split() if arg.startswith("--gui-address=")]
        if gui_address_arg:
            port_number = gui_address_arg[0].split(":")[-1]
            # Update the local field of the first tunnel in the playitcli_toml_config file
            playitcli_toml_config = self.playitcli_toml_config_syncthing_server2
            with open(playitcli_toml_config, "r") as f:
                playitcli_config = toml.load(f)
            if "tunnels" in playitcli_config:
                playitcli_config["tunnels"][0]["local"] = int(port_number)
            with open(playitcli_toml_config, "w") as f:
                toml.dump(playitcli_config, f)
        
        command_parts = server_command.split()
        command = command_parts[0]
        command_args = command_parts[1:]
        
        if not os.path.isfile(playitcli_toml_config):
            raise FileNotFoundError(f"PlayIt CLI TOML config file not found: {playitcli_toml_config}")
        
        with open(playitcli_toml_config, "r") as f:
            playitcli_config = toml.load(f)
        
        playitcli_config["command"] = command
        
        if "command_args" in playitcli_config:
            playitcli_config["command_args"].clear()
        else:
            playitcli_config["command_args"] = []
        
        playitcli_config["command_args"].extend(command_args)
        
        with open(playitcli_toml_config, "w") as f:
            toml.dump(playitcli_config, f)

        return command_parts

# ============== Secrets File Management ==============

    def test_machine(self):
        print("[DEBUG] Calculating Machine performance...")
        try:
            # Get internet speed score
            st = speedtest.Speedtest()
            download_speed = st.download() / 10**6  # convert to Mbps
            upload_speed = st.upload() / 10**6  # convert to Mbps
            internet_score = ((download_speed + upload_speed) / 2) / 100 * 75
        except speedtest.SpeedtestException:
            internet_score = 0
            print("[WARNING] Unable to measure internet speed")
            
        try:
            # Get hardware score
            cpu_usage = psutil.cpu_percent()
            ram_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/').percent
            hardware_score = (100 - cpu_usage - ram_usage - disk_usage) / 100 * 25
        except Exception as e:
            hardware_score = 0
            print(f"[WARNING] Unable to measure hardware performance: {e}")
            
        # Calculate total score with 75% weight for internet score and 25% weight for hardware score
        total_score = internet_score * 0.55 + hardware_score * 0.45
        
        # Ensure score is between 0 and 100
        total_score = max(0, min(total_score, 100))
        
        print(f"[DEBUG] Performance given: {total_score}")
        return total_score

    def delete_files_inside_server_folder(self):
        if os.path.exists(self.server_path):
            try:
                for root, dirs, files in os.walk(self.server_path, topdown=False):
                    for file in files:
                        if not file.startswith('.'):
                            os.remove(os.path.join(root, file))
                    for dir in dirs:
                        if not dir.startswith('.'):
                            os.rmdir(os.path.join(root, dir))
            except Exception as e:
                print(f"Failed to delete. Reason: {e}")
        else:
            print(f"[DEBUG] {self.server_path} does not exist")

    def observer_is_triggered_and_server_is_not_running(self):
        pass

    def there_are_active_tunnels(self):
        pass

    class FatalError(Exception):
        pass
