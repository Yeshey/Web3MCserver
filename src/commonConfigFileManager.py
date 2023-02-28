import os
import toml
import random

class CommonConfigFileManager:
    def __init__(self, web3mcserverLogic):
        self.web3mcserverLogic = web3mcserverLogic

    def update_common_config_file(self, shutting_down = False):
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
        
        # Update the config with new values
        if 'info' not in config:
            config['info'] = []
        for i in range(3):
            new_info = {
                'ID': '-'.join([''.join(random.choices('0123456789ABCDEF', k=8)) for j in range(8)]),
                'some_info': 'some_value',
            }
            config['info'].append(new_info)
        config['server_run_priority'] = 10
        config['Is_Host'] = True
        
        print(f"this is the path: {self.web3mcserverLogic.common_config_file_path}")

        # Save the updated config to file
        with open(self.web3mcserverLogic.common_config_file_path, 'w') as f:
            toml.dump(config, f)

    def update_common_config_file_to_say_that_im_new_host(self):
        pass

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