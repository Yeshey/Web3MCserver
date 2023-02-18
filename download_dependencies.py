import os
import sys
import urllib.request
import zipfile
import tarfile

DOWNLOAD_PATHS = {
    'Windows': ('./lib/windows', [
        ('https://github.com/syncthing/syncthing/releases/download/v1.23.1/syncthing-windows-amd64-v1.23.1.zip', 'syncthing.zip'),
        ('https://github.com/playit-cloud/playit-agent/releases/download/v1.0.0-rc2/playit-cli.exe', 'playit-cli.exe')
    ]),
    'Linux': ('./lib/linux', [
        ('https://github.com/syncthing/syncthing/releases/download/v1.23.1/syncthing-linux-amd64-v1.23.1.tar.gz', 'syncthing.tar.gz'),
        ('https://github.com/playit-cloud/playit-agent/releases/download/v1.0.0-rc2/playit-cli', 'playit-cli')
    ])
}

def main():
    if sys.platform.startswith('win'):
        SYSTEM = 'Windows'
    elif sys.platform.startswith('linux'):
        SYSTEM = 'Linux'
    else:
        raise OSError(f'Unsupported operating system: {sys.platform}')

    download_path, files = DOWNLOAD_PATHS[SYSTEM]
    os.makedirs(download_path, exist_ok=True)

    syncthing_path = os.path.join(download_path, 'syncthing')
    if os.path.exists(syncthing_path):
        print('Syncthing folder already exists. Skipping download and extraction.')
    else:
        for url, filename in files:
            file_path = os.path.join(download_path, filename)
            if os.path.exists(file_path):
                print(f'File {filename} already exists. Skipping download.')
            else:
                print(f'Downloading {filename} from {url}')
                urllib.request.urlretrieve(url, file_path)

            if filename.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(download_path)
                os.remove(file_path)
            elif filename.endswith('.tar.gz'):
                with tarfile.open(file_path, 'r:gz') as tar_ref:
                    extracted_path = tar_ref.getnames()[0]
                    tar_ref.extractall(download_path)
                os.remove(file_path)
                os.rename(os.path.join(download_path, extracted_path), syncthing_path)

if __name__ == '__main__':
    main()
