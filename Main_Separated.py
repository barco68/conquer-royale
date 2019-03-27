import argparse

import graphics.pg.gtypes
from network import Network


def get_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    player_parser = subparsers.add_parser('player')
    player_parser.add_argument('-n', help='your nickname', required=True)
    addresses = player_parser.add_mutually_exclusive_group(required=True)
    addresses.add_argument('-l', action='store_true', help='specifying that the server is the player\'s computer')
    addresses.add_argument('-addr', help='specifying the address of the server (IPv4 only)')
    player_parser.add_argument('-p', type=int, help='specifying the port of the server', required=True)
    server = subparsers.add_parser('server')
    server.add_argument("-f", required=False, default="server", help='ignore')
    subparsers.add_parser('graphics')
    return parser.parse_args()


def main():
    args = get_args()
    if not vars(args):
        game = graphics.pg.gtypes.Engine([((50, 50), 'blue', 1)], [])
        game.run()
    else:
        try:
            if args.l:
                Network.player(args.n, '127.0.0.1', args.p)
            else:
                Network.player(args.n, args.addr, args.p)
        except AttributeError:
            Network.server()


if __name__ == '__main__':
    main()
