import asyncore
import socket
import ast
from random import randint

CHUNK = 4096


class AsyncServer(asyncore.dispatcher):

    def __init__(self, max_players):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self._max_players = max_players
        self._data_organizer = []
        self._curr_players = []
        self._last = ['red', 'blue']
        self.bind(('0.0.0.0', 50527))
        self.set_reuse_addr()
        self.address = self.socket.getsockname()
        print socket.gethostbyname(socket.gethostname())
        self.listen(max_players)

    def pick_team(self):
        team = self._last.pop(0)
        self._last.append(team)
        return team

    def handle_accept(self):
        if len(self._curr_players) < self._max_players:
            ret = self.accept()
            if ret is not None:
                print 'got connection'
                ret[0].setblocking(1)
                name = ret[0].recv(CHUNK)
                text = ((randint(0, 1500),  randint(0, 1500)), self.pick_team(), len(self._curr_players)+1)
                ret[0].send(str(text))
                self._curr_players.append(AsyncHandler(ret[0], name, self._data_organizer, len(self._curr_players)))
                for p in self._curr_players:
                    p.inc_check()
            else:
                print 'something went wrong'
        if len(self._curr_players) == self._max_players:
            self.handle_close()

    def handle_close(self):
        self.close()


class AsyncHandler(asyncore.dispatcher):
    def __init__(self, sock, name, organizer, check):
        asyncore.dispatcher.__init__(self, sock=sock)
        # sock.setblocking(1)
        self._data_organizer = organizer
        self._name = name
        self._check = check

    def handle_write(self):
        data = str(self._data_organizer)
        if not self._data_organizer:
            print 'no data received'
            return
        sent = self.send(data)
        data = data[sent:]
        while data:
            sent = self.send(data)
            data = data[sent:]
        self._data_organizer.append(True)
        self._check -= reduce(lambda x, y: x + int(not y == -1),
                              [v.find('disconnected') for v in self._data_organizer if isinstance(v, str)],
                              0)
        if self._data_organizer.count(True) >= self._check:
            for _ in self._data_organizer[:]:
                self._data_organizer.pop()

    def handle_read(self):
        data = self.recv(CHUNK)
        if data.find('exit') > -1:
            self.handle_expt()
        else:
            self._data_organizer.append(data)

    def handle_expt(self):
        self._data_organizer.append('player %s have disconnected' % self._name)
        self.handle_close()

    def handle_close(self):
        self.close()

    def inc_check(self):
        self._check += 1


class AsyncClient(asyncore.dispatcher):
    def __init__(self, name, host, port, dstream, ostream):
        self._data_stream = dstream
        self._output = ostream
        self._name = name
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))

    def handle_write(self):
        if self._data_stream:
            flag = self._data_stream[0][2].lower() == 'exit'
            data = self._data_stream.pop(0)
            data = '{}'.format(data)
            self.send(data)
            if flag:
                self.close()

    def handle_read(self):
        data = self.recv(CHUNK)
        parts = ast.literal_eval(data)
        for part in parts:
            self._output.append(part)
        print data

    def handle_close(self):
        self.close()

    def handle_connect(self):
        print 'connected'
        self.socket.setblocking(1)
        self.send(self._name)
        initdata = self.recv(CHUNK)
        self._output.append(initdata)
