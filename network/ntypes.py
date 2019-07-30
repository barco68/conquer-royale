import socket
import struct
from errno import EWOULDBLOCK, ECONNRESET, ENOTCONN, ESHUTDOWN, EINTR, EBADF, ECONNABORTED, EPIPE, EAGAIN, ECONNREFUSED

TRY_AGAIN = [EINTR, EAGAIN]
CLOSED = (ECONNRESET, ENOTCONN, ESHUTDOWN, ECONNABORTED, EPIPE, EBADF, ECONNREFUSED)
CHUNK = 4096
FORMAT = struct.Struct('!ic3f')


class AsyncServer(object):
    """main Server object. used to manage new connections and data structures"""

    def __init__(self):
        """
        create a new server object
        """
        super(AsyncServer, self).__init__()
        self._data_organizer = ({}, [])
        self._teams = ['r', 'b']
        self.closed = False
        self._sock = None

    def clear(self):
        """
        clear bullet and mobs data
        """
        self._data_organizer[1][:] = []

    def pick_team(self):
        """
        equal team selection for new players

        :return: the team char
        :rtype: str
        """
        team = self._teams.pop(0)
        self._teams.append(team)
        return team

    def init(self, port=50527):
        """
        open the service of the server

        :param port: the port on which the server is listening
        :type port: int
        """
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.setblocking(0)
        self._sock.bind(('0.0.0.0', port))
        print socket.gethostbyname(socket.gethostname()), port
        self._sock.listen(5)

    def accept(self):
        """
        accept new connection and apply a handler to handle that connection
        """
        try:
            conn, addr = self._sock.accept()
            return AsyncHandler(conn, self._data_organizer)
        except socket.error as e:
            if not e[0] in TRY_AGAIN + [EWOULDBLOCK]:
                raise

    def close(self):
        """
        close the listening for new connections
        """
        self.closed = True
        try:
            self._sock.close()
        except socket.error as e:
            if not e[0] in CLOSED:
                raise

    def fileno(self):
        """
        get the file descriptor of the socket

        :return: file descriptor for the socket
        :rtype: int
        """
        return self._sock.fileno()


class AsyncHandler(object):
    """Handler for single connection to a player."""

    def __init__(self, sock, organizer):
        """
        create a new handler

        :param sock: the connection socket
        :type sock: socket.socket
        :param organizer: the data container of the server
        :type organizer: tuple[dict[int, tuple[str, int, int, float]], list[tuple[int, str, int, int, float]]
        """
        super(AsyncHandler, self).__init__()
        self._sock = sock
        self._data_organizer = organizer
        self.closed = False

    def receive(self):
        """
        receiving data from connection function
        """
        try:
            datalen, packeddata = recv_with_header(self._sock)
        except socket.error as e:
            if e[0] in CLOSED:
                self.close()
                return
            elif e[0] not in TRY_AGAIN + [EWOULDBLOCK]:
                raise
        for i in xrange(datalen):
            try:
                datapart = FORMAT.unpack(packeddata[i * FORMAT.size:(i + 1) * FORMAT.size])
                if datapart[0] > 0:
                    self._data_organizer[0][datapart[0]] = datapart[1:]
                else:
                    self._data_organizer[1].append(datapart)
            except struct.error:
                continue

    def send(self, data=None):
        """
        sending data to the connection function

        :param data: optional, if exist, send it instead of what is in the data organizer
        :type data: tuple[int, str, int, int, float] or None
        """
        alldata = []
        if data:
            alldata.append(data)
            self._data_organizer[0][data[0]] = data[1:]
        else:
            for ident in self._data_organizer[0]:
                alldata.append((ident,) + self._data_organizer[0][ident])
            alldata.extend(self._data_organizer[1])
        try:
            send_with_header(self._sock, alldata)
        except socket.error as e:
            if e[0] in CLOSED:
                self.close()
            elif e[0] not in TRY_AGAIN + [EWOULDBLOCK]:
                raise

    def close(self):
        """
        close the connection
        """
        self.closed = True
        try:
            self._sock.close()
        except socket.error as e:
            if not e[0] in CLOSED:
                raise

    def fileno(self):
        """
        get the file descriptor of the connection

        :return: file descriptor for the connection
        :rtype: int
        """
        return self._sock.fileno()

    def check_errors(self):
        """
        check for errors in the socket
        needed to differ between OOB messages and actual errors
        captured by select.select

        :return: the error code of the latest error in the socket
        :rtype: int
        """
        return self._sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)


class AsyncClient(object):
    """Client object."""

    def __init__(self, in_obj, out_obj):
        """
        create a client

        :param in_obj: the object providing the data to send to the server
        :type in_obj: list[tuple[int, str, int, int, float]]
        :param out_obj: the object to write the data from the server to him
        :type out_obj: list[tuple[int, str, int, int, float]]
        """
        super(AsyncClient, self).__init__()
        self._in = in_obj
        self._out = out_obj
        self.closed = False
        self._sock = None

    def connect(self, host, port=50527):
        """
        connect to the game server

        :param host: the server IP(v4) address
        :type host: str
        :param port: the port were the server listen
        :type port: int
        """
        self._sock = socket.create_connection((host, port))
        self._sock.setblocking(1)

    def receive(self):
        """
        receive data from the server and move it to out_obj
        """
        try:
            datalen, packeddata = recv_with_header(self._sock)
        except socket.error as e:
            if e[0] in CLOSED:
                self.close()
                return
            raise
        for i in xrange(datalen):
            try:
                datapart = FORMAT.unpack(packeddata[i * FORMAT.size:(i + 1) * FORMAT.size])
                if datapart[0] > 0:
                    try:
                        self._out[datapart[0] - 1] = datapart
                    except IndexError:
                        self._out.append(datapart)
                else:
                    self._out.append(datapart)
            except struct.error:
                continue

    def send(self):
        """
        send to the server the data in in_obj
        """
        flag = False
        for part in self._in:
            flag |= 'e' in part
        send_with_header(self._sock, self._in)
        if flag:
            self.close()

    def close(self):
        """
        close the connection to the server
        """
        self.closed = True
        try:
            self._sock.close()
        except socket.error as e:
            if not e[0] in CLOSED:
                raise


def send_with_header(sock, data):
    """
    global function to send data by protocol

    :param sock: the socket of the connection to send over the data
    :type sock: socket.socket
    :param data: the data to be sent
    :type data: list[tuple[int, str, int, int, float]]
    """
    datalen = struct.pack('!i', len(data))
    to_send = ''
    for part in data:
        to_send += FORMAT.pack(*part)
    to_send = datalen + to_send + 'END'
    while to_send:
        sent = sock.send(to_send)
        to_send = to_send[sent:]


def recv_with_header(sock):
    """
    global function for receiving data from connection by protocol

    :param sock: the socket of the connection
    :type sock: socket.socket
    :return: the number of data parts received and the packed string of the data parts
    :rtype: (int, str)
    """
    strdata = ''
    while 'END' not in strdata:
        strdata += sock.recv(CHUNK)
    data = strdata.split('END')
    try:
        datalen = struct.unpack('!i', data[0][:4])[0]
    except struct.error:
        return 0, ''
    packeddata = data[0][4:]
    return datalen, packeddata
