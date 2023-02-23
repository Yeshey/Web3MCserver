import os

def secret():
    if not os.path.exists("./../secrets/secrets.toml"):
        print("secrets.toml doesn't exist")
        # create secrets folder if it doesn't exist
        if not os.path.exists("secrets"):
            os.makedirs("secrets")
        # create secrets.toml file and write nothing inside
        with open('secrets/secrets.toml', 'w') as f:
            pass
        print("creating... put your secret inside ./secrets/secrets.toml and run me again")
        return

    with open("./../secrets/secrets.toml", "r") as f:
        secret = f.read().strip() # clean white space around the secret
        return secret