from threading import Thread
# from network.Network import net_thread will be needed later
from graphics.pg.gtypes import graphic_thread


def demy_net_thread(gton, ntog):
    """
    a function to simulate network responses

    :param gton: "client"'s input stream
    :type gton: list
    :param ntog: "client"'s output stream
    :type ntog: list
    """
    flag = True
    while flag:
        echo = gton[:]
        for data in echo:
            if data[0] == 1:
                ntog[0] = data
                try:
                    ntog[1] = (2, chr(ord('b') + ord('r') - ord(data[1])), (1550 - data[2][0], 1550
                                                                            - data[2][1]), data[3])
                except IndexError:
                    ntog.append((2, chr(ord('b') + ord('r') - ord(data[1])), (1550 - data[2][0], 1550
                                                                              - data[2][1]), data[3]))
            flag = not data[1] == 'exit'
    print ntog[-1]


def main():
    """
    main function for activation of threads
    """
    gton, ntog = [], [(1, 'b', (1000, 1000)), (1, 'b', (1000, 1000), 0)]
    gthread = Thread(target=graphic_thread, args=(ntog, gton))
    nthread = Thread(target=demy_net_thread, args=(gton, ntog))
    gthread.start()
    nthread.start()
    gthread.join()
    nthread.join()
    # currently Main_Separated.py for activating server
    # possible change: main.py for both playing and server


if __name__ == '__main__':
    main()
