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

- download and install python
- run `pip install -r requirements.txt`
- make and get the secret for a playit-gg account: `playit-cli claim generate` && `playit-cli claim url <CODE>` && `playit-cli claim exchange <CODE>`, then you can put the secret in the `./secrets/secrets.toml` file

# To-Do

- Handle the situation when the minectraft server crashes, or the eula needs to be accepted
- [Pin nixpkgs](https://nix.dev/tutorials/towards-reproducibility-pinning-nixpkgs#pinning-nixpkgs)
- Check a working playit-gg tunnel configuration from the website:
- Compile executables (look for Cpython)

| Address              | communications-de.craft.ply.gg  |
| -------------------- | ------------------------------- |
| Custom Domain        | -                               |
| Tunnel Type          | Minecraft Java                  |
| IP                   | 224.ip.ply.gg                   |
| IPV4                 | 147.185.221.224                 |
| IPV6                 | 2602:fbaf::e0                   |
| Protocol             | tcp                             |
| Port                 | 20514                           |
| Port-Range           | 20514-20514                     |
| Port-Count           | 1                               |

# Program Planning:

- Best Java run command for minecraft server: https://aikar.co/2018/07/02/tuning-the-jvm-g1gc-garbage-collector-flags-for-minecraft/

- Check the common syncthing file and update it, if exists, I'm a new node (this file has the syncthing ID of each machine and a score based on internet speed and hardware power to see how likely it is to be picked to host, and weather each one is online or not, and witch one is running the server) 
- If I'm a new node: 
  - Check if there are files in the server folder, and say that if we don't make a new minecraft server they will be deleted.
  - Question If I want to make a new distributed minecraft server? 
    - YES 
      - Walk user through the process of making a new secret with playit-cli: `playit-cli claim generate` && `playit-cli claim url <CODE>` && `playit-cli claim exchange <CODE>`, then you can put the secret in the `./secrets/secrets.toml` file
      - Download minecraft 1.19.3 jar file and put it in the server folder.
      - <span style="color:lightgreen">Launch syncthing in another thread.</span>
      - <span style="color:lightgreen">Create the common config file</span>
      - <span style="color:lightgreen">Run it_has_been_determined_that_I_am_the_host_now()</span>
    - NO:  
      - delete the files inside ./server
      - Send a message to the playit-cli python tunnel with secret 
        - If no answer, wait, and send a new message every 30 seconds 
      - Get details to connect to syncthing 
      - Send message to connect to syncthing | have syncthing auto accept and sync the folders, and everyone is an introducer 
      - <span style="color:lightgreen">Launch syncthing in another thread.</span>
      - <span style="color:lightgreen">Create the common config file</span>
      - <span style="color:lightgreen">Run it_has_been_determined_that_I_am_the_host_now()</span>
- If I'm not a new node: 
  - Uses secret and checks out tunnels 
    - If no Tunnels  
      - Fatal error 
    - There are tunnels: 
      - None are active: 
        - then "WARNING MESSAGE" saying that its not possible to confirm that I have the latest version of the server, starting anyways. 
        - <span style="color:red">Run it_has_been_determined_that_I_am_the_host_now()</span> 
      - Playit-cli python server and playit-cli minecraft-server ports are active and reachable, the server is being ran by a peer 
        - Put an observer in the syncthing files, or in the server ports 
        - Run a thread that updates the sync file every 20min with info on how good this machine is to host 
        - If observer is triggered and the server isn't running, then 
        - Check if I have the heighest value and am gonna be picked to run the server 
          - NO 
            - Check in 30 seconds if server is already running, if not, then if I'm the second option in the list start, if not wait 30 more seconds.       
          - YES 
            - Update the sync file with the information, all the machines that were supposed to start the server but didn't should be marked as not online,  
            - <span style="color:red">Run it_has_been_determined_that_I_am_the_host_now()</span> 

 

When shutting down: 
- Update the syncthing common file saying that I'm not online anymore and I'm not hosting if need be, wait for it to finish syncing. 
- Close all threads. 

 

<span style="color:red">Run it_has_been_determined_that_I_am_the_host_now():</span> 
- Run a thread that checks every 20min for peers that are not Online and updates them in the common syncthing file if it is not up to date. 
- Check if all files have been synced, if I have the latest version of the files, if not, wait for them to finish syncing. 
- Change the file informing saying that I'm going to host now 
- Launch the playit-cli python server on another thread  
- Launch the playit-cli minecraft server 