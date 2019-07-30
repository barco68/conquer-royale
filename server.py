import argparse
from network import Network


def get_args():
    """
    simple function for organized argument parsing

    :return: the arguments given to the program, by name and value in a namespace
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-mp', type=int, required=True, help='max players for the game')
    return parser.parse_args()


def main():
    """
    the activated function of the server program
    """
    args = get_args()
    Network.server(args.mp)


if __name__ == '__main__':
    main()
