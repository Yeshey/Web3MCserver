import os
import string
import toml
import random

class CommonConfigFileManager:
    def __init__(self, web3mcserverLogic):
        self.web3mcserverLogic = web3mcserverLogic

    def update_common_config_file(self, recalculate_server_run_priority, Is_Host = None):
        # recalculate_server_run_priority: True or false
        # Is_Host = None, True False, if nothing given, keep as it was.

        # Check if the folder exists, create it if necessary
        folder_path = os.path.dirname(self.web3mcserverLogic.common_config_file_path)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # Check if the file exists, load it if necessary
        if os.path.exists(self.web3mcserverLogic.common_config_file_path):
            with open(self.web3mcserverLogic.common_config_file_path, 'r') as f:
                config = toml.load(f)
        else:
            config = {}

        try:
            syncthingDeviceID = self.web3mcserverLogic.syncthing_manager.get_syncthing_ID()
        except RuntimeError as e:
            print("[DEBUG] Syncthing config doesn't exist yet: ", e)
            return

        # Check if a machine with the same ID already exists in the config
        machine_exists = False
        for machine in config.get('machines', []):
            if machine.get('ID') == syncthingDeviceID:
                machine_exists = True
                # Update the existing machine's information
                if recalculate_server_run_priority:
                    machine['server_run_priority'] = self.web3mcserverLogic.test_machine()
                machine['Is_Host'] = Is_Host if Is_Host is not None else machine['Is_Host']
                break

        # If the machine doesn't exist, add a new one to the list
        if not machine_exists:
            new_machine = {
                'ID': syncthingDeviceID,
                'Is_Host': Is_Host if Is_Host is not None else False,
                'server_run_priority': self.web3mcserverLogic.test_machine()
            }
            config.setdefault('machines', []).append(new_machine)

        # Save the updated config to file
        with open(self.web3mcserverLogic.common_config_file_path, 'w') as f:
            toml.dump(config, f)

    def update_common_config_file_periodically(self):
        pass

    def my_priority_position_in_common_config_file(self):
        pass

    def new_node_and_update_common_config_file(self):
        pass

    def mark_other_machines_as_not_online(self):
        pass

    def check_periodically_for_online_peers_and_updates_common_sync_file_in_separate_thread(self):
        pass

    def is_new_node_and_update_common_config_file(self):
        return True