# pinning nixpkgs in version 21.11 (https://github.com/NixOS/nixpkgs/releases/tag/21.11), done as explained here: https://nix.dev/tutorials/towards-reproducibility-pinning-nixpkgs
{ pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/06278c77b5d162e62df170fec307e83f1812d94b.tar.gz") {
    # config.allowUnfree = true; # for steam-run
  }
}:

let
  my-python = pkgs.python3;
  python-with-my-packages = my-python.withPackages (p: with p; [
    distro # to see that we're on nixOS
    toml
    notify-py
    # pandas
    # beautifulsoup4
    # requests
    # lxml
    # pillow
    # other python packages you want
  ]);
in
pkgs.mkShell {
  buildInputs = [
    python-with-my-packages
    pkgs.cacert # to fix certificate issues (https://github.com/NixOS/nixpkgs/issues/66716#issuecomment-883399373)
    libnotify # to support notifications
    jdk17
    # pkgs.steam-run # I know this sucks, but making nix work sucks more..
    #pkgs.curl
    #pkgs.unzip
    #pkgs.tar
  ];

  shellHook = ''
    PYTHONPATH=${python-with-my-packages}/${python-with-my-packages.sitePackages}

    # Download dependencies using the Python script
    python3 ./src/utils/download_dependencies.py

    if [ ! -d ./bin/nixos/syncthing ]; then
      echo "[shell.nix]: Downloading syncthing..."
      mkdir -p ./bin/nixos/syncthing/
      cp ${pkgs.syncthing}/bin/syncthing ./bin/nixos/syncthing/
      chmod +x ./bin/nixos/syncthing/syncthing
    else
      echo "[shell.nix]: Directory ./bin/nixos/syncthing already exists, skipping download"
    fi

    if [ -f "./bin/nixos/playit-cli" ]; then
      echo "[shell.nix]: File ./bin/nixos/playit-cli already exists, skipping download."
    else
      echo "[shell.nix]: Downloading playit-cli..."
      cp ${(pkgs.callPackage ./nix/playit-cli.nix {})}/bin/playit-cli ./bin/nixos/
      chmod +x ./bin/nixos/playit-cli
    fi

    echo
    echo "run 'python3 main.py' to start the program"
  '';
}
