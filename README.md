# Web3MCserver
Distributed Minecraft server to run always on the available PC

# Links

- [playit repository](https://github.com/playit-cloud/playit-agent)  
- [syncthing repository](https://github.com/syncthing/syncthing)
- syncthing [rest API](https://docs.syncthing.net/dev/rest.html) & [development documentation](https://docs.syncthing.net/v1.19.1/dev/intro.html) & [event API documentation](https://docs.syncthing.net/v1.19.1/dev/events.html)
- syncthing [community contributions](https://docs.syncthing.net/v1.19.1/users/contrib.html#contributions) for reference, like [syncthingtray](https://github.com/Martchus/syncthingtray)
- Example command to get latest event on syncthing: `curl -H "X-API-Key: nsMQDyVwYkQAbRYJXfXdbHD4Rmkawa4A" "http://localhost:8384/rest/events?since=0&limit=1"`
- You can check [this flake for modded minecraft servers](https://github.com/mkaito/nixos-modded-minecraft-servers)
- [Run Go from Haskell?(To compile syncthing from Haskell)](https://sakshamsharma.com/2018/02/haskell-golang-ffi/)
- [Getting Started with GHC & cabal](https://github.com/composewell/haskell-dev/blob/master/getting-started.rst#using-dependencies)
- Build syncthing with:
  - for linux: `go run build.go --goos linux -no-upgrade zip` or `go run build.go --goos linux -no-upgrade`
  - for windows: `go run build.go --goos windows -no-upgrade zip`, couldn't ge it to work in any other way, zip file in the same folder as syncthing
- Building my project:
  - I think what I'm going to use is a combination of cabbal + stack.yaml + nix to build everything. Check [this](https://www.reddit.com/r/haskell/comments/yu40pa/comment/iwa66q3/?utm_source=share&utm_medium=web2x&context=3) for an explanation on why haskell.nix exists, and see here [haskell.nix](https://github.com/input-output-hk/haskell.nix)
  - [set up haskell with flakes](https://input-output-hk.github.io/haskell.nix/tutorials/getting-started-flakes.html)

- Set up without flakes, because they don't have cross compilation yet:

# How to run

1. Install nix package manager (in Windows you need WSL)
2. clone and `cd` to the directory 
3. run `nix-shell` to get the environment with the required dependencies
4. run `nix-build -A Web3MCserver.components.exes.Web3MCserver && ./result/bin/Web3MCserver` to build and run
   1. running `nix-build -A projectCross.mingwW64.hsPkgs.Web3MCserver.components.exes.Web3MCserver` compiles it for windows.