
class Codes:
    ERROR_CODE_EXISTING_USER = 1001
    ERROR_CODE_NOT_EXISTING_USER = 1002
class CryptoException(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(self.message)
class ExistingUser(CryptoException):
    def __init__(self):
        self.code=Codes.ERROR_CODE_EXISTING_USER
        self.message='Email already registered'



class NotExistingUser(CryptoException):
    def __init__(self):
        self.code = Codes.ERROR_CODE_EXISTING_USER
        self.message = "User doesn't exist"