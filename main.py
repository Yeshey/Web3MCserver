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
        cli_path = os.path.join(base_path, 'lib', 'windows', 'playit-cli.exe')
    elif system == 'Linux':
        if 'NixOS' in distro.name():
            cli_path = 'steam-run ' + os.path.join(base_path, 'lib', 'linux', 'playit-cli')
            #cli_path = ['steam-run', cli_path]
        else:
            cli_path = os.path.join(base_path, 'lib', 'linux', 'playit-cli')
    else:
        print(f"Unsupported system: {system}")
        return

    os.system(cli_path)
    #subprocess.run(cli_path)

if __name__ == '__main__':
    main()
