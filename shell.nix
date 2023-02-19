# pinning nixpkgs in version 21.11 (https://github.com/NixOS/nixpkgs/releases/tag/21.11), done as explained here: https://nix.dev/tutorials/towards-reproducibility-pinning-nixpkgs
{ pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/a7ecde854aee5c4c7cd6177f54a99d2c1ff28a31.tar.gz") {
  config.allowUnfree = true; # for steam-run
} }:

let
  my-python = pkgs.python3;
  python-with-my-packages = my-python.withPackages (p: with p; [
    distro # to see that we're on nixOS
    # pandas
    #beautifulsoup4
    #requests
    #lxml
    #pillow
    # other python packages you want
  ]);
in
pkgs.mkShell {
  buildInputs = [
    python-with-my-packages
    pkgs.cacert # to fix certificate issues (https://github.com/NixOS/nixpkgs/issues/66716#issuecomment-883399373)
    pkgs.steam-run # I know this sucks, but making nix work sucks more..
    #pkgs.curl
    #pkgs.unzip
    #pkgs.tar
  ];

  shellHook = ''
    PYTHONPATH=${python-with-my-packages}/${python-with-my-packages.sitePackages}

    # Download dependencies using the Python script
    python3 download_dependencies.py

    # maybe set more env-vars
  '';
}
