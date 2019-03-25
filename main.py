from threading import Thread
from network.Network import net_thread
from graphics.pg.gtypes import graphic_thread
from argparse import ArgumentParser


def get_args():
    parser = ArgumentParser()
    parser.add_argument('-p', type=int)
    return parser.parse_args()


def demy_net_thread(gton, ntog):
    flag = True
    while flag:
        echo = gton[:]
        for data in echo:
            if data[0] == 1:
                ntog[0] = data
                try:
                    ntog[1] = (2, chr(ord('b') + ord('r') - ord(data[1])), (1550 - data[2][0], 1550
                                    - data[2][1]),data[3])
                except Exception as e:
                    ntog.append((2, chr(ord('b') + ord('r') - ord(data[1])), (1550 - data[2][0], 1550
                                - data[2][1]),data[3]))
            flag = not data[1] == 'exit'
            # gton.remove(data)
    print ntog[-1]


def main():
    # args = get_args()
    gton, ntog = [], [(1, 'b', (1000, 1000)), (1, 'b', (1000, 1000), 0)]
    gthread = Thread(target=graphic_thread, args=(ntog, gton))
    nthread = Thread(target=demy_net_thread, args=(gton, ntog))
    gthread.start()
    nthread.start()
    gthread.join()
    nthread.join()


if __name__ == '__main__':
    main()
