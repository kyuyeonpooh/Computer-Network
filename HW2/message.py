
class Message:

    REG_FILE = 1
    FILE_LIST = 2
    GET_FILE = 3
    EXIT_MSG = 4
    FILE_SIZE = 100
    WELCOME = 200
    NOTICE = 700
    ERROR = 900    

    def __init__(self, msg_type, msg):
        self.__msg_type = msg_type
        self.__msg = msg

    def get_msg_type(self):
        return self.__msg_type
    
    def get_msg(self):
        return self.__msg


