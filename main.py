import os
import subprocess
import platform

def main():
    base_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_path)

    system = platform.system()
    cli_path = None

    if system == 'Windows':
        cli_path = os.path.join(base_path, 'lib', 'windows', 'playit-cli.exe')
    elif system == 'Linux':
        cli_path = os.path.join(base_path, 'lib', 'linux', 'playit-cli')
    else:
        print(f"Unsupported system: {system}")
        return

    subprocess.run([cli_path])

if __name__ == '__main__':
    main()
