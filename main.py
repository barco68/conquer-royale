import argparse
from threading import Thread
from network.Network import player_net_thread
from graphics.pg.gtypes import graphic_thread


def get_args():
    """
    simple function for organized argument parsing

    :return: the arguments given to the program, by name and value in a namespace
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-l', action='store_true', help='a flag to tell the program the server is on the same device')
    group.add_argument('-addr', help='the IP(v4) address of the server')
    return parser.parse_args()


def main():
    """
    main function for activation of threads
    """
    args = get_args()
    if args.l:
        args.addr = '127.0.0.1'
    gton, ntog = [], []
    nthread = Thread(target=player_net_thread, args=(gton, ntog, args.addr))
    gthread = Thread(target=graphic_thread, args=(ntog, gton))
    nthread.start()
    gthread.start()
    nthread.join()
    gthread.join()
    # currently Main_Separated.py for activating server
    # possible change: main.py for both playing and server


if __name__ == '__main__':
    main()
