import os
import string
import threading
import time
import toml
import random

class CommonConfigFileManager:
    def __init__(self, web3mcserverLogic):
        self.web3mcserver = web3mcserverLogic

    def update_common_config_file(self, recalculate_server_run_priority, Is_Host = None): # todo, make thread safe?
        # recalculate_server_run_priority: True or false
        # Is_Host = None, True False, if nothing given, keep as it was.

        self.web3mcserver.isHost = Is_Host if Is_Host is not None else self.web3mcserver.isHost

        # Check if the folder exists, create it if necessary
        folder_path = os.path.dirname(self.web3mcserver.common_config_file_path)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # Check if the file exists, load it if necessary
        if os.path.exists(self.web3mcserver.common_config_file_path):
            with open(self.web3mcserver.common_config_file_path, 'r') as f:
                config = toml.load(f)
        else:
            config = {}

        # return if my syncthing is not running
        syncthingDeviceID = self.web3mcserver.syncthing_manager.get_my_syncthing_ID()
        if syncthingDeviceID is None:
            print("[DEBUG] Couldn't get Syncthing ID")
            return
        
        updateSyncthingShenenigans = False
        try:
            if self.web3mcserver.file_has_field(file = os.path.join(self.web3mcserver.secrets_path, self.web3mcserver.secret_addresses_file_name), field = "syncthing_server_command"):
                remote_address = self.web3mcserver.get_syncthing_server_address()
                if self.web3mcserver.syncthing_manager.syncthing_active(remote_address, timeout=1):
                    updateSyncthingShenenigans = True
                    print("[DEBUG] Syncthing online, updating common config file about remote syncthing")
            else:
                print("[DEBUG] Syncthing server address field in file doesn't exist yet. Not updating common config file about remote syncthing")
        except KeyboardInterrupt:
            # handle KeyboardInterrupt separately
            print("KeyboardInterrupt caught")
            raise KeyboardInterrupt
        except Exception as e:
           updateSyncthingShenenigans = False 
        if updateSyncthingShenenigans:
            try:
                hostID = self.web3mcserver.syncthing_manager.get_remote_syncthing_ID()
            except KeyboardInterrupt:
                # handle KeyboardInterrupt separately
                print("KeyboardInterrupt caught")
                raise KeyboardInterrupt
            except Exception as e:
                print(f"[DEBUG] Exception getting remote ID: {e}, Not updating common config file about remote syncthing")
                updateSyncthingShenenigans = False
        if updateSyncthingShenenigans:
            myID = self.web3mcserver.syncthing_manager.get_my_syncthing_ID()
            # clean up the ones that are not host and claim they are () on second thought, we don't even need the isHost right? we can just check...
            for machine in config.get('machines', []):
                if machine.get('ID') == hostID:
                    if hostID == myID and Is_Host == False: # unless I'm the host but terminatting
                        machine['Is_Host'] = False
                    else:
                        machine['Is_Host'] = True
                else:
                    machine['Is_Host'] = False

        # Check if a machine with the same ID already exists in the config
        machine_exists = False
        for machine in config.get('machines', []):
            if machine.get('ID') == syncthingDeviceID:
                machine_exists = True
                # Update the existing machine's information
                if recalculate_server_run_priority:
                    machine['server_run_priority'] = self.web3mcserver.test_machine()
                machine['Is_Host'] = Is_Host if Is_Host is not None else machine['Is_Host']
                break

        # If the machine doesn't exist, add a new one to the list
        if not machine_exists:
            new_machine = {
                'ID': syncthingDeviceID,
                'Is_Host': Is_Host if Is_Host is not None else False,
                'server_run_priority': self.web3mcserver.test_machine()
            }
            config.setdefault('machines', []).append(new_machine)

        # Save the updated config to file
        with open(self.web3mcserver.common_config_file_path, 'w') as f:
            toml.dump(config, f)

    def update_common_config_file_periodically(self):
        # should skip if in the process of choosing new host
        def run_update():
            while True:
                print("[DEBUG] running update_common_config_file_periodically")
                self.update_common_config_file(recalculate_server_run_priority=True, Is_Host=None)
                time.sleep(7200)  # sleep for 2 hours
        
        thread = threading.Thread(target=run_update)
        thread.daemon = True # so this thread ends automatically when main thread ends
        thread.start()

    def sorted_dic_of_ID_and_server_run_priority(self):
        my_id = self.web3mcserver.syncthing_manager.get_my_syncthing_ID()
        online_peers = self.web3mcserver.syncthing_manager.online_peers_list()
        everyone_online = online_peers + [my_id]
        print(f"[DEBUG] Online peers: {online_peers}")
        
        # Load the config file
        with open(self.web3mcserver.common_config_file_path) as f:
            config = toml.load(f)
        
        # Get server run priorities for online peers
        try:
            _ = config["machines"]
        except KeyboardInterrupt:
            # handle KeyboardInterrupt separately
            print("KeyboardInterrupt caught")
            raise KeyboardInterrupt
        except RuntimeError as e:
            print(f"[DEBUG] exception caught: {e}, common config file still empty, create it")
            self.update_common_config_file()

        priorities = {}
        for machine in config["machines"]:
            if machine["ID"] in everyone_online:
                priorities[machine["ID"]] = machine["server_run_priority"]

        
        # Sort priorities in descending order
        sorted_priorities = dict(sorted(priorities.items(), key=lambda x: x[1], reverse=True))
        return sorted_priorities

    def my_order_in_server_host_priority(self, sorted_priorities):
        # Get my ID
        my_id = self.web3mcserver.syncthing_manager.get_my_syncthing_ID()
        
        # Sort priorities in descending order
        #sorted_priorities = self.sorted_dic_of_ID_and_server_run_priority()
        
        # Find my order in priority queue
        my_priority = sorted_priorities.get(my_id)
        my_order = sum(1 for _, priority in sorted_priorities.items() if priority > my_priority)
        
        return my_order

    def machine_with_highest_priority(self, sorted_priorities):
        # Get sorted priorities
        #sorted_priorities = self.sorted_dic_of_ID_and_server_run_priority()
        
        print(f"[DEBUG] sorted_priorities: {sorted_priorities}")

        # Return the ID of the machine with the highest priority
        return list(sorted_priorities.keys())[0]

    def is_new_node(self):
        try:
            ID = self.web3mcserver.syncthing_manager.get_my_syncthing_ID()
        except KeyboardInterrupt:
            # handle KeyboardInterrupt separately
            print("KeyboardInterrupt caught")
            raise KeyboardInterrupt
        except Exception as e:
            return True

        print(self.web3mcserver.common_config_file_path)

        if not os.path.exists(self.web3mcserver.common_config_file_path):
            with open(self.web3mcserver.common_config_file_path, 'w') as f:
                f.write('')

        with open(self.web3mcserver.common_config_file_path) as f:
            machines = toml.load(f).get("machines", [])

        for machine in machines:
            if machine.get("ID") == ID:
                return False

        return True