import os

def secret():
    if not os.path.exists("./../secrets/secrets.txt"):
        print("secrets.txt doesn't exist")
        # create secrets folder if it doesn't exist
        if not os.path.exists("secrets"):
            os.makedirs("secrets")
        # create secrets.txt file and write nothing inside
        with open('secrets/secrets.txt', 'w') as f:
            pass
        print("creating... put your secret inside ./secrets/secrets.txt and run me again")
        return

    with open("./../secrets/secrets.txt", "r") as f:
        secret = f.read().strip() # clean white space around the secret
        return secret