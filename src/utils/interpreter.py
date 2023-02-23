class Interpreter:
#    def __init__(self):
#        self.msg = ""

    @staticmethod
    def error(self, error_number):
        match error_number:
            case 0:
                print("Not a bad error")
            case 1:
                print("file IO man")
            case _:
                print(f"Error {error_number}: An unexpected error occurred")

