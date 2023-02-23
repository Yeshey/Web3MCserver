import subprocess

class PlayitCliManager:
    def __init__(self, bin_path):
        self.bin_path = bin_path

    def process_of_making_new_playitcli_secret(self):
        pass

    def launch_python_playitcli_server_on_separate_thread(self):
        pass

    def launch_minecraft_playitcli_server_on_separate_thread(self):
        print("Starting Playit-cli...")

        subprocess.run([self.bin_path + "/playit-cli", "launch", "./../playit-cli_config/config.toml"], cwd="./server")