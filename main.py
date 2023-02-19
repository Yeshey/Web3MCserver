import os
import subprocess
import platform
import distro

def main():
    base_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_path)

    system = platform.system()
    cli_path = None

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

    #subprocess.run(cli_path)
    subprocess.run([cli_path + "/syncthing/syncthing", "--home", "./syncthing-config"])

    # example of a port you can use: http://127.0.0.1:37995/
    # this is the command: ./bin/nixos/syncthing/syncthing --home ./syncthing-config

if __name__ == '__main__':
    main()
