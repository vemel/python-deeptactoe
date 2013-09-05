# -*- coding: utf-8 -*-
from gevent import monkey
from socketio.namespace import BaseNamespace
from socketio.mixins import RoomsMixin, BroadcastMixin

from server import app
from player import Player
from room import GameRoom

monkey.patch_all()


class GameNamespace(BaseNamespace, RoomsMixin, BroadcastMixin):
    needed_players = 2
    rooms = {}
    metarooms = ["main"]

    def initialize(self):
        self.logger = app.logger
        self.warn("Socketio session started")

    def warn(self, message):
        self.logger.warn("socket[{0}] {1}".format(self.socket.sessid, message))

    def send_game_started(self, room, send_to=None):
        if send_to is None:
            send_to = [
                socket
                for sessid, socket in self.socket.server.sockets.iteritems()]
        else:
            send_to = [send_to]
        for socket in send_to:
            if not 'room' in socket.session:
                continue
            if not socket.session['room'] == room:
                continue
            data = room.game.get_data()
            data["team"] = socket.session['player'].get_team()
            data["room_name"] = room.name
            pkt = dict(
                type='event',
                name='gameStarted',
                args=data,
                endpoint=self.ns_name)
            socket.send_packet(pkt)

    def get_available_room(self, room_name):
        # get room with this name, join as spectator if full
        if room_name not in self.metarooms:
            if room_name not in self.rooms:
                self.rooms[room_name] = GameRoom(room_name)
            return self.rooms[room_name]

        # get first not full metaroom or create it
        i = 0
        room = None
        while room is None or room.is_full():
            new_room_name = "%s_%s" % (room_name, i)
            if new_room_name not in self.rooms:
                self.rooms[new_room_name] = GameRoom(new_room_name)

            room = self.rooms[new_room_name]
            i += 1
        return room

    # TODO: rejoin players after disconnect and send them game data
    def on_join(self, room_name='main'):
        'New player: disconnect if needed, join it to room, rejoin in future'
        if 'room' in self.socket.session:
            self.warn('non-pure leave: %s' % self.socket.session)
            room = self.socket.session['room']
            player = self.socket.session['player']
            room.leave(player)
            self.emit_to_room(room.name, 'opponentLeft', [])

        if room_name not in self.rooms:
            self.rooms[room_name] = GameRoom(room_name)

        room = self.get_available_room(room_name)
        self.join(room.name)

        if not room.is_full():
            player = room.get_player()
            room.join(player)

            self.socket.session['room'] = room
            self.socket.session['player'] = player

            if room.is_full():
                room.get_game()

                for sessid, socket in self.socket.server.sockets.iteritems():
                    self.send_game_started(room, socket)
            else:
                self.emit_to_room(room.name, 'waitingForOpponent', [])
        else:
            player = Player()
            self.socket.session['room'] = room
            self.socket.session['player'] = player
            self.send_game_started(room, self.socket)

    def on_turn(self, coords):
        'Change game state, send it to all except sender (client do the rest)'
        room = self.socket.session['room']
        player = self.socket.session['player']

        room.game.turn(
            player, (coords["x"], coords["y"]), (coords["x1"], coords["y1"]))
        self.emit_to_room_not_me(
            room.name, 'gameStateChanged', room.game.get_data())

    def recv_connect(self):
        pass

    def recv_disconnect(self):
        'Player has left, let\'s spread the word'
        self.warn('pure leave: %s' % self.socket.session)
        if 'room' in self.socket.session:
            room = self.socket.session['room']
            room.leave(self.socket.session['player'])
            self.emit_to_room(room.name, 'opponentLeft', [])
        self.disconnect(silent=True)

    def emit_to_room_not_me(self, room, event, *args):
        "Sent to all in the room except current socket (in this Namespace)"
        pkt = dict(type="event",
                   name=event,
                   args=args,
                   endpoint=self.ns_name)
        room_name = self._get_room_name(room)
        for sessid, socket in self.socket.server.sockets.iteritems():
            if 'rooms' not in socket.session:
                continue
            if socket is self.socket:
                continue
            if room_name in socket.session['rooms'] and self.socket != socket:
                socket.send_packet(pkt)
