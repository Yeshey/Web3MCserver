from src.web3MCserver_logic import Web3MCserverLogic
from src.cli_interface import Cli_interface

if __name__ == "__main__":
    try:
        web3mcserver = Web3MCserverLogic()
        ui_cli = Cli_interface(web3mcserver)
        ui_cli.start()
    except KeyboardInterrupt:
        print ("\n\n----- Interrupted by Keyboard... -----\n")