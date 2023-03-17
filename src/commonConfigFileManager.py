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
        try:
            syncthingDeviceID = self.web3mcserver.syncthing_manager.get_my_syncthing_ID()
        except RuntimeError as e:
            print("[DEBUG] Syncthing config doesn't exist yet: ", e)
            return

        try:
            myID = self.web3mcserver.syncthing_manager.get_my_syncthing_ID()
            hostID = self.web3mcserver.syncthing_manager.get_remote_syncthing_ID()
            # clean up the ones that are not host and claim they are () on second thought, we don't even need the isHost right? we can just check...
            for machine in config.get('machines', []):
                if machine.get('ID') == hostID:
                    if hostID == myID and Is_Host == False: # unless I'm the host but terminatting
                        machine['Is_Host'] = False
                    else:
                        machine['Is_Host'] = True
                else:
                    machine['Is_Host'] = False
        except:
            print("[DEBUG] not updating common config file about remote syncthing, because exception ocurred")

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
                self.update_common_config_file(recalculate_server_run_priority=True, Is_Host=None)
        
        thread = threading.Thread(target=run_update)
        thread.daemon = True # so this thread ends automatically when main thread ends
        thread.start()

    def my_order_in_server_host_priority(self):
        # Get my ID
        my_id = self.web3mcserver.syncthing_manager.get_my_syncthing_ID()
        online_peers = self.web3mcserver.syncthing_manager.online_peers_list()
        everyone_online = online_peers.append(my_id)
        print(f"[DEBUG] Online peers: {online_peers}")
        
        # Load the config file
        with open(self.web3mcserver.common_config_file_path) as f:
            config = toml.load(f)
            
        # Get the server_run_priority values for all online peers and myself
        server_priorities = [machine['server_run_priority'] for machine in config['machines'] if machine['ID'] in everyone_online]
        server_priorities.sort(reverse=True)

        # Get my position in the priority list
        my_priority = config['machines'][config['machines'].index({'ID': my_id})]['server_run_priority']
        my_position = len([priority for priority in server_priorities if priority > my_priority])

        return my_position

    def is_new_node(self):
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