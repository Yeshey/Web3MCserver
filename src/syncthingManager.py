import webbrowser
import subprocess

class SyncthingManager:
    def __init__(self, web3mcserverLogic):
        self.web3mcserverLogic = web3mcserverLogic

    def launch_syncthing_in_separate_thread(self, save_syncthing_server_address_in_secrets = False):
        print("Starting Syncthing server in tunnel...")

        # todo: to make it more secure you should add password and user. But it seems like you'd need to stop syncthing and run some commands and start again
        # https://docs.syncthing.net/users/faq.html#how-do-i-reset-the-gui-password
        
        #t = threading.Thread(target=self.launch_syncthing)
        #t.start()

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

    def get_remote_syncthing_ID(self):
        remoteSyncthingID = self.web3mcserverLogic.get_syncthing_server_address()
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