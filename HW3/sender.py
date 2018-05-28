from socket import *
from threading import *
from packet import Packet
import pickle
import math
import os
import time

current_ack = -1
current_packet_num = 0
duplicate_ack_count = 0
window = []  # sent packets will be stored in here
win_locker = Lock()
total_packet = 0
base_time = None


class ReliableSender:

    def __init__(self, port, send_addr, recv_addr, win_size, timeout_val, file_name):
        self.__socket = None
        self.__port = port
        self.__send_addr = send_addr
        self.__recv_addr = recv_addr
        self.__win_size = win_size
        self.__timeout_val = timeout_val
        self.__file_name = file_name

    def init_socket(self):
        self.__socket = socket(AF_INET, SOCK_DGRAM)
        self.__socket.bind((self.__send_addr, 0))

    def manage_ack(self):
        # initialize global variables
        global current_ack
        global current_packet_num
        global duplicate_ack_count
        global window
        global win_locker
        global total_packet
        global base_time

        while current_ack != total_packet - 1:
            ack, _ = self.__socket.recvfrom(1024)
            ack = int(ack.decode())
            print("{0:0.3f} ACK: {1:d} Sender < Receiver".format(
                time.time() - base_time, ack))

            # get expected ACK
            if ack > current_ack:
                current_ack = ack
                with win_locker:
                    for p in window:
                        if p.get_seq_num() <= current_ack:
                            window.remove(p)
                        else:
                            break
                    duplicate_ack_count = 0
            # get duplicate ACK
            else:
                with win_locker:
                    duplicate_ack_count += 1

    def start(self):
        # initialize global variables
        global current_ack
        global current_packet_num
        global duplicate_ack_count
        global window
        global win_locker
        global total_packet
        global base_time

        # calculate total number of packets and then send file name to receiver
        total_packet = int(math.ceil(os.path.getsize(self.__file_name) / 1024))
        f = open(self.__file_name, "rb")
        self.__socket.sendto((self.__file_name + ":" + str(total_packet)).encode(), self.__recv_addr)

        # create ACK receiving thread and initialize starting time
        ack_manager = Thread(target=self.manage_ack, args=())
        ack_manager.start()
        base_time = time.time()

        # repeat until getting ACKed of all packets
        while current_ack != total_packet - 1:
            # send packets according to the window size
            if len(window) < self.__win_size and current_packet_num < total_packet:
                data = f.read(1024)
                packet = Packet(current_packet_num, data, time.time())
                with win_locker:
                    window.append(packet)
                self.__socket.sendto(pickle.dumps(packet), self.__recv_addr)
                print("{0:0.3f} pkt: {1:d} Sender > Receiver".format(
                    time.time() - base_time, current_packet_num))
                current_packet_num += 1

            # if base packet timed out
            with win_locker:
                if len(window) > 0 and time.time() - window[0].get_time() > self.__timeout_val:
                    print("{0:0.3f} pkt: {1:d} | timeout since {2:0.3f}".format(
                        time.time() - base_time, window[0].get_seq_num(), window[0].get_time() - base_time))
                    # retransmit only the lost packet
                    window[0].set_time(time.time())
                    self.__socket.sendto(pickle.dumps(window[0]), self.__recv_addr)
                    print("{0:0.3f} pkt: {1:d} Sender > Receiver (retransmission)".format(
                        time.time() - base_time, window[0].get_seq_num()))

            # if got 3 duplicated ACKs
            with win_locker:
                if len(window) > 0 and duplicate_ack_count >= 3:
                    print("{0:0.3f} pkt: {1:d} | 3 duplicated ACKs".format(
                        time.time() - base_time, window[0].get_seq_num()))
                    # retransmit only the lost packet
                    window[0].set_time(time.time())
                    self.__socket.sendto(pickle.dumps(window[0]), self.__recv_addr)

        # close the file, socket and print the result
        throughput = total_packet / (time.time() - base_time)
        f.close()
        self.__socket.close()
        print("\n{0:s} is successfully transferred.".format(self.__file_name))
        print("Throughput: {0:0.2f} pkts / sec".format(throughput))


if __name__ == "__main__":
    recv_addr = (input("Receiver IP address: "), 10080)
    win_size = int(input("window size: "))
    timeout_val = float(input("timeout (sec): "))
    file_name = input("file name: ")
    print("")
    sender = ReliableSender(0, "", recv_addr, win_size, timeout_val, file_name)
    sender.init_socket()
    sender.start()
