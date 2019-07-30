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


def player_net_thread(instream, outstream, host):
    """
    simple thread for communicating with the server

    :param instream: object collecting the data to send to the server
    :type instream: list
    :param outstream: object for distributing the data collected from the server
    :type outstream: list
    :param host: the address of the server
    :type host: str
    """
    import socket
    from network.ntypes import AsyncClient
    port = 50527
    play = AsyncClient(instream, outstream)
    play.connect(host, port)
    while not play.closed:
        try:
            play.receive()
            play.send()
        except socket.error:
            play.close()


def server(max_players):
    """
    server operations function

    :param max_players: the maximum number of players to play together
    :type max_players: int
    """
    import time
    import select
    from errno import EINTR
    from random import randint
    from network.ntypes import AsyncServer
    serv = AsyncServer()
    serv.init()
    connections = {serv.fileno(): serv}
    start_time = time.gmtime()
    while connections:
        serv.clear()
        write = connections.keys()
        if serv in connections.values():
            write.remove(serv.fileno())
        try:
            read, write, expt = select.select(connections.keys(), write, connections.keys(), 30)
        except select.error as e:
            if e[0] == EINTR:
                continue
            else:
                raise
        for fd in read:
            if connections[fd] is serv:
                if len(connections) - 1 < max_players:
                    new_player = serv.accept()
                    new_player.send((len(connections), serv.pick_team(), randint(0, 1500), randint(0, 1500), 0))
                    connections[new_player.fileno()] = new_player
                if calc_time(start_time, time.gmtime()) > 60:
                    serv.close()
            else:
                connections[fd].receive()
        for fd in write:
            connections[fd].send()
        for fd in expt:
            if connections[fd] is server or connections[fd].check_errors():
                connections[fd].close()
        for fd in connections.keys():
            if connections[fd].closed:
                del connections[fd]
        time.sleep(0.01)
