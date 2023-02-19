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
        cli_path = os.path.join(base_path, 'bin', 'windows', 'playit-cli.exe')
    elif system == 'Linux':
        if 'NixOS' in distro.name():
            cli_path = os.path.join(base_path, 'bin', 'nixos', 'playit-cli')
        else:
            cli_path = os.path.join(base_path, 'bin', 'linux', 'playit-cli')
    else:
        print(f"Unsupported system: {system}")
        return

    #os.system(cli_path)
    subprocess.run(cli_path)

if __name__ == '__main__':
    main()
