from socket import *
from threading import *
from time import sleep
from queue import Queue


class DynamicReceiver:
    def __init__(self, port, recv_addr):
        self.__socket = None
        self.__port = port
        self.__recv_addr = recv_addr

    def init_socket(self):
        self.__socket = socket(AF_INET, SOCK_DGRAM)
        self.__socket.bind((self.__recv_addr, self.__port))

    def start(self):
        global income, bottleneck_queue
        global locker

        stat_printer = Thread(target=print_stat)
        ack_sender = Thread(target=self.dequeue_and_ack)
        stat_printer.start()
        ack_sender.start()

        while True:
            try:
                packet, send_addr = self.__socket.recvfrom(1024)
            except ConnectionResetError:
                self.__socket.close()
                self.init_socket()
                continue
            with locker:
                income += 1
                if bottleneck_queue.qsize() == max_qsize:
                    self.send_queue_full(send_addr)
                else:
                    bottleneck_queue.put(send_addr)

    def dequeue_and_ack(self):
        global forwarded, bottleneck_queue
        global locker

        while True:
            with locker:
                if not bottleneck_queue.empty():
                    send_addr = bottleneck_queue.get()
                    forwarded += 1
                    self.send_ack(send_addr)
            sleep(1.0 / bottleneck_rate)

    def send_ack(self, send_addr):
        self.__socket.sendto("ack".encode(), send_addr)
        return

    def send_queue_full(self, send_addr):
        self.__socket.sendto("full".encode(), send_addr)
        return


def print_stat():
    global income, forwarded, bottleneck_queue
    global locker

    while True:
        queue_occupancy = 0
        counter = 0
        while counter < 20:
            with locker:
                queue_occupancy += bottleneck_queue.qsize()
            counter += 1
            sleep(0.1)
        with locker:
            print("\nIncoming rate: {0:0.2f} pps".format(income / 2.0))
            print("Forwarding rate: {0:0.2f} pps".format(forwarded / 2.0))
            print("Average queue occupancy: {0:0.2f} %".format((queue_occupancy / 20) / max_qsize * 100))
            income = 0
            forwarded = 0


income = 0
forwarded = 0
bottleneck_queue = Queue()
bottleneck_rate = float(input("Bottleneck link rate (pps): "))
max_qsize = int(input("Queue size: "))
locker = Lock()

client = DynamicReceiver(10080, "")
client.init_socket()
client.start()
