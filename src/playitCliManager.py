import subprocess
import webbrowser

class PlayitCliManager:
    def __init__(self, web3mcserverLogic):
        self.web3mcserverLogic = web3mcserverLogic

    def launch_python_playitcli_server_on_separate_thread(self):
        pass

    def create_syncthing_tunnel():
        # create syncthing tunnel and save secret
        pass

    def create_server_tunnel():
        # create syncthing tunnel and save secret
        pass

    def make_new_secret(self):
        # run
        # playit-cli claim generate
        # playit-cli claim url <CODE>
        # playit-cli claim exchange <CODE>
        
        playitcli_code = subprocess.check_output([self.web3mcserverLogic.bin_path + "/playit-cli", "claim", "generate"])

        playitcli_code = playitcli_code.decode().strip()
        print("[DEBUG] playitcli_code: "+ playitcli_code)

        url_of_site = subprocess.check_output([self.web3mcserverLogic.bin_path + "/playit-cli", "claim", "url", playitcli_code])
        url_of_site = url_of_site.decode().strip()
        print("[DEBUG] If site doesn't open, open it manually: " + url_of_site)
        webbrowser.open(url_of_site, new=0, autoraise=True) 

        playitcli_secret = subprocess.check_output([self.web3mcserverLogic.bin_path + "/playit-cli", "claim", "exchange", playitcli_code])
        playitcli_secret = playitcli_secret.decode().strip()

        print("[DEBUG] This is the secret: "+ playitcli_secret)
        return playitcli_secret


    def launch_minecraft_playitcli_server_on_separate_thread(self):
        print("[DEBUG] Starting Playit-cli...")

        subprocess.run([self.web3mcserverLogic.bin_path + "/playit-cli", "launch", self.web3mcserverLogic.playitcli_config_toml], cwd=self.web3mcserverLogic.server_path)