from threading import Thread
from network.Network import net_thread
from graphics.pg.gtypes import graphic_thread
from argparse import ArgumentParser


def get_args():
    parser = ArgumentParser()
    parser.add_argument('-p', type=int)
    return parser.parse_args()


def main():
    # args = get_args()
    gton, ntog = [], []
    nthread = Thread(target=net_thread, args=('bla', '127.0.0.1', 50527, gton, ntog))
    gthread = Thread(target=graphic_thread, args=(ntog, gton))
    nthread.start()
    gthread.start()
    nthread.join()
    gthread.join()


if __name__ == '__main__':
    main()
