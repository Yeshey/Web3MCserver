import subprocess
import time
import threading

class SyncthingManager:
    def __init__(self, web3mcserverLogic):
        self.web3mcserverLogic = web3mcserverLogic

    def launch_syncthing_in_separate_thread(self, save_syncthing_server_address_in_secrets = False):
        print("Starting Syncthing server in tunnel...")

        # todo: to make it more secure you should add password and user. But it seems like you'd need to stop syncthing and run some commands and start again
        # https://docs.syncthing.net/users/faq.html#how-do-i-reset-the-gui-password
        
        t = threading.Thread(target=self.launch_syncthing)
        t.start()

        time.sleep(15) # terrible terrible practice

        tunnels_list = subprocess.check_output([self.web3mcserverLogic.bin_path + "/playit-cli", 
            "--secret", 
            self.web3mcserverLogic.get_secrets_playitcli_file(),
            "tunnels", 
            "list"])
        tunnels_list = tunnels_list.decode().strip()
        port_of_first_tunnel = tunnels_list.split()[4]
        address_of_first_tunnel = tunnels_list.split()[3]

        print(f"[DEBUG] You can access syncthing with: http://{address_of_first_tunnel}:{port_of_first_tunnel}")

        
        if save_syncthing_server_address_in_secrets:
            # todo: add the address syncthing is running on to the secrets.
            pass

        time.sleep(100)

        #subprocess.run([self.web3mcserverLogic.bin_path + "/syncthing/syncthing", "--home", self.web3mcserverLogic.syncthing_config])

    def launch_syncthing(self):
        subprocess.run([self.web3mcserverLogic.bin_path + "/playit-cli", "launch", self.web3mcserverLogic.playitcli_toml_config_syncthing_server], cwd="./../")    

    def get_syncthing_details_from_playit_cli_python_server(self):
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