# shell.nix

let
  pkgs = import <nixpkgs> {};
in
  pkgs.mkShell {
    buildInputs = [
      pkgs.haskellPackages.ghc
      pkgs.niv
      pkgs.cabal-install
      # add any other dependencies here
    ];
  }
