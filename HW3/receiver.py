from socket import *

import pickle
import time
import random


class ReliableReceiver:

    MAX_RECV_SIZE = 1472

    def __init__(self, port, recv_addr, loss_rate, recv_buf_size):
        self.__socket = None
        self.__port = port
        self.__recv_addr = recv_addr
        self.__loss_rate = loss_rate
        self.__recv_buf_size = recv_buf_size

    def init_socket(self):
        self.__socket = socket(AF_INET, SOCK_DGRAM)
        self.__socket.bind((self.__recv_addr, self.__port))
        if self.__recv_buf_size < 10000000:
            # resize receive buffer size to 10 MB
            self.__socket.setsockopt(SOL_SOCKET, SO_RCVBUF, 1000000)
            print("socket recv buffer size updated: 10000000")

    def start(self):
        while True:
            # receive file name and expected total number of packets
            print("\nThe receiver is ready to receive.")
            while True:
                # ignore received data if it is not file information
                try:
                    file_info, send_addr = self.__socket.recvfrom(self.MAX_RECV_SIZE)
                    file_info = file_info.decode()
                    file_name = file_info.split(":")[0]
                    total_packet = int(file_info.split(":")[1])
                    break
                except UnicodeDecodeError or IndexError:
                    continue
            print("File name is received: {0:s}".format(file_name))
            f = open(file_name, "wb+")

            # receive each packet and write to file
            expected_seq_num = -1
            base_time = time.time()
            while expected_seq_num != total_packet - 1:
                packet, _ = self.__socket.recvfrom(self.MAX_RECV_SIZE)
                packet = pickle.loads(packet)
                seq_num = packet.get_seq_num()

                # save time of receiving packet and print it
                print("{0:0.3f} pkt: {1:d} Receiver < Sender".format(time.time() - base_time, seq_num))

                # first, drop the packet according to the probability
                if random.random() < self.__loss_rate:
                    print("{0:0.3f} pkt: {1:d} | dropped".format(time.time() - base_time, seq_num))
                # second, update ACK number if wanted packet is received
                elif expected_seq_num + 1 == seq_num:
                    f.write(packet.get_file_data())
                    expected_seq_num += 1
                # finally, send ACK to the sender
                if expected_seq_num >= 0:
                    self.__socket.sendto(str(expected_seq_num).encode(), send_addr)
                    print("{0:0.3f} ACK: {1:d} Receiver > Sender".format(time.time() - base_time, expected_seq_num))

            # close the file and print the result
            f.close()
            print("\n{0:s} is successfully transferred.".format(file_name))


if __name__ == "__main__":
    loss_rate = float(input("packet loss probability: "))
    print("")
    recv_buf_size = int(input("socket recv buffer size: "))
    client = ReliableReceiver(10080, "", loss_rate, recv_buf_size)
    client.init_socket()
    client.start()
