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
        self._last = ['r', 'b']
        self.bind(('0.0.0.0', 50527))
        self.set_reuse_addr()
        self.address = socket.gethostbyname(socket.gethostname()), self.socket.getsockname()[1]
        self.listen(max_players)

    def pick_team(self):
        # current more or less fair selection of teams
        # future: players decide their team
        team = self._last.pop(0)
        self._last.append(team)
        return team

    def handle_accept(self):
        if len(self._curr_players) < self._max_players:
            ret = self.accept()
            if ret is not None:
                ret[0].setblocking(1)
                name = ret[0].recv(CHUNK)
                text = (len(self._curr_players)+1, self.pick_team(), (randint(0, 1500),  randint(0, 1500)))
                ret[0].send(str(text))
                self._curr_players.append(AsyncHandler(ret[0], name, self._data_organizer))
        if len(self._curr_players) == self._max_players:
            # currently one game per running
            self.handle_close()

    def handle_close(self):
        self.close()


class AsyncHandler(asyncore.dispatcher):
    def __init__(self, sock, name, organizer):
        asyncore.dispatcher.__init__(self, sock=sock)
        self._data_organizer = organizer
        self._name = name

    def handle_write(self):
        if not self._data_organizer:
            return
        data = str(self._data_organizer)
        sent = self.send(data)
        data = data[sent:]
        while data:
            sent = self.send(data)
            data = data[sent:]

    def handle_read(self):
        strdata = self.recv(CHUNK)
        if not strdata:
            return
        try:
            data = ast.literal_eval(strdata)
        except Exception as e:
            print strdata
            raise
        if strdata.find('exit') > -1:
            self.handle_expt()
        else:
            if len(self._data_organizer) > data[0]-1:
                self._data_organizer.sort(key=lambda x: x[0])
                del self._data_organizer[data[0]-1]
            self._data_organizer.append(data)

    def handle_expt(self):
        self._data_organizer.append('player %s have disconnected' % self._name)
        self.handle_close()

    def handle_close(self):
        self.close()


class AsyncClient(asyncore.dispatcher):
    def __init__(self, name, host, port, dstream, ostream):
        self._data_stream = dstream
        self._output = ostream
        self._name = name
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        # currently immidiate connection in start of game
        self.connect((host, port))

    def handle_write(self):
        if self._data_stream:
            data = self._data_stream.pop(0)
            flag = data[1].lower() == 'exit'
            data = '{}'.format(data)

            self.send(data)
            if flag:
                self.close()

    def handle_read(self):
        data = self.recv(CHUNK)
        if not data:
            return
        data = data.split(']')
        data = filter(lambda x: isinstance(x, str) and x.startswith('[') and x.endswith(']'), data)
        for data_part in data:
            if not data_part:
                continue
            data_part += ']'
            try:
                parts = ast.literal_eval(data_part)
                for part in parts:
                    if isinstance(part, str):
                        part = ast.literal_eval(part)
                    if self._output:
                        self._output.sort(key=lambda x: x[0])
                        del self._output[part[0]-1]
                    self._output.append(part)
            except Exception as e:
                print data_part
                print data
                raise

    def handle_close(self):
        self.close()

    def handle_connect(self):
        print 'connected'
        self.socket.setblocking(1)
        self.send(self._name)
        initdata = ast.literal_eval(self.recv(CHUNK))
        self._output.append(initdata)
        self.socket.setblocking(0)
