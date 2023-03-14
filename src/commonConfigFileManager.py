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

        try:
            syncthingDeviceID = self.web3mcserver.syncthing_manager.get_my_syncthing_ID()
        except RuntimeError as e:
            print("[DEBUG] Syncthing config doesn't exist yet: ", e)
            return

        # clean up the ones that are not host and claim they are () on second thought, we don't even need the isHost right? we can just check...
        for machine in config.get('machines', []):
            if machine.get('Is_Host') == True:
                try:
                    if self.web3mcserver.syncthing_mnager.get_remote_syncthing_ID() != machine.get('ID'):
                        machine['Is_Host'] = False
                except: # not online
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
                time.sleep(7200)  # sleep for 2 hours
                self.update_common_config_file(recalculate_server_run_priority=True, Is_Host=self.web3mcserver.isHost)
        
        thread = threading.Thread(target=run_update)
        thread.daemon = True # so this thread ends automatically when main thread ends
        thread.start()

    def my_order_in_server_host_priority(self):
        # Get my ID
        my_id = self.web3mcserver.syncthing_manager.get_my_syncthing_ID()
        online_peers = self.web3mcserver.syncthing_manager.online_peers()
        print(f"[DEBUG] Online peers: {online_peers}")
        
        # Load the config file
        with open(self.web3mcserver.common_config_file_path) as f:
            config = toml.load(f)
            
        # Find the online host with highest priority
        host = max(config["machines"], key=lambda m: m["server_run_priority"] if m["ID"] in online_peers else float("-inf"))
        
        # Determine own order in server host priority
        if host["ID"] == my_id:
            return 0
        else:
            return sum(1 for m in config["machines"] if m["server_run_priority"] > host["server_run_priority"] and m["ID"] in online_peers)

    def my_priority_position_in_common_config_file(self):
        pass

    def mark_other_machines_as_not_online(self):
        pass

    def check_periodically_for_online_peers_and_updates_common_sync_file_in_separate_thread(self):
        pass

    def is_new_node(self):
        return True
        try:
            ID = self.web3mcserver.syncthing_manager.get_my_syncthing_ID()
        except:
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