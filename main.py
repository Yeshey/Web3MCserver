import platform
import urllib.request
import os

def main():
    # Get the name of the operating system
    os_name = platform.system().lower()

    # Set the URLs and file paths based on the OS name
    if os_name == 'windows':
        syncthing_url = 'https://github.com/syncthing/syncthing/releases/download/v1.23.1/syncthing-windows-amd64-v1.23.1.zip'
        playit_url = 'https://github.com/playit-cloud/playit-agent/releases/download/v1.0.0-rc2/playit-cli.exe'
        lib_dir = './lib/windows'
    elif os_name == 'linux':
        syncthing_url = 'https://github.com/syncthing/syncthing/releases/download/v1.23.1/syncthing-linux-amd64-v1.23.1.tar.gz'
        playit_url = 'https://github.com/playit-cloud/playit-agent/releases/download/v1.0.0-rc2/playit-cli'
        lib_dir = './lib/linux'
    else:
        print(f"Unsupported OS: {os_name}")
        return

    # Create the lib directory if it doesn't exist
    if not os.path.exists(lib_dir):
        os.makedirs(lib_dir)

    # Download Syncthing and Playit
    syncthing_path = os.path.join(lib_dir, os.path.basename(syncthing_url))
    playit_path = os.path.join(lib_dir, os.path.basename(playit_url))
    urllib.request.urlretrieve(syncthing_url, syncthing_path)
    urllib.request.urlretrieve(playit_url, playit_path)

if __name__ == '__main__':
    main()
