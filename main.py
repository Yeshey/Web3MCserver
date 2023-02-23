from src.utils.download_dependencies import *
import os
import subprocess
import platform
import distro
import threading
import time

def start_syncthing():
    print("Starting Syncthing...")

    subprocess.run([bin_path + "/syncthing/syncthing", "--home", "./syncthing_config"])

def start_playit_cli():
    print("Starting Playit-cli...")

    subprocess.run([bin_path + "/playit-cli", "launch", "./../playit-cli_config/config.toml"], cwd="./server")

    # cwd used so server fis are generated in the right place
    # final playit-gg command might be: playit-cli --secret 9cdb9e37b46ef10baa7d15f2c1d84b9852ddfc4d7085c5ae7dfe49399f63872a run 9e0a3886-8b6d-403a-9755-1d67987eb440=192.168.1.109:25565
    # Example: ./bin/nixos/playit-cli launch ./playit-cli_config/config.toml

def main():
    download_dependencies()
    if not os.path.exists("secrets/secrets.txt"):
        print("secrets.txt doesn't exist")
        # create secrets folder if it doesn't exist
        if not os.path.exists("secrets"):
            os.makedirs("secrets")
        # create secrets.txt file and write nothing inside
        with open('secrets/secrets.txt', 'w') as f:
            pass
        print("creating... put your secret inside ./secrets/secrets.txt and run me again")
        return


    base_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_path)

    system = platform.system()
    global bin_path

    if system == 'Windows':
        bin_path = os.path.join(base_path, 'bin', 'windows')
    elif system == 'Linux':
        if 'NixOS' in distro.name():
            bin_path = os.path.join(base_path, 'bin', 'nixos')
        else:
            bin_path = os.path.join(base_path, 'bin', 'linux')
    else:
        print(f"Unsupported system: {system}")
        return


    #threading.Thread(target=start_syncthing).start()
    #threading.Thread(target=start_playit_cli).start()
    
if __name__ == "__main__":
    main()