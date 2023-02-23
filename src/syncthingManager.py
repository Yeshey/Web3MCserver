import subprocess

class SyncthingManager:
    def __init__(self, bin_path):
        self.bin_path = bin_path

    def launch_syncthing_in_separate_thread(self):
        print("Starting Playit-cli...")

        subprocess.run([self.bin_path + "/playit-cli", "launch", "./../playit-cli_config/config.toml"], cwd="./server")

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