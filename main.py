import os
import subprocess
import platform
import distro
import threading

def start_syncthing():
    print("Starting Syncthing...")

    subprocess.run([cli_path + "/syncthing/syncthing", "--home", "./syncthing_config"])

def start_playit_cli():
    print("Starting Playit-cli...")

    # Example: ./bin/nixos/playit-cli launch ./playit-cli_config/config.toml

    subprocess.run([cli_path + "/playit-cli", "launch", "./playit-cli_config/config.toml"])
    # final playit-gg command might be: playit-cli --secret 9cdb9e37b46ef10baa7d15f2c1d84b9852ddfc4d7085c5ae7dfe49399f63872a run 9e0a3886-8b6d-403a-9755-1d67987eb440=192.168.1.109:25565

def main():
    base_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_path)

    system = platform.system()
    global cli_path

    if system == 'Windows':
        cli_path = os.path.join(base_path, 'bin', 'windows')
    elif system == 'Linux':
        if 'NixOS' in distro.name():
            cli_path = os.path.join(base_path, 'bin', 'nixos')
        else:
            cli_path = os.path.join(base_path, 'bin', 'linux')
    else:
        print(f"Unsupported system: {system}")
        return


    threading.Thread(target=start_syncthing).start()
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
        proto: The protocol used by the tunnel.
        port_count: The number of ports used by the tunnel.
        local: The local port used by the tunnel. This field is optional.

The configuration file may also have a PLAYIT_SECRET environment variable, which can be used as a fallback secret key if the secret_key field is not provided.
'''

#This is a example configuration file: (.toml)
'''
agent_name = "my-agent"
agent_type = "rust-agent"

secret_path = "path/to/secret/file"

command = "/path/to/my/command"
command_args = ["arg1", "arg2"]

[tunnels]
[[tunnels.tunnel]]
name = "tunnel1"
proto = "both"
port_count = 2
local = 8080

[[tunnels.tunnel]]
name = "tunnel2"
proto = "udp"
port_count = 1
'''

#This configuration specifies the following:

#    The name of the agent is "my-agent" and its type is "rust-agent".
#    The secret key for the agent is stored in a file located at "path/to/secret/file".
#    The command to run is located at "/path/to/my/command" and its arguments are "arg1" and "arg2".
#    The agent will create two tunnels. The first tunnel is named "tunnel1" and exposes 2 ports over TCP and UDP. The local port used to expose the tunnel is 8080. The second tunnel is named "tunnel2" and exposes 1 port over UDP.

# or...?

'''
agent_name = "my-agent"
command = "python"
command_args = ["-m", "http.server"]
tunnels = [
  { name = "http-tunnel", proto = "tcp", port_count = 1 }
]
'''