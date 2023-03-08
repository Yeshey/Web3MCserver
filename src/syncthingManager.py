from email import header
import signal
import webbrowser
import subprocess
import os
import toml
import requests

class SyncthingManager:
    def __init__(self, web3mcserverLogic):
        self.web3mcserverLogic = web3mcserverLogic

    def launch_syncthing_in_separate_thread(self, save_syncthing_server_address_in_secrets = False):
        print("Starting Syncthing server in tunnel...")

        # todo: to make it more secure you should add password and user. But it seems like you'd need to stop syncthing and run some commands and start again
        # https://docs.syncthing.net/users/faq.html#how-do-i-reset-the-gui-password
        
        # build toml playit config file for syncthing with the secrets syncthing command, create the syncthing secrets command if doesn't exist
        self.web3mcserverLogic.update_playit_config_command_from_secrets(to_update = "syncthing_server")

        for path in self.web3mcserverLogic.execute([self.web3mcserverLogic.bin_path + "/playit-cli", 
            "launch", 
            self.web3mcserverLogic.playitcli_toml_config_syncthing_server],
            cwd="./../"):
            print(path, end="")
            if 'Access the GUI via the following URL:' in path:
                self.web3mcserverLogic.local_syncthing_address = path.split()[-1]
            if 'INFO: My name is' in path: # allow it to continue when it sees this string in the output
                print("[DEBUG] Syncthing running, continuing...")
                break

        tunnels_list = self.web3mcserverLogic.get_existing_tunnels(self.web3mcserverLogic.get_secrets_playitcli_file(self.web3mcserverLogic.secret_syncthing_playitcli))
        port_of_first_tunnel = tunnels_list.split()[4]
        address_of_first_tunnel = tunnels_list.split()[3]

        syncthing_url = f"http://{address_of_first_tunnel}:{port_of_first_tunnel}"
        print(f"[DEBUG] You can access syncthing with: {syncthing_url}")
        webbrowser.open(syncthing_url, new=0, autoraise=True)

        if save_syncthing_server_address_in_secrets:
            self.web3mcserverLogic.write_secret_addresses_toml_file(syncthing_address="http://" + address_of_first_tunnel + ":" + port_of_first_tunnel)

        #subprocess.run([self.web3mcserverLogic.bin_path + "/syncthing/syncthing", "--home", self.web3mcserverLogic.syncthing_config])

    #def launch_syncthing(self):
    #    subprocess.run([self.web3mcserverLogic.bin_path + "/playit-cli", "launch", self.web3mcserverLogic.playitcli_toml_config_syncthing_server], cwd="./../")    

    def add_folders_to_sync(self):
    # The following works, and see this website (https://docs.syncthing.net/v1.22.1/rest/config.html)
        '''
        > curl -X PUT -H "X-API-Key: CRQeRBtNS1mQQg3B1WEa" -H "Content-Type: application/json" -d '[
            {
            "id": "my_folder",
            "path": "/path/to/my/folder",
            "type": "sendreceive",
            "devices": [
                {
                "deviceID": "QPC5HG7-AHK2PHJ-V7OPBG5-HPTVDVC-MDIY272-4UZ3NHG-BSTQEQG-K32YMAH",
                "introducer": true
                }
            ]
            }
        ]' http://127.0.0.1:23840/rest/config/folders
        '''

        # and this is the command you want:
        '''
curl -X PUT -H "X-API-Key: CRQeRBtNS1mQQg3B1WEa" -H "Content-Type: application/json" -d '[\
  {\
    "id": "common_config_file",\
    "label": "common_config_file",\
    "filesystemType": "basic",\
    "path": "/mnt/DataDisk/PersonalFiles/2023/Projects/Programming/Web3MCserver/common_config_file/",\
    "type": "sendreceive",\
    "devices": [\
      {\
        "deviceID": "3E23V4H-WL5NFEJ-XX3BLYY-ARUPG4Y-RHBC2MG-3V4QZFX-BMAGTCV-Y6MQCAU",\
        "introducedBy": "",\
        "encryptionPassword": ""\
      }\
    ],\
    "rescanIntervalS": 3600,\
    "fsWatcherEnabled": true,\
    "fsWatcherDelayS": 10,\
    "ignorePerms": false,\
    "autoNormalize": true,\
    "minDiskFree": {\
      "value": 1,\
      "unit": "%"\
    },\
    "versioning": {\
      "type": "staggered",\
      "params": {\
        "maxAge": "1728000"\
      },\
      "cleanupIntervalS": 3600,\
      "fsPath": "",\
      "fsType": "basic"\
    },\
    "copiers": 0,\
    "pullerMaxPendingKiB": 0,\
    "hashers": 0,\
    "order": "random",\
    "ignoreDelete": false,\
    "scanProgressIntervalS": 0,\
    "pullerPauseS": 0,\
    "maxConflicts": 10,\
    "disableSparseFiles": false,\
    "disableTempIndexes": false,\
    "paused": false,\
    "weakHashThresholdPct": 25,\
    "markerName": ".stfolder",\
    "copyOwnershipFromParent": false,\
    "modTimeWindowS": 0,\
    "maxConcurrentWrites": 2,\
    "disableFsync": false,\
    "blockPullOrder": "standard",\
    "copyRangeMethod": "standard",\
    "caseSensitiveFS": false,\
    "junctionsAsDirs": false,\
    "syncOwnership": false,\
    "sendOwnership": false,\
    "syncXattrs": false,\
    "sendXattrs": false,\
    "xattrFilter": {\
      "entries": [],\
      "maxSingleEntrySize": 1024,\
      "maxTotalSize": 4096\
    }\
  },\
  {\
    "id": "server",\
    "label": "server",\
    "filesystemType": "basic",\
    "path": "/mnt/DataDisk/PersonalFiles/2023/Projects/Programming/Web3MCserver/server/",\
    "type": "sendreceive",\
    "devices": [\
      {\
        "deviceID": "3E23V4H-WL5NFEJ-XX3BLYY-ARUPG4Y-RHBC2MG-3V4QZFX-BMAGTCV-Y6MQCAU",\
        "introducedBy": "",\
        "encryptionPassword": ""\
      }\
    ],\
    "rescanIntervalS": 3600,\
    "fsWatcherEnabled": true,\
    "fsWatcherDelayS": 10,\
    "ignorePerms": false,\
    "autoNormalize": true,\
    "minDiskFree": {\
      "value": 1,\
      "unit": "%"\
    },\
    "versioning": {\
      "type": "staggered",\
      "params": {\
        "maxAge": "1728000"\
      },\
      "cleanupIntervalS": 3600,\
      "fsPath": "",\
      "fsType": "basic"\
    },\
    "copiers": 0,\
    "pullerMaxPendingKiB": 0,\
    "hashers": 0,\
    "order": "random",\
    "ignoreDelete": false,\
    "scanProgressIntervalS": 0,\
    "pullerPauseS": 0,\
    "maxConflicts": 10,\
    "disableSparseFiles": false,\
    "disableTempIndexes": false,\
    "paused": false,\
    "weakHashThresholdPct": 25,\
    "markerName": ".stfolder",\
    "copyOwnershipFromParent": false,\
    "modTimeWindowS": 0,\
    "maxConcurrentWrites": 2,\
    "disableFsync": false,\
    "blockPullOrder": "standard",\
    "copyRangeMethod": "standard",\
    "caseSensitiveFS": false,\
    "junctionsAsDirs": false,\
    "syncOwnership": false,\
    "sendOwnership": false,\
    "syncXattrs": false,\
    "sendXattrs": false,\
    "xattrFilter": {\
      "entries": [],\
      "maxSingleEntrySize": 1024,\
      "maxTotalSize": 4096\
    }\
  }\
]' http://127.0.0.1:23840/rest/config/folders\
        '''

        url = f'{self.web3mcserverLogic.local_syncthing_address}rest/config/folders'
        headers = {'X-API-Key': self.get_api_key()}
        data = [
            {
                "id": "common_config_file",
                "label": "common_config_file",
                "filesystemType": "basic",
                "path": f"{self.web3mcserverLogic.bin_path}/../common_config_file/",
                "type": "sendreceive",
                "devices": [
                {
                    "deviceID": f"{self.get_my_syncthing_ID()}",
                    "introducedBy": "",
                    "encryptionPassword": ""
                }
                ],
                "rescanIntervalS": 3600,
                "fsWatcherEnabled": True,
                "fsWatcherDelayS": 10,
                "ignorePerms": False,
                "autoNormalize": True,
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
                "copiers": 0,
                "pullerMaxPendingKiB": 0,
                "hashers": 0,
                "order": "random",
                "ignoreDelete": False,
                "scanProgressIntervalS": 0,
                "pullerPauseS": 0,
                "maxConflicts": 0,
                "disableSparseFiles": False,
                "disableTempIndexes": False,
                "paused": False,
                "weakHashThresholdPct": 25,
                "markerName": ".stfolder",
                "copyOwnershipFromParent": False,
                "modTimeWindowS": 0,
                "maxConcurrentWrites": 2,
                "disableFsync": False,
                "blockPullOrder": "standard",
                "copyRangeMethod": "standard",
                "caseSensitiveFS": False,
                "junctionsAsDirs": False,
                "syncOwnership": False,
                "sendOwnership": False,
                "syncXattrs": False,
                "sendXattrs": False,
                "xattrFilter": {
                "entries": [],
                "maxSingleEntrySize": 1024,
                "maxTotalSize": 4096
                }
            },
            {
                "id": "server",
                "label": "server",
                "filesystemType": "basic",
                "path": f"{self.web3mcserverLogic.bin_path}/../server/",
                "type": "sendreceive",
                "devices": [
                {
                    "deviceID": f"{self.get_my_syncthing_ID()}",
                    "introducedBy": "",
                    "encryptionPassword": ""
                }
                ],
                "rescanIntervalS": 3600,
                "fsWatcherEnabled": True,
                "fsWatcherDelayS": 10,
                "ignorePerms": False,
                "autoNormalize": True,
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
                "copiers": 0,
                "pullerMaxPendingKiB": 0,
                "hashers": 0,
                "order": "random",
                "ignoreDelete": False,
                "scanProgressIntervalS": 0,
                "pullerPauseS": 0,
                "maxConflicts": 0,
                "disableSparseFiles": False,
                "disableTempIndexes": False,
                "paused": False,
                "weakHashThresholdPct": 25,
                "markerName": ".stfolder",
                "copyOwnershipFromParent": False,
                "modTimeWindowS": 0,
                "maxConcurrentWrites": 2,
                "disableFsync": False,
                "blockPullOrder": "standard",
                "copyRangeMethod": "standard",
                "caseSensitiveFS": False,
                "junctionsAsDirs": False,
                "syncOwnership": False,
                "sendOwnership": False,
                "syncXattrs": False,
                "sendXattrs": False,
                "xattrFilter": {
                "entries": [],
                "maxSingleEntrySize": 1024,
                "maxTotalSize": 4096
                }
            }
        ] 
        response = requests.post(url, headers=headers, json=data)
        print(response)

    def get_my_syncthing_ID(self):
        syncthingDeviceID = subprocess.check_output([self.web3mcserverLogic.bin_path + "/syncthing/syncthing", 
            "--home", 
            "./../syncthing_config",
            "-device-id" ])
        syncthingDeviceID = syncthingDeviceID.decode().strip()
        if 'Error' in syncthingDeviceID:
            raise RuntimeError('Unable to get Syncthing device ID')
        return syncthingDeviceID

    def get_api_key(self):
        secrets_file_path = os.path.join(self.web3mcserverLogic.secrets_path, self.web3mcserverLogic.secrets_file_name)
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
        try:
            syncthingApiKey = self.get_api_key() # same key for everyone in the cluster
            headers = {"X-API-Key": syncthingApiKey}
            url = f"{syncthing_address}rest/system/shutdown"
            response = requests.post(url, headers=headers)
            print(f"[DEBUG] {response.text}")
        except:
            try:
                print("[DEBUG] Couldn't kill syncthing, trying again...")
                os.killpg(os.getpgid(syncthing_process.pid), signal.SIGTERM)
            except:
                print(f"[DEBUG] Failed to kill syncthing, kill it manually. Address: {syncthing_address}")
                syncthing_process.terminate() # doesn't seem to do anything?
                syncthing_process.kill() # doesn't seem to do anything?

    def get_remote_syncthing_ID(self):
        remoteSyncthingAddress = self.web3mcserverLogic.get_syncthing_server_address()
        syncthingApiKey = self.get_api_key()
        headers = {"X-API-Key": syncthingApiKey}
        url = f"{remoteSyncthingAddress}/rest/system/status"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response_json = response.json()
        my_id = response_json["myID"]
        print(f"[DEBUG] API KEY: {syncthingApiKey}, remoteSyncthingAddress: {remoteSyncthingAddress}, remoteSyncthingID: {my_id}")
        return my_id

    def syncthing_active(self, syncthing_address):
        #remoteSyncthingAddress = self.web3mcserverLogic.get_syncthing_server_address()
        secret = self.get_api_key() # Replace with your actual secret key
        headers = {'X-API-Key': secret}
        try:
            response = requests.get(f"{syncthing_address}/rest/system/ping", headers=headers, timeout=30)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def connect_to_syncthing_peer(self, ID):
        pass

    def exist_tunnels_with_this_secret(self):
        pass

    def there_are_active_tunnels(self):
        pass

    def put_observer_for_changes(self):
        pass

    def wait_for_sync_to_finish(self):
        pass