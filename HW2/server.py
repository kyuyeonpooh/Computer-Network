
from socket import *
from select import select
import sys
import time
from message import *
import pickle
from colors import *


class RelayServer:

    def __init__(self, port, host_addr):
        self.__socket = None
        self.__conn_list = []
        self.__user_id_map = {}
        self.__file_list = []
        self.__port = port
        self.__host_addr = host_addr

    # initialize socket
    def init_socket(self):
        self.__socket = socket(AF_INET, SOCK_STREAM)
        self.__socket.bind((self.__host_addr, self.__port))
        self.__socket.listen(20)
        self.__conn_list.append(self.__socket) # add server socket into the list
        print_yellow("RelayServer is ready for port number {}.".format(self.__port))

    # start communicating with clients
    def start(self):
        try:
            while self.__conn_list:
                
                # get list of sockets ready to be used
                read_socket, write_socket, err_socket = select(self.__conn_list, [], [], 10)
                
                # iterate through readable candidates
                for sock in read_socket:
                    
                    # get connection request from the client
                    if sock is self.__socket:
                        client_socket, _ = sock.accept()
                        self.__conn_list.append(client_socket) # add to connection list
                        msg = Message(Message.WELCOME, "")
                        client_socket.send(pickle.dumps(msg)) # serialize
                    
                    # get message from the client
                    else:

                        # get data from the client
                        data = sock.recv(2048)

                        if data:
                            msg = pickle.loads(data)
                            msg_type = msg.get_msg_type()

                            # client starts to send file content
                            if msg_type == Message.FILE_SIZE:
                                file_size = msg.get_msg() # get file size
                                recver = sock.recv(2048).decode() # get receiver's name
                                file_name = sock.recv(2048).decode() # get file name
                                print(recver)
                                print(file_name)
                                recv_soc = None
                                for soc, usr in self.__user_id_map.items(): # find receiver's socket
                                    if usr == recver:
                                        recv_soc = soc
                                        break
                                msg = Message(Message.FILE_SIZE, file_size)
                                recv_soc.send(pickle.dumps(msg))
                                time.sleep(0.1)
                                recv_soc.send(file_name.encode())
                                time.sleep(0.1)
                                self.transfer_file(file_name, file_size, recv_soc, sock)

                            # notify all clients about new user
                            elif msg_type == Message.WELCOME:
                                user_id = msg.get_msg()
                                self.__user_id_map[sock] = user_id # add to user id to map
                                print_green(user_id + " is connected.")
                                self.notify_all("Welcome " + user_id + "!")
                            
                            # client want to register new file
                            elif msg_type == Message.REG_FILE:
                                reg_file = msg.get_msg()
                                user_id = self.__user_id_map[sock]
                                if not user_id + "/" + reg_file in self.__file_list:
                                    self.__file_list.append(user_id + "/" + reg_file)
                                    self.__file_list.sort() # add file to the list and sort them
                                    print_cyan("The global file list is as follows:")
                                    print("  " + "\n  ".join(self.__file_list))
                                    self.notify_all("The global file list is updated.")
                                else:
                                    self.send_error_msg(sock, "File already registered.")
                            
                            # client has requested the file
                            elif msg_type == Message.GET_FILE:
                                file_recver = self.__user_id_map[sock]
                                file_sender = msg.get_msg().split("/", 1)[0]
                                file_name = msg.get_msg().split("/", 1)[1]
                                print_yellow(
                                        "Received the file download request from "
                                        + file_recver + " for " + msg.get_msg())
                                for soc, usr in self.__user_id_map.items(): # find file sender's socket
                                    if usr == file_sender:
                                        msg = Message(Message.GET_FILE, file_recver + ":" + file_name)
                                        soc.send(pickle.dumps(msg))
                                        break

                            # client want global file list
                            elif msg_type == Message.FILE_LIST:
                                file_list = "\n  ".join(self.__file_list)
                                msg = Message(Message.FILE_LIST, "  " + file_list)
                                sock.send(pickle.dumps(msg))

                        # nofity disconnected user
                        else:
                            self.__conn_list.remove(sock)
                            user_left = self.__user_id_map.pop(sock, None)
                            file_list_copied = list(self.__file_list)
                            for f in file_list_copied: # delete file registered by user who just left
                                if f.split("/", 1)[0] == user_left:
                                    self.__file_list.remove(f)
                            print_blue(user_left + " has left.")
                            self.notify_all(user_left + " has left.")
                            print_cyan("The global file list is as follows:") # print file list
                            print("  " + "\n  ".join(self.__file_list))
                            self.notify_all("The global file list is updated.")
                            sock.close()
        
        # for softer exit
        except KeyboardInterrupt:
            self.__socket.close()
            sys.exit(1)
    
    # transfer file to another user
    def transfer_file(self, file_name, file_size, recv_soc, send_soc):
        print_yellow("Retrieved " + file_name + " from " + self.__user_id_map[send_soc])
        cur_size = 0
        while cur_size < file_size:
            data = send_soc.recv(2048)
            recv_soc.send(data)
            cur_size += len(data)
        print_yellow("The transfer of " + file_name + " to " + self.__user_id_map[recv_soc]
                + " has been completed.")
        self.__file_list.append(self.__user_id_map[recv_soc] + "/" + file_name)
        print_cyan("The global file list is as follows:") # print file list
        print("  " + "\n  ".join(self.__file_list))
        self.notify_all("The global file list is updated.")

    # notify all users
    def notify_all(self, msg):
        for each_client in self.__conn_list:
            if each_client is not self.__socket:
                notice = Message(Message.NOTICE, msg)
                each_client.send(pickle.dumps(notice)) # serialize

    # send error message to client
    def send_error_msg(self, sock, err_msg):
        err_msg = Message(Message.ERROR, err_msg)
        sock.send(pickle.dumps(err_msg))


if __name__ == "__main__":
    server = RelayServer(10080, "")
    server.init_socket()
    server.start()

