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
