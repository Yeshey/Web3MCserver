from .playitCliManager import PlayitCliManager
from .syncthingManager import SyncthingManager
from .commonConfigFileManager import CommonConfigFileManager
import time

class Web3MCserverLogic:
    def __init__(self):
        # needs to be inside to not share data between instances of class
        self.common_config_file_manager = CommonConfigFileManager()
        self.syncthing_manager = SyncthingManager()
        self.playitcli_manager = PlayitCliManager()

    def put_observer_for_changes(self):
        if self.observer_is_triggered_and_server_is_not_running():
            if self.common_config_file_manager.my_priority_position_in_common_config_file() == 0:
                self.i_will_be_host_now()
            else:
                self.check_if_server_started_correctly_or_I_need_to_host()

    def check_if_server_started_correctly_or_I_need_to_host(self):
        time.sleep(30)
        if not self.syncthing_manager.there_are_active_tunnels():
            if self.common_config_file_manager.my_priority_position_in_common_config_file() == 1: #I'm the second option
                self.common_config_file_manager.mark_other_machines_as_not_online()
                self.i_will_be_host_now()

    def shutting_down_now(self):
        self.common_config_file_manager.update_common_config_file(shutting_down = True)
        self.syncthing_manager.wait_for_sync_to_finish()
        self.close_all_threads()

    def i_will_be_host_now(self):
        print("becoming host")
        self.common_config_file_manager.check_periodically_for_online_peers_and_updates_common_sync_file_in_separate_thread()
        self.syncthing_manager.wait_for_sync_to_finish()
        self.common_config_file_manager.update_common_config_file_to_say_that_im_new_host()
        self.playitcli_manager.launch_python_playitcli_server_on_separate_thread()
        self.playitcli_manager.launch_minecraft_playitcli_server_on_separate_thread()

    def files_exist_in_server_folder(self):
        pass

    def download_minecraft_server(self):
        pass

    def i_will_be_host_now(self):
        pass

    def secrets_file_in_place(self):
        pass

    def delete_files_inside_server_folder(self):
        pass

    def observer_is_triggered_and_server_is_not_running(self):
        pass

    def close_all_threads(self):
        pass

    def there_are_active_tunnels(self):
        pass

    class FatalError(Exception):
        pass
