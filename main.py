from python.download_dependencies import *
import os
import subprocess
import platform
import distro
import threading

def start_syncthing():
    print("Starting Syncthing...")

    subprocess.run([bin_path + "/syncthing/syncthing", "--home", "./syncthing_config"])

def start_playit_cli():
    print("Starting Playit-cli...")

    new_client_connecting()

    subprocess.run([bin_path + "/playit-cli", "launch", "./../playit-cli_config/config.toml"], cwd="./server")

    print ("HELLOOOOOOOOOOOOO")
    # cwd used so server fis are generated in the right place
    # final playit-gg command might be: playit-cli --secret 9cdb9e37b46ef10baa7d15f2c1d84b9852ddfc4d7085c5ae7dfe49399f63872a run 9e0a3886-8b6d-403a-9755-1d67987eb440=192.168.1.109:25565
    # Example: ./bin/nixos/playit-cli launch ./playit-cli_config/config.toml

def new_client_connecting():
    print("ok")

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
    threading.Thread(target=start_playit_cli).start()
    

if __name__ == "__main__":
    main()

# How to make a configuration file for playit-gg:
'''
Based on the launch.rs file, it seems to be a Rust code for launching and managing tunnels, probably for a network application.

From the LaunchConfig struct, the configuration file may have the following fields:

    agent_name: The name of the agent that is running.
    agent_type: The type of the agent that is running. This field is optional.
    secret_key: The secret key to use to authenticate with the server.
    secret_path: The path to the secret key file.
    command: The command to run.
    command_args: Any arguments to pass to the command.
    env_overrides: A mapping of environment variable overrides.
    tunnels: A list of tunnels that need to be set up, each with the following fields:
        id: The ID of the tunnel. This field is optional.
        tunnel_type: The type of the tunnel. This field is optional.
        name: The name of the tunnel.
        proto: The protocol used by the tunnel. (Both, Tcp or Udp)
        port_count: The number of ports used by the tunnel.
        local: The local port used by the tunnel. This field is optional.

The configuration file may also have a PLAYIT_SECRET environment variable, which can be used as a fallback secret key if the secret_key field is not provided.
'''