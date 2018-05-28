
class Packet:

    def __init__(self, seq_num, file_data, time):
        self.__seq_num = seq_num
        self.__file_data = file_data
        self.__time = time

    def get_seq_num(self):
        return self.__seq_num

    def get_file_data(self):
        return self.__file_data

    def set_time(self, time):
        self.__time = time

    def get_time(self):
        return self.__time
