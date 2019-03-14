import asyncore
# import socket
# import time
import threading

from network.ntypes import AsyncServer, AsyncClient


def calc_time(since, until):
    years = until[0] - since[0]
    months = until[1] - since[1]
    days = until[2] - since[2]
    hours = until[3] - since[3]
    minutes = until[4] - since[4]
    seconds = until[5] - since[5]
    result = seconds + minutes * 60 + hours * 3600 + days * 86400 + months * 2592000 + years * 946080000
    return result


def data_thread(queue):
    message = ''
    while not message.lower() == 'exit':
        message = raw_input("Enter massage:\n")
        queue.append(message)


def net_thread(name, host, port, instream, outstream):

    play = AsyncClient(name, host, port, instream, outstream)

    asyncore.loop()


def server():

    MAX_PLAYERS = 2

    serv = AsyncServer(MAX_PLAYERS)
    print serv.address

    asyncore.loop()


def player(name, address, port):

    stream = []
    net = threading.Thread(target=net_thread, args=(name, address, port, stream, stream))
    data = threading.Thread(target=data_thread, args=(stream,))
    net.start()
    data.start()
    net.join()
    data.join()
