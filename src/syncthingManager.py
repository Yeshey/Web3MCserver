from email import header
import re
import signal
import webbrowser
import subprocess
import os
import toml
import requests
import threading
import time
import urllib.request

class SyncthingManager:
    def __init__(self, web3mcserver):
        self.web3mcserver = web3mcserver

    def run_syncthing(self, command, cwd):      
        print(f"[DEBUG] run syncthing, command: {command}, cwd: {cwd}")
        for path in self.web3mcserver.execute(command,
                        cwd=cwd):
            print(path, end="")
            if 'Access the GUI via the following URL:' in path:
                self.web3mcserver.local_syncthing_address = path.split()[-1]
            if 'shutting down' in path:
                break
            if "INFO: Connection to" in path and "closed:" in path:
                # extract the ID of the remote machine using string manipulation
                pattern = r'Connection to (\w+-\w+-\w+-\w+-\w+-\w+-\w+-\w+)'
                match = re.search(pattern, path)
                if match:
                    id = match.group(1)
                    with self.web3mcserver.my_lock_peerDisconnected:
                        self.web3mcserver.peerDisconnected = id
                        self.web3mcserver.event_peerDisconnected.set()
                    print(f"[DEBUG] Online peer disconnected, its ID: {id}")
                else:
                    raise Exception("ID not found in input string")



    def launch_syncthing_in_separate_thread(self, with_playitgg):

        # todo: to make it more secure you should add password and user. But it seems like you'd need to stop syncthing and run some commands and start again
        # https://docs.syncthing.net/users/faq.html#how-do-i-reset-the-gui-password

        # build toml playit config file for syncthing with the secrets syncthing command, create the syncthing secrets command if doesn't exist
        # also returns the command to run
        command = self.web3mcserver.update_playit_syncthing_config_command_from_secrets()

        if with_playitgg:
            print("[DEBUG] Starting Syncthing server in tunnel...")
            if self.web3mcserver.file_has_field(file = os.path.join(self.web3mcserver.secrets_path, self.web3mcserver.secret_addresses_file_name), field = "syncthing_server_command"):
                remote_address = self.web3mcserver.get_syncthing_server_address()
                if self.syncthing_active(remote_address, timeout=1) and self.get_remote_syncthing_ID() != self.get_my_syncthing_ID():
                    Exception("[WARNING] Shouldn't start while syncthing server is running!...")
            else:
                print("[DEBUG] Syncthing server address doesn't exist yet.")

            # tmp trying another way
            t = threading.Thread(target=self.run_syncthing, args=([self.web3mcserver.bin_path + "/playit-cli", 
                "launch", 
                self.web3mcserver.playitcli_toml_config_syncthing_server], 
                "./../"))
            t.start()

            while self.web3mcserver.local_syncthing_address == None:
                time.sleep(1) # give syncthing time to start (find a better way)
            
            tunnels_list = self.web3mcserver.get_existing_tunnels(self.web3mcserver.get_secrets_playitcli_file(self.web3mcserver.secret_syncthing_playitcli))
            port_of_first_tunnel = tunnels_list.split()[4]
            address_of_first_tunnel = tunnels_list.split()[3]

            syncthing_url = f"http://{address_of_first_tunnel}:{port_of_first_tunnel}"
            print(f"[DEBUG] You can access syncthing with: {syncthing_url}")
            #webbrowser.open(syncthing_url, new=0, autoraise=True)

            self.web3mcserver.write_secret_addresses_toml_file(syncthing_address="http://" + address_of_first_tunnel + ":" + port_of_first_tunnel)

        else:
            print("[DEBUG] Starting Syncthing locally...")
            # tmp trying another way
            t = threading.Thread(target=self.run_syncthing, args=(command, self.web3mcserver.root))
            t.start()
            #self.web3mcserver.local_syncthing_address = "http://127.0.0.1:23840/" # find better way for this too

            while self.web3mcserver.local_syncthing_address == None:
                time.sleep(1) # give syncthing time to start (find a better way)

        # Set default folder (to auto accept that folder)
        url = f'{self.web3mcserver.local_syncthing_address}rest/config/defaults/folder'
        headers = {'X-API-Key': self.get_api_key()}
        # folders synced with no conflicts allowed, and staggered versioning
        data = {
            "id": "sync", 
            "label": "sync", 
            "filesystemType": "basic", 
            "path": f"{self.web3mcserver.sync_folder_path}", 
            "type": "sendreceive",  
            "devices": [
            {
                "deviceID": self.get_my_syncthing_ID(),
                "introducedBy": "",
                "encryptionPassword": ""
            }
            ],
            "rescanIntervalS": 3600, 
            "minDiskFree": { 
                "value": 1, 
                "unit": "%" 
            }, 
            "versioning": { 
                "type": "staggered", 
                "params": { 
                    "maxAge": "1728000" 
                }, 
                "cleanupIntervalS": 3600, 
                "fsPath": "", 
                "fsType": "basic" 
            }, 
            "maxConflicts": 0, 
        }
        response = requests.put(url, headers=headers, json=data, timeout=60)
        print(f"[DEBUG] Set default folder: {response}")

        # Add the sync folder
        self.add_folders_to_sync()

    def check_devices(self):
        while True:
            time.sleep(100) # Check every 100 seconds

            # Check if there are syncthing peers that want to connect
            if self.web3mcserver.file_has_field(file = os.path.join(self.web3mcserver.secrets_path, self.web3mcserver.secret_addresses_file_name), field = "syncthing_server_command") and self.syncthing_active(self.web3mcserver.local_syncthing_address, timeout=3):
                url = f'{self.web3mcserver.local_syncthing_address}rest/cluster/pending/devices'
                headers = {'X-API-Key': self.get_api_key()}
                devices = {}
                try:
                    response = requests.get(url, headers=headers, timeout=60)
                    response.raise_for_status()
                    data = response.json()
                    if data != devices:
                        print("[DEBUG] New Device wants to connect!")
                        ID_of_peer_that_wants_to_connect = list(data.keys())[0]
                        self.connect_to_syncthing_peer(ID_of_peer_that_wants_to_connect)
                        self.add_folders_to_sync([ID_of_peer_that_wants_to_connect])
                except KeyboardInterrupt:
                    # handle KeyboardInterrupt separately
                    print("KeyboardInterrupt caught")
                    raise KeyboardInterrupt
                except requests.exceptions.RequestException as e:
                    print(f"Error: {e}")

            if self.web3mcserver.terminating == True:
                break

            if self.web3mcserver.notDoingStuff == True:

                if self.web3mcserver.isHost == True:
                    if self.web3mcserver._30_minutes_passed(self.web3mcserver.lastServerHostChange):
                        sorted_priorities = self.web3mcserver.common_config_file_manager.sorted_dic_of_ID_and_server_run_priority()
                        my_order = self.web3mcserver.common_config_file_manager.my_order_in_server_host_priority(sorted_priorities)
                        if my_order != 0:
                            self.youShouldStopBeingHost = True
                            self.web3mcserver.event_peerDisconnected.set() # let server go to someone better

                # am I the actual host?
                if self.web3mcserver.file_has_field(file = os.path.join(self.web3mcserver.secrets_path, self.web3mcserver.secret_addresses_file_name), field = "syncthing_server_command"):
                    remote_address = self.web3mcserver.get_syncthing_server_address()

                    if ( not self.syncthing_active(remote_address, timeout=1) ):
                        print("[DEBUG] server is not online!!!")
                        self.web3mcserver.event_peerDisconnected.set() 

                    if self.web3mcserver.isHost == True:
                        if (
                                self.web3mcserver.syncthing_manager.syncthing_active(remote_address, timeout=1) and 
                                self.web3mcserver.syncthing_manager.get_remote_syncthing_ID() != self.web3mcserver.syncthing_manager.get_my_syncthing_ID()
                            ):
                            print("\n[DEBUG] I'm a fake host!?\n")
                            self.web3mcserver.iAmAFakeHost = True
                            self.web3mcserver.event_peerDisconnected.set()
                else:
                    print("[DEBUG] Syncthing server address doesn't exist yet.")    



    def add_folders_to_sync(self, ids=[]):
    # The following works, and see this website (https://docs.syncthing.net/v1.22.1/rest/config.html)

        url = f'{self.web3mcserver.local_syncthing_address}rest/config/folders'
        headers = {'X-API-Key': self.get_api_key()}

        devices = [{"deviceID": self.get_my_syncthing_ID(), "introducedBy": "", "encryptionPassword": ""}]
        # Check if the devices section is already populated
        response = requests.get(url, headers=headers, timeout=60)
        if response.status_code == 200 and len(response.json()) > 0:
            existing_devices = response.json()[0]['devices']
            devices = existing_devices if existing_devices else devices
        for device_id in ids:
            devices.append({"deviceID": device_id, "introducedBy": "", "encryptionPassword": ""})

        # folders synced with no conflicts allowed, and staggered versioning
        data = [
            {
                "id": "sync",
                "label": "sync",
                "filesystemType": "basic",
                "path": f"{self.web3mcserver.sync_folder_path}",
                "type": "sendreceive",
                "devices": devices,
                "rescanIntervalS": 3600, 
                "minDiskFree": { 
                    "value": 1, 
                    "unit": "%" 
                }, 
                "versioning": { 
                    "type": "staggered", 
                    "params": { 
                        "maxAge": "1728000" 
                    }, 
                    "cleanupIntervalS": 3600, 
                    "fsPath": "", 
                    "fsType": "basic" 
                }, 
                "maxConflicts": 0, 
            }
        ]
        response = requests.put(url, headers=headers, json=data, timeout=60)
        print(f"[DEBUG] add_folders_to_sync: {response}")

    def get_my_syncthing_ID(self):
        try:
            syncthingDeviceID = subprocess.check_output([self.web3mcserver.syncthing_path, 
                "--home", 
                os.path.join(".","..","syncthing_config"),
                "-device-id" ])
            syncthingDeviceID = syncthingDeviceID.decode().strip()
        except KeyboardInterrupt:
            # handle KeyboardInterrupt separately
            print("KeyboardInterrupt caught")
            raise KeyboardInterrupt
        except Exception as e:
            print(f"Exception caught: {e}, Couldn't get Syncthing ID")
            return None
        return syncthingDeviceID

    def get_api_key(self):
        secrets_file_path = os.path.join(self.web3mcserver.secrets_path, self.web3mcserver.secret_addresses_file_name)
        if not os.path.isfile(secrets_file_path):
            raise FileNotFoundError(f"Common config file not found: {secrets_file_path}")

        with open(secrets_file_path, "r") as f:
            config = toml.load(f)

        syncthing_server_command = config.get("syncthing_server_command")
        if not syncthing_server_command:
            raise ValueError("syncthing_server_command not found in common config file.")

        api_key_arg = [arg for arg in syncthing_server_command.split() if arg.startswith("--gui-apikey=")]
        if not api_key_arg:
            raise ValueError("--gui-apikey argument not found in syncthing_server_command.")

        api_key = api_key_arg[0].split("=")[-1]
        return api_key

    def terminate_syncthing(self, syncthing_address, syncthing_process):

        self.web3mcserver.kill_playitcli_server(self.web3mcserver.playitcli_toml_config_syncthing_server)

        print("Trying old method of killing syncthing too")
        try:
            syncthingApiKey = self.get_api_key() # same key for everyone in the cluster
            headers = {"X-API-Key": syncthingApiKey}
            url = f"{syncthing_address}rest/system/shutdown"
            response = requests.post(url, headers=headers, timeout=60)
            print(f"[DEBUG] {response.text}")
        except KeyboardInterrupt:
            # handle KeyboardInterrupt separately
            print("KeyboardInterrupt caught")
            raise KeyboardInterrupt
        except Exception as e:
            try:
                print(f"[DEBUG] Exception: {e}")
                print(syncthing_process.pid)
                print(os.getpid())
                raise Exception("No pid?")
            except KeyboardInterrupt:
                # handle KeyboardInterrupt separately
                print("KeyboardInterrupt caught")
                raise KeyboardInterrupt
            except Exception as e:
                print(f"[DEBUG] Exception: {e}, Failed to kill syncthing, kill it manually. Address: {syncthing_address}")
                try:
                    syncthing_process.terminate() # doesn't seem to do anything?
                    syncthing_process.kill() # doesn't seem to do anything?
                except KeyboardInterrupt:
                    # handle KeyboardInterrupt separately
                    print("KeyboardInterrupt caught")
                    raise KeyboardInterrupt
                except Exception as e:
                    print(f"Exception: {e}, WTH, no syncthing at all, what are you trying to kill?")
        with self.web3mcserver.my_lock_local_syncthing_address:
            self.web3mcserver.local_syncthing_address = None
            self.web3mcserver.syncthing_process = None

    def get_remote_syncthing_ID(self):
        remoteSyncthingAddress = self.web3mcserver.get_syncthing_server_address()
        syncthingApiKey = self.get_api_key()
        headers = {"X-API-Key": syncthingApiKey}
        url = f"{remoteSyncthingAddress}/rest/system/status"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        response_json = response.json()
        my_id = response_json["myID"]
        return my_id
        
    def internet_on(self):
        try:
            urllib.request.urlopen("http://google.com") #Python 3.x
            return True
        except KeyboardInterrupt:
            # handle KeyboardInterrupt separately
            print("KeyboardInterrupt caught")
            raise KeyboardInterrupt
        except:
            try:
                urllib.request.urlopen("https://www.bing.com") #Python 3.x
                return True
            except KeyboardInterrupt:
                # handle KeyboardInterrupt separately
                print("KeyboardInterrupt caught")
                raise KeyboardInterrupt
            except:
                return False

    def syncthing_active(self, syncthing_address, timeout = 60):
        while not self.internet_on():
            print("[DEBUG] No internet!")
        secret = self.get_api_key() # Replace with your actual secret key
        headers = {'X-API-Key': secret}

        for i in range(3):
            try:
                response = requests.get(f"{syncthing_address}/rest/system/ping", headers=headers, timeout=timeout)
                if response.status_code == 200:
                    return True
            except KeyboardInterrupt:
                # handle KeyboardInterrupt separately
                print("KeyboardInterrupt caught")
                raise KeyboardInterrupt
            except requests.exceptions.RequestException:
                print(f"[DEBUG] no syncthing detected, trying {3-i} more")
            
            time.sleep(3)

        return False

    def connect_to_syncthing_peer(self, ID):

        url = f'{self.web3mcserver.local_syncthing_address}rest/config/devices'
        headers = {'X-API-Key': self.get_api_key()}

        # folders synced with no conflicts allowed, and staggered versioning
        data = {
            "deviceID": f"{ID}",
            #"name": "manjaro-LaptopBOYY",
            "introducer": True,
            "skipIntroductionRemovals": False,
            "introducedBy": "",
            "allowedNetworks": [],
            "autoAcceptFolders": False,
            "maxSendKbps": 0,
            "maxRecvKbps": 0,
            "ignoredFolders": []
        }
        response = requests.post(url, headers=headers, json=data, timeout=60)
        print(f"[DEBUG] connect_to_syncthing_peer: URL: {url}, HEADERS: {headers}, response: {response}")
        self.add_folders_to_sync([ID]) # so my folder shares itself with the new guy
        
        # make it share the folders witht his device
        
    def online_peers_list(self):
        url = f'{self.web3mcserver.local_syncthing_address}rest/system/connections'
        headers = {'X-API-Key': self.get_api_key()}
        response = requests.get(url, headers=headers, timeout=60)

        if response.status_code != 200:
            raise Exception(f'Failed to get connections: {response.content}')

        connections = response.json().get('connections', {})
        online_ids = [id for id, conn in connections.items() if conn.get('connected')]
        return online_ids

    '''
        Returns False if no peers online and don't have the minium required sync amount to continue being host
        Returns True otherwise
    '''
    def wait_for_sync_to_finish(self):
        if not self.syncthing_active(self.web3mcserver.local_syncthing_address, timeout=1):
            print("[DEBUG] Local syncthing not active, returning False for sync compleation")
            return
        urlScan = f'{self.web3mcserver.local_syncthing_address}rest/db/scan\?folder\=sync'
        url = f'{self.web3mcserver.local_syncthing_address}rest/db/completion'
        headers = {'X-API-Key': self.get_api_key()}

        response = requests.post(urlScan, headers=headers, timeout=60) # cause it to rescan
        print(f"[DEBUG] {response}")

        time_to_sleep = 3

        value = 99
        min_completion = 91
        while True: # make it not take forever... there might be no peers online
            response = requests.get(url, headers=headers, timeout=60)
            data = response.json()
            completion = data.get('completion')
            if not self.online_peers_list(): # list is empty
                print(f"[DEBUG] No online peers, unable to garantee most recent version")
                if completion < min_completion:
                    return False

            if completion >= value:
                print(f"[DEBUG] Sync compleation above {value}%, continuing...")
                break
            print(f"[DEBUG] Sync compleation below {value}%, checking for new peers every {time_to_sleep} seconds")
            if value > min_completion: # Don't let it advance if sync compleation isn't above 91%
                value -= 1
            time.sleep(time_to_sleep)
        return True
        print("[DEBUG] Sync compleate!")
