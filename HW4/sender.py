from socket import *
from threading import *
from time import sleep
from random import randint
import sys


class DynamicSender:
    def __init__(self, _port, _send_addr, _recv_addr):
        self.__socket = None
        self.__port = _port
        self.__send_addr = _send_addr
        self.__recv_addr = _recv_addr

    def init_socket(self):
        self.__socket = socket(AF_INET, SOCK_DGRAM)
        self.__socket.bind((self.__send_addr, self.__port))

    def manage_ack(self):
        global sending_rate, ack_counter
        global locker

        while True:
            ack, _ = self.__socket.recvfrom(1024)
            ack = ack.decode()
            with locker:
                if ack == "ack":
                    ack_counter += 1
                    sending_rate = sending_rate + (1 / sending_rate) ** 1.5
                elif ack == "full":
                    sending_rate *= 0.5

    def start(self):
        global sending_rate, packet_counter
        global locker

        stat_printer = Thread(target=print_stat)
        ack_manager = Thread(target=self.manage_ack)
        stat_printer.start()
        ack_manager.start()

        packet = ""
        while sys.getsizeof(packet) < 1000:
            packet += "0"
        while True:
            with locker:
                self.__socket.sendto(packet.encode(), self.__recv_addr)
                packet_counter += 1
            sleep(1.0 / sending_rate)


def print_stat():
    global packet_counter, ack_counter
    global locker

    while True:
        with locker:
            curr_sending_rate = packet_counter / 2.0
            if curr_sending_rate != 0:
                curr_goodput = ack_counter / 2.0
                print("\nSending rate: {0:0.2f} pps".format(curr_sending_rate))
                print("Goodput: {0:0.2f} aps".format(curr_goodput))
                print("Goodput ratio: {0:0.2f}".format(curr_goodput / curr_sending_rate))
            packet_counter = 0
            ack_counter = 0
        sleep(2.0)


recv_addr = (input("Receiver IP address: "), 10080)
sending_rate = float(input("Initial sending rate (pps): "))
packet_counter = 0
ack_counter = 0
locker = Lock()

sender = DynamicSender(randint(11000, 12000), "", recv_addr)
sender.init_socket()
sender.start()
