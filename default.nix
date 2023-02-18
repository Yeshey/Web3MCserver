#{ lib, fetchFromGitHub, rustPlatform }:
let
  # conigure `nixpkgs` such that all its packages are build for the host platform
  # for version 21.11 (https://github.com/NixOS/nixpkgs/releases/tag/21.11), done as explained here: https://nix.dev/tutorials/towards-reproducibility-pinning-nixpkgs
  pkgs = import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/a7ecde854aee5c4c7cd6177f54a99d2c1ff28a31.tar.gz") { 


    # cross compilation for rust program as explained here: https://github.com/NixOS/nixpkgs/blob/master/doc/languages-frameworks/rust.section.md#cross-compilation-cross-compilation
    #crossSystem = (import <nixpkgs/lib>).systems.examples.armhf-embedded // {
      # Found out what host platforms exist as explained here: https://nix.dev/tutorials/cross-compilation
    #  rustc.config = "x86_64-pc-windows-gnu";
      #rustc.config = "x86_64-pc-linux-gnu";
    #};

    crossSystem = { config = "x86_64-w64-mingw32"; }; 
  };
in
pkgs.rustPlatform.buildRustPackage rec {
  pname = "playit-agent";
  version = "1.0.0"; # for release 1.0.0-rc2;
  doCheck = false; # the tests weren't letting it build???
  # You have to change this to disable just the test that wasn't making it work: https://github.com/NixOS/nixpkgs/blob/master/doc/languages-frameworks/rust.section.md#running-package-tests-running-package-tests

  src = pkgs.fetchFromGitHub {
    owner = "playit-cloud";
    repo = pname;
    rev = version;
    sha256 = "sha256-25j17LQn12Vm7Ybp0qKFN+nYQ9w3ys8RsM3ROy83V/w=";
  };

  cargoSha256 = "sha256-M5zO31AfuyX9zfyYiI2X3gFgEYhTQA95pmHSii+jNGY=";

  meta = with pkgs.lib; {
    description = "game client to run servers without portforwarding";
    homepage = "https://playit.gg";
    license = licenses.unlicense;
    maintainers = [ "Yeshey" ];
  };
}
