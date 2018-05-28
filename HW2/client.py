
from socket import *
from select import select
import sys
import os
import time
from message import *
import pickle
from colors import *


class RelayClient:

    def __init__(self, user_id, port, host_addr):
        self.__socket = None
        self.__conn_list = [sys.stdin] # add stdin for non-blocking
        self.__user_id = user_id
        self.__port = port
        self.__host_addr = host_addr

    # initialize socket
    def init_socket(self):
        self.__socket = socket(AF_INET, SOCK_STREAM)
        try:
            self.__socket.connect((self.__host_addr, self.__port))
        except Exception as e:
            print_red("Failed connecting to {}.".format(self.__host_addr))
            sys.exit(1)
        print_green("Connected to server {}.".format(self.__host_addr))
        self.__conn_list.append(self.__socket) # add client socket into the list

    # start communicating with server
    def start(self):
        try:
            while True:
            
                # get list of sockets ready to be used
                read_socket, write_socket, err_socket = select(self.__conn_list, [], [], 10)
                
                # either connected socket or stdin
                for sock in read_socket:

                    # get message from the server
                    if sock is self.__socket:

                        # get data from the server
                        data = sock.recv(2048)

                        if data:
                            msg = pickle.loads(data)                            
                            msg_type = msg.get_msg_type()
                            
                            # server starts to transfer the file
                            if msg_type == Message.FILE_SIZE:
                                file_size = msg.get_msg()
                                file_name = sock.recv(2048).decode()
                                self.get_file(file_name, file_size, sock)

                            # send user id to the server
                            if msg_type == Message.WELCOME:
                                msg = Message(Message.WELCOME, self.__user_id)
                                sock.send(pickle.dumps(msg)) # serialize

                            # print notice message from the server
                            elif msg_type == Message.NOTICE:
                                print_yellow("[Notice] " + msg.get_msg())

                            # get file list from server
                            elif msg_type == Message.FILE_LIST:
                                print_cyan("The global file list is as follows:")
                                print(msg.get_msg())

                            # other cilent wants my file
                            elif msg_type == Message.GET_FILE:
                                req = msg.get_msg()
                                recver = req.split(":", 1)[0]
                                file_name = req.split(":", 1)[1]
                                try:
                                    file_size = os.path.getsize(file_name)
                                    msg = Message(Message.FILE_SIZE, file_size)
                                    sock.send(pickle.dumps(msg))
                                    time.sleep(0.1)
                                    sock.send(recver.encode())
                                    time.sleep(0.1)
                                    sock.send(file_name.encode())
                                    time.sleep(0.1)
                                    self.send_file(file_name, file_size, sock)
                                except FileNotFoundError:
                                    print_red("Error occurred!")

                            # get error message from server
                            elif msg_type == Message.ERROR:
                                print_red(msg.get_msg())

                        # disconnection error
                        else:
                            self.__socket.close()
                            print_red("Disconnected from server {}".format(self.__host_addr))
                            sys.exit(0)

                    # read message from the stdin
                    else:
                        try:
                            user_input = sys.stdin.readline().rstrip()
                            user_input = int(user_input)
                        except Exception as e:
                            print_red("Wrong input")
                        if isinstance(user_input, int):
                            
                            # print the menu
                            if user_input == 0:
                                print_purple("=================================")
                                print_purple("1. Register a file.")
                                print_purple("2. Get the global file list.")
                                print_purple("3. Download a file.")
                                print_purple("4. Exit.")
                                print_purple("=================================")
                            
                            # register file to server
                            elif user_input == 1:
                                print_yellow_inline("Which file to register? ")
                                file_name = input()
                                if os.path.isfile(file_name):
                                    msg = Message(Message.REG_FILE, file_name)
                                    self.__socket.send(pickle.dumps(msg)) # serialize
                                else:
                                    print_red("File not found.")
                            
                            # request global file list
                            elif user_input == 2:
                                msg = Message(Message.FILE_LIST, "")
                                self.__socket.send(pickle.dumps(msg))
                            
                            # download file from server
                            elif user_input == 3:
                                print_yellow_inline("Which file to download? ")
                                file_name = input()
                                msg = Message(Message.GET_FILE, file_name)
                                self.__socket.send(pickle.dumps(msg))
                            
                            # terminate connection and exit
                            elif user_input == 4:
                                self.__socket.close()
                                print_green("Notified RelayServer.")
                                print_green("Goodbye!")
                                sys.exit(1)
                            
                            # wrong input
                            else:
                                print_red("Wrong input")
        
        # for softer exit
        except KeyboardInterrupt:
            self.__socket.close()
            print_green("Notified RelayServer.")
            print_green("Goodbye!")
            sys.exit(1)

    # send file to the server
    def send_file(self, file_name, file_size, sock):
        cur_size = 0
        f = open(file_name, "rb")
        while cur_size < file_size:
            data = f.read(2048)
            sock.send(data)
            cur_size += len(data)
        f.close()

    # get file from the server
    def get_file(self, file_name, file_size, sock):
        cur_size = 0
        f = open(file_name, "wb+")
        while cur_size < file_size:
            data = sock.recv(2048)
            f.write(data)
            cur_size += len(data)
        f.close()
        print_yellow(file_name + " has been downloaded.")


if __name__ == "__main__":
    print_yellow_inline("Enter User ID: ")
    user_id = input()
    print_yellow_inline("Enter RelayServer IP address: ")
    ip_addr = input()
    client = RelayClient(user_id, 10080, ip_addr)
    client.init_socket()
    client.start()


