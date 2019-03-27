import asyncore
import threading

from network.ntypes import AsyncServer, AsyncClient


def calc_time(since, until):
    """
    simple function to calculate time passage

    :param since: the start of the moment
    :type since: time.struct_time
    :param until: the end of the moment
    :type until: time.struct_time
    :return: the length of the calculated moment in seconds
    :rtype: int or long
    """
    years = until[0] - since[0]
    months = until[1] - since[1]
    days = until[2] - since[2]
    hours = until[3] - since[3]
    minutes = until[4] - since[4]
    seconds = until[5] - since[5]
    result = seconds + minutes * 60 + hours * 3600 + days * 86400 + months * 2592000 + years * 946080000
    return result


def data_thread(queue):
    """
    deprecated
    simple thread for interactive input

    :param queue: the object for transferring the data to the network thread
    :type queue: list
    """
    message = ''
    while not message.lower() == 'exit':
        message = raw_input("Enter massage:\n")
        queue.append(message)


def net_thread(name, host, port, instream, outstream):
    """
    simple thread for communicating with the server

    :param name: name of the player
    :type name: str
    :param host: the IP(v4) address of the server
    :type host: str
    :param port: the port on which the server is listening
    :type port: int
    :param instream: object collecting the data to send to the server
    :type instream: list
    :param outstream: object for distributing the data collected from the server
    :type outstream: list
    """
    play = AsyncClient(name, host, port, instream, outstream)

    asyncore.loop()


def server():
    """
    thread function to run the server
    """
    # current maximum of players per game
    # possible change: operator determine the number of players
    MAX_PLAYERS = 2

    serv = AsyncServer(MAX_PLAYERS)
    # basic show of server location
    print serv.address

    asyncore.loop()


def player(name, address, port):
    """
    deprecated
    simple thread for checking server stability

    :param name: name of the user
    :type name: str
    :param address: the IP(v4) of the server
    :type address: str
    :param port: the port on which the server is listening
    :type port: int
    """
    stream = []
    net = threading.Thread(target=net_thread, args=(name, address, port, stream, stream))
    data = threading.Thread(target=data_thread, args=(stream,))
    net.start()
    data.start()
    net.join()
    data.join()
