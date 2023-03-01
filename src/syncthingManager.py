import webbrowser
import subprocess
import os
import toml

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
        config_file_path = self.web3mcserverLogic.common_config_file_path
        if not os.path.isfile(config_file_path):
            raise FileNotFoundError(f"Common config file not found: {config_file_path}")

        with open(config_file_path, "r") as f:
            config = toml.load(f)

        syncthing_server_command = config.get("syncthing_server_command")
        if not syncthing_server_command:
            raise ValueError("syncthing_server_command not found in common config file.")

        api_key_arg = [arg for arg in syncthing_server_command.split() if arg.startswith("--gui-apikey=")]
        if not api_key_arg:
            raise ValueError("--gui-apikey argument not found in syncthing_server_command.")

        api_key = api_key_arg[0].split("=")[-1]
        return api_key


    def get_remote_syncthing_ID(self):
        remoteSyncthingID = self.web3mcserverLogic.get_syncthing_server_address()
        syncthingApiKey = self.get_api_key()
        print(f"[DEBUG] API KEY: {syncthingApiKey}, remoteSyncthingID: {remoteSyncthingID}")
        pass

    def connect_to_syncthing_peer(self, syncthing_details_to_connect):
        pass

    def exist_tunnels_with_this_secret(self):
        pass

    def there_are_active_tunnels(self):
        pass

    def put_observer_for_changes(self):
        pass

    def wait_for_sync_to_finish(self):
        pass