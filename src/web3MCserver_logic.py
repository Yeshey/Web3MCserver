from asyncio import Lock
from datetime import datetime, timedelta
from enum import Flag
from multiprocessing import RLock
import multiprocessing
import threading
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
from mcstatus import MinecraftServer
import socket

class Web3MCserverLogic:
    # Define the directory path
    secrets_path = "./../secrets/"
    secret_addresses_file_name = "secret_addresses.toml"
    secret_syncthing_playitcli = "secret_syncthing_playitcli.txt"
    secret_main_playitcli = "secret_main_playitcli.txt"
    server_path = "./../sync/server/"
    minecraft_server_file_name = "server.jar"
    minecraft_server_url = "https://piston-data.mojang.com/v1/objects/8f3112a1049751cc472ec13e397eade5336ca7ae/server.jar"
    playitcli_toml_config_syncthing_server = "./sync/playit-cli_config/syncthing_server_config.toml"
    playitcli_toml_config_syncthing_server2 = "./../sync/playit-cli_config/syncthing_server_config.toml"
    syncthing_config = "./../syncthing_config"

    def __init__(self):

        # needs to be inside to not share data between instances of class
        self.bin_path = str() # for example ./bin/linux
        self.common_config_file_manager = CommonConfigFileManager(self)
        self.syncthing_manager = SyncthingManager(self)
        self.playitcli_manager = PlayitCliManager(self)

        self.syncthing_process = None # needs to be a list so it is a muttable object
        self.mc_process = None
        self.isHost = False
        self.checkDevicesThreadRunning = False
        self.going_to_restart = None
        self.lastServerHostChange = None
        self.youShouldStopBeingHost = False
        self.iAmAFakeHost = False

        self.server_folder_path = os.path.abspath("./sync/server/")
        self.playitcli_toml_config_main_server = os.path.abspath("./sync/playit-cli_config/main_server_config.toml")
        self.playitcli_toml_config_syncthing_server = os.path.abspath("./sync/playit-cli_config/syncthing_server_config.toml")
        self.sync_folder_path = os.path.abspath("./sync/")
        self.common_config_file_path = os.path.abspath("./sync/common_conf.toml")
        self.root = os.path.abspath("./")
        #print(f"[DEBUG] {self.playitcli_toml_config_main_server}")

        self.my_lock_terminating = threading.Lock()
        with self.my_lock_terminating:
            self.terminating = False
        self.my_lock_peerDisconnected = threading.Lock()
        with self.my_lock_peerDisconnected:
            self.peerDisconnected = None
        self.my_lock_local_syncthing_address = threading.Lock()
        with self.my_lock_local_syncthing_address:
            self.local_syncthing_address = None
        self.my_lock_notDoingStuff = threading.Lock()
        with self.my_lock_notDoingStuff:
            self.notDoingStuff = False

        self.event_peerDisconnected = threading.Event()    

        # ======= Figuring out witch platform I'm running on ======= #
        base_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(base_path)
        system = platform.system()
        if system == 'Windows':
            self.bin_path = os.path.join(base_path, '..', 'bin', 'windows')
            self.syncthing_path = os.path.abspath(os.path.join(self.root, 'bin', 'windows', 'syncthing', 'syncthing.exe'))
        elif system == 'Linux':
            self.bin_path = os.path.join(base_path, '..', 'bin', 'linux')
            self.syncthing_path = os.path.abspath(os.path.join(self.root, 'bin', 'linux', 'syncthing', 'syncthing'))
        else:
            print(f"Unsupported system: {system}")
            return
        # ======= ========================================== ======= #

        print("BIN PATH" + self.bin_path)

    def _30_minutes_passed(self, last_time):
        current_time = datetime.now()
        time_difference = current_time - last_time
        return time_difference >= timedelta(minutes=30)

    def create_directories_from_path(self, path):
        # Split the path into its component directories
        directories = os.path.split(path)
        # Iterate over the directories and check/create each one
        for i in range(len(directories)):
            directory = os.path.join(*directories[:i+1])
            if not os.path.exists(directory):
                os.mkdir(directory)

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
        with self.my_lock_terminating:
            self.terminating = True
        print ('[DEBUG] Terminating...')
        self.isHost = False
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

    def run_minecraft(self, command, cwd):
        print("[Debug] Killing Minecraft")
        self.terminate_minecraft()
        address_added = False # Make it save the address

        for path in self.execute_mc(command,
                        cwd=cwd):
            print(path, end="")
            if not address_added:
                address_added = True
                tunnels_list = self.get_existing_tunnels(self.get_secrets_playitcli_file(self.secret_main_playitcli))
                print(f"[DEBUG] Tunnels_list: {tunnels_list}")
                port_of_first_tunnel = tunnels_list.split()[4]
                address_of_first_tunnel = tunnels_list.split()[3]
                print(f"[DEBUG] You can access the minecraft server with: http://{address_of_first_tunnel} or if that doesn't work: http://{address_of_first_tunnel}:{port_of_first_tunnel}")
                self.write_secret_addresses_toml_file(main_server_address=f"{address_of_first_tunnel}:{port_of_first_tunnel}")

    def i_will_be_host_now(self):
        # Send system notification saying that thes PC will be host now
        print("\n[DEBUG] Becoming Host\n")
        self.lastServerHostChange = datetime.now()
        self.isHost = True

        # Send desktop notification
        notification = Notify()
        notification.title = "This computer will be host for the Minecraft server now"
        try:
            server_address = self.get_main_server_address()
        except KeyboardInterrupt:
            # handle KeyboardInterrupt separately
            print("KeyboardInterrupt caught")
            raise KeyboardInterrupt
        except Exception as e:
            print(f"[DEBUG] Exception: {e}")
            server_address = "--First time running, please check /secrets/secret_addresses.toml--"
        notification.message = f"server address: {server_address}"
        notification.send()

        # tmp trying another way
        t = threading.Thread(target=self.run_minecraft, args=([self.bin_path + "/playit-cli", 
            "launch", 
            self.playitcli_toml_config_main_server], 
            self.server_folder_path))
        t.start()
        
        while True: # wait for it to save the stuff in the file
            try:
                _ = self.get_main_server_address()
                break
            except KeyboardInterrupt:
                # handle KeyboardInterrupt separately
                print("KeyboardInterrupt caught")
                raise KeyboardInterrupt
            except Exception as e:
                print(f"[DEBUG] Exception caught: {e}")
                time.sleep(1)

        self.observer_of_common_conf_file(iAmHost = True)

        '''# Start the server
        address_added = False # Make it save the address

        for path in self.execute([self.bin_path + "/playit-cli", 
            "launch", 
            self.playitcli_toml_config_main_server],
            cwd=self.server_folder_path):

            if not address_added:
                address_added = True
                tunnels_list = self.get_existing_tunnels(self.get_secrets_playitcli_file(self.secret_main_playitcli))
                print(f"[DEBUG] Tunnels_list: {tunnels_list}")
                port_of_first_tunnel = tunnels_list.split()[4]
                address_of_first_tunnel = tunnels_list.split()[3]
                print(f"[DEBUG] You can access the minecraft server with: http://{address_of_first_tunnel} or if that doesn't work: http://{address_of_first_tunnel}:{port_of_first_tunnel}")
                self.write_secret_addresses_toml_file(main_server_address=f"{address_of_first_tunnel}:{port_of_first_tunnel}")
            print(path, end="")'''

    def kill_process_by_command(self, command, command_args):
        # Get process information for all running processes
        for proc in psutil.process_iter(attrs=['name', 'cmdline']):
            try:
                # Check if process name and command-line arguments match
                #if proc is None: # this is needed in Windows
                #    proc = []
                if proc.info['name'] in command and proc.info['cmdline'] is not None and all(arg in proc.info['cmdline'] for arg in command_args):
                    print(proc.info['name'])
                    # Kill the process
                    proc.kill()
                    print(f"Process {proc.pid} ({command} {' '.join(command_args)}) has been terminated.")
            except KeyboardInterrupt:
                # handle KeyboardInterrupt separately
                print("KeyboardInterrupt caught")
                raise KeyboardInterrupt
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Process has already terminated or we don't have permission to kill it
                print("[DEBUG] Couldn't kill, or, wasn't found")
    
    def kill_playitcli_server(self, playitconfig):
        # Read the TOML config file
        with open(playitconfig, "r") as f:
            config = toml.load(f)
        
        # Extract command and command_args from the config file
        command = config.get("command")
        command_args = config.get("command_args", [])
        print(command)
        print(command_args)
        
        # Kill the process with the matching command and command_args
        self.kill_process_by_command(command, command_args)


    def terminate_minecraft(self):
        
        self.kill_playitcli_server(self.playitcli_toml_config_main_server)

        try:
            if self.mc_process != None:
                print(f"mc process pid: {self.mc_process.pid}")
                print(f"python script pid: {os.getpid()}")
                if os.getpid() != self.mc_process.pid:
                    os.kill(self.mc_process.pid, signal.SIGKILL)
                    print("Trying to kill")
                else:
                    print("Pid of minecraft and Pid of this python script are the same, not killing!")
                self.mc_process.terminate() # doesn't seem to do anything?
                self.mc_process.kill() # doesn't seem to do anything?
        except KeyboardInterrupt:
            # handle KeyboardInterrupt separately
            print("KeyboardInterrupt caught")
            raise KeyboardInterrupt
        except Exception as e:
            print(f"[DEBUG] Exception caught: {e}, Minecraft doesn't seem to be running")

        '''command_parts = self.update_playit_syncthing_config_command_from_secrets()
        print(f"[DEBUG] command parts: {command_parts}")
        for proc in psutil.process_iter():
            try:
                cmd = proc.cmdline()
                if 'java' in cmd and all(part in cmd for part in command_parts):
                    proc.kill()
                    print('Process killed')
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                print(f"[DEBUG] Exception on killing minecraft")'''

        self.mc_process = None

    def get_existing_tunnels(self, secret_to_use):
        tunnels_list = subprocess.check_output([self.bin_path + "/playit-cli", 
            "--secret", 
            secret_to_use,
            "tunnels", 
            "list"])
        return tunnels_list.decode().strip()

    def execute(self, cmd, cwd = ""):
        # https://stackoverflow.com/questions/4417546/constantly-print-subprocess-output-while-process-is-running
        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=cwd, universal_newlines=True)
        print(F"[DEBUG] Syncthing PID: {popen.pid}")
        self.syncthing_process = popen

        for stdout_line in iter(popen.stdout.readline, ""):
            yield stdout_line 
        popen.stdout.close()
        return_code = popen.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, cmd)

    def execute_mc(self, cmd, cwd = ""):
        # https://stackoverflow.com/questions/4417546/constantly-print-subprocess-output-while-process-is-running
        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=cwd, universal_newlines=True)
        print(F"[DEBUG] Minecraft PID: {popen.pid}")
        self.mc_process = popen

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
            try:
                resp = requests.get(self.minecraft_server_url, timeout=60).content
                with open(self.server_path + self.minecraft_server_file_name, "wb") as f:
                    f.write(resp)
                print("[DEBUG] server.jar is saved")
            except KeyboardInterrupt:
                # handle KeyboardInterrupt separately
                print("KeyboardInterrupt caught")
                raise KeyboardInterrupt
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
            default_command = fr"{self.syncthing_path} --home ./syncthing_config --gui-apikey={api_key} --no-default-folder --no-browser --gui-address=0.0.0.0:23840"
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
            #f.write(toml.dumps(playitcli_config).replace('\\\\', '\\'))

        return command_parts

# ============== Secrets File Management ==============

    def auto_accept_devices_syncthing(self):
        t = threading.Thread(target=self.syncthing_manager.check_devices)
        t.daemon = True # so this thread ends automatically when main thread ends
        t.start()

    def test_machine(self): # todo, if device is on battery, then it should do from -100 to 0 instead
        print("[DEBUG] Calculating Machine performance...")

        try:
            is_power_plugged = psutil.sensors_battery().power_plugged
        except KeyboardInterrupt:
            # handle KeyboardInterrupt separately
            print("KeyboardInterrupt caught")
            raise KeyboardInterrupt
        except Exception as e:
            print(f"[DEBUG] Exception caught: {e}, couldn't get battery information, assuming on battery")
            is_power_plugged = False # if can't get the information, assume its on battery

        print(f"[DEBUG] Power Plugged: {is_power_plugged}")

        try:
            # Get internet speed score
            st = speedtest.Speedtest()
            download_speed = st.download() / 10**6  # convert to Mbps
            upload_speed = st.upload() / 10**6  # convert to Mbps
            internet_score = ((download_speed + upload_speed) / 2) / 100 * 75
        except KeyboardInterrupt:
            # handle KeyboardInterrupt separately
            print("KeyboardInterrupt caught")
            raise KeyboardInterrupt
        except speedtest.SpeedtestException:
            internet_score = 0
            print("[WARNING] Unable to measure internet speed")
            
        try:
            # Get hardware score
            cpu_usage = psutil.cpu_percent()
            ram_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/').percent
            hardware_score = (100 - cpu_usage - ram_usage - disk_usage) / 100 * 25
        except KeyboardInterrupt:
            # handle KeyboardInterrupt separately
            print("KeyboardInterrupt caught")
            raise KeyboardInterrupt
        except Exception as e:
            hardware_score = 0
            print(f"[WARNING] Unable to measure hardware performance: {e}")
            
        # Calculate total score with 75% weight for internet score and 25% weight for hardware score
        total_score = internet_score * 0.55 + hardware_score * 0.45
        
        # Ensure score is between 0 and 100
        total_score = max(0, min(total_score, 100))

        if is_power_plugged == False: #  loose 100 points if it is not plugged in
            total_score -= 100
        
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
            except KeyboardInterrupt:
                # handle KeyboardInterrupt separately
                print("KeyboardInterrupt caught")
                raise KeyboardInterrupt
            except Exception as e:
                print(f"Failed to delete. Reason: {e}")
        else:
            print(f"[DEBUG] {self.server_path} does not exist")

    def is_mc_server_online(self, server_address):
        try:
            try:
                # Split the server address into its hostname and port
                host, port = server_address.split(":")
                # Create a MinecraftServer object
                server = MinecraftServer(host, int(port))
                # Call the status() method to get the server's status
                status = server.status()
                return True
            except KeyboardInterrupt:
                # handle KeyboardInterrupt separately
                print("KeyboardInterrupt caught")
                raise KeyboardInterrupt
            except (socket.timeout, ConnectionRefusedError):
                # If the server is not responding or refused the connection, return False
                return False
        except KeyboardInterrupt:
            # handle KeyboardInterrupt separately
            print("KeyboardInterrupt caught")
            raise KeyboardInterrupt
        except Exception as e:
            print(f"[DEBUG] Exception caught on is_mc_server_online: {e}")
            return False

    def observer_of_common_conf_file(self, iAmHost = False):
        while True:

            with self.my_lock_notDoingStuff:
                self.notDoingStuff = True
            self.event_peerDisconnected.wait()
            with self.my_lock_notDoingStuff:
                self.notDoingStuff = False
            self.event_peerDisconnected.clear()  # Reset event
            print("Continuing main thread execution...")

            id_that_disconnected = self.peerDisconnected
            self.peerDisconnected = None

            if not self.syncthing_manager.internet_on():
                print("[DEBUG] No internet!")
                continue

            if self.terminating:
                print("[DEBUG] Someone disconnected, but terminating, skipping")
                continue

            if self.syncthing_manager.wait_for_sync_to_finish() is False:
                print("[DEBUG] Someone disconnected, don't have a recent enough version of server and no peers online to get it. Not becoming host...")
                continue

            if self.iAmAFakeHost is True: # shame on me
                self.iAmAFakeHost = False
                print("[DEBUG] I am fake host? Confirming...")
                if iAmHost == True:
                    try:
                        if (
                                self.web3mcserver.syncthing_manager.get_remote_syncthing_ID() != self.web3mcserver.syncthing_manager.get_my_syncthing_ID()
                            ):
                            print("\n[DEBUG] I'm a fake host!!\n")
                            break
                        elif (self.web3mcserver.syncthing_manager.syncthing_active(remote_address, timeout=1)):
                            print("\n[DEBUG] I'm a fake host?? Syncthing server not online?\n")
                            break
                    except KeyboardInterrupt:
                        # handle KeyboardInterrupt separately
                        print("KeyboardInterrupt caught")
                        raise KeyboardInterrupt
                    except Exception as e:
                        print(f"\n[DEBUG] Exception caught: {e}, I'm a fake host?? Syncthing server not online? Relinquishing host status...\n")
                        break
                

            if self.going_to_restart is not None:
                if self.going_to_restart == id_that_disconnected:
                    self.going_to_restart = None
                    print("[DEBUG] giving it 90 seconds before checking again")
                    time.sleep(90)

            print("[DEBUG] Someone disconnected")
            field = "syncthing_server_command"
            if self.file_has_field(file = os.path.join(self.secrets_path, self.secret_addresses_file_name), field = field):
                remote_address = self.get_syncthing_server_address()

                sorted_priorities = self.common_config_file_manager.sorted_dic_of_ID_and_server_run_priority()
                my_order = self.common_config_file_manager.my_order_in_server_host_priority(sorted_priorities)
                
                if self.isHost == True and self.youShouldStopBeingHost == True: # in case it should give up being the host in favor of someone better
                    self.youShouldStopBeingHost = False
                    if self._30_minutes_passed(self.lastServerHostChange):
                        my_order = self.common_config_file_manager.my_order_in_server_host_priority(sorted_priorities)
                        if my_order != 0:
                            break

                remote_server_still_running = False
                for _ in range(2):
                    try:
                        if ( self.syncthing_manager.syncthing_active(remote_address, timeout=1) ):
                            for _ in range(2):
                                time.sleep(5)
                                if self.is_mc_server_online(self.get_main_server_address()):
                                    remote_server_still_running = True
                                    time.sleep(3) # give him time to shutdown in the other side
                                    print(f"[DEBUG] 1 - remote server still running: {remote_server_still_running}")
                                    break
                        else:
                            remote_server_still_running = False
                            print(f"[DEBUG] 3 - dremote server still running: {remote_server_still_running}")
                            break
                    except KeyboardInterrupt:
                        # handle KeyboardInterrupt separately
                        print("KeyboardInterrupt caught")
                        raise KeyboardInterrupt
                    except Exception as e:
                        print(f"[DEBUG] Exception caught: {e}")

                if not remote_server_still_running:
                    num_in_queue = my_order
                    interval_time = 100

                    if iAmHost == True:
                        print(f"[DEBUG] remote server not responding, but I am host. I'm doing an awful job!!")    

                    print(f"[DEBUG] my number in queue: {num_in_queue}")

                    if num_in_queue == 0:
                        print("[DEBUG] I should be host!!")
                        if iAmHost == True:
                            print("[DEBUG] I'm already host... restarting anyways")
                        break
                    elif iAmHost == True:
                        print("[DEBUG] Gonna become a normal observer then...")
                        break

                    self.going_to_restart = self.common_config_file_manager.machine_with_highest_priority(sorted_priorities)
                    
                    not_gonna_be_host = False
                    for _ in range(num_in_queue):
                        time.sleep(interval_time)
                        if self.syncthing_manager.syncthing_active(remote_address, timeout=3):
                            print("[DEBUG] server running already, oki")
                            not_gonna_be_host = True
                            break
                    if not_gonna_be_host:
                        continue

                    if self.terminating:
                        print("[DEBUG] someone disconnected, but terminating, skipping")
                        continue

                    break
                else:
                    print("[DEBUG] No new Host needed")
            else:
                raise Exception(f"Where is the field {field}?")
        print("[DEBUG] broke out of observer_of_common_conf_file")
        self.lastServerHostChange = datetime.now()
        