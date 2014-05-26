# -*- coding: utf-8 -*-
import copy
import json
import inspect
import time

from board import Board
from easyAI import TwoPlayersGame
from player import HumanPlayer, AIPlayer


class Game(TwoPlayersGame):
    cells_x = 3
    cells_y = 3

    def __init__(self, players=None):
        self.board = Board(self.cells_x, self.cells_y)
        self.small_boards = {}
        for coords in self.board.iter_coords():
            self.small_boards[coords] = Board(self.cells_x, self.cells_y)

        self.reset_players(players or [])
        self.winner = None
        self.nplayer = 1
        self.data_dumped = None
        self.turns = []
        self.history = []
        self.player_turn = {}
        for player in self.players:
            self.player_turn[player] = []

    def reset_players(self, players):
        self.players = players
        print players
        try:
            players[0].set_team('x')
            players[1].set_team('o')
        except IndexError:
            pass

        self.board.set_players(self.players)
        for coords in self.board.iter_coords():
            self.small_boards[coords].set_players(self.players)

    def get_next_player(self):
        player_index = self.players.index(self.player)
        next_player_index = (player_index + 1) % len(self.players)
        return self.players[next_player_index]

    def set_player(self, player):
        return
        self.player = player

    def get_small_board(self, coords):
        return self.small_boards[coords]

    def is_turn_possible(self, player, coords, small_coords):
        return (coords, small_coords) in self.possible_moves()
        if not self.get_small_board(coords).is_field_empty(small_coords):
            return False

        force_turn_coords = self.get_force_turn(player)
        if not force_turn_coords:
            return True

        if force_turn_coords == coords:
            return True

        return False

    def get_data_start(self):
        'New game state to send'
        return {
            "teams": [player and player.get_team() for player in self.players],
        }

    def get_data_turn(self):
        'Last turn data to send'
        return {
            "last_turn": (
                self.get_last_turn() and
                (self.get_last_turn()[1] + self.get_last_turn()[2])),
        }

    def get_data(self):
        'Full game state to send'
        return {
            "teams": [player and player.get_team() for player in self.players],
            "player": self.player.get_team(),
            "board": self.board.get_data(),
            "small_boards": [[
                self.get_small_board((x, y)).get_data()
                for x in range(self.cells_x)]
                for y in range(self.cells_y)],
            "board_win": self.board.get_data_win(),
            "small_boards_win": [
                self.get_small_board(coords).get_data_win()
                for coords in self.board.iter_coords()],
            "small_boards_lines": [[
                (self.get_small_board((x, y)).get_data_win()
                    and self.get_small_board((x, y)).get_data_win()[1])
                for x in range(self.cells_x)]
                for y in range(self.cells_y)],
            "last_turn": (
                self.get_last_turn() and
                (self.get_last_turn()[1] + self.get_last_turn()[2])),
            "last_turn_player": (
                self.get_last_turn() and self.get_last_turn()[0].get_team()),
        }

    def dump(self):
        return {
            "board": self.board.dump(),
            "small_boards": dict([
                (coords, self.get_small_board(coords).dump())
                for coords in self.board.iter_coords()]),
            "data_dumped": self.data_dumped,
            "winner": self.winner,
            "player": self.player,
            "player_turn": copy.deepcopy(self.player_turn),
        }

    def load(self, data):
        self.board.load(data["board"])
        for coords in self.board.iter_coords():
            self.get_small_board(coords).load(data["small_boards"][coords])
        self.data_dumped = data["data_dumped"]
        self.winner = data["winner"]
        # self.player = data["player"]
        self.player_turn = data["player_turn"]

    def get_possible_coords(self, player):
        'Get all cell coords that player can turn into.'
        result = []

        for coords in self.board.iter_coords():
            force_turn_coords = player.get_force_turn()
            if force_turn_coords and force_turn_coords != coords:
                continue

            small_board = self.get_small_board(coords)
            for small_coords in small_board.iter_coords():
                if small_board.is_field_empty(small_coords):
                    result.append((coords, small_coords))

        return result

    def get_winner(self):
        return self.winner

    def draw_boards(self):
        res = []
        for y in range(self.board.size_y ** 2 + self.board.size_y - 1):
            res.append([])
            res[-1].append('-' * self.board.size_x)
            for x in range(self.board.size_x - 1):
                res[-1].append('|')
                res[-1].append('-' * self.board.size_x)

        for coords in self.board.iter_coords():
            small_board = self.get_small_board(coords)
            for y, line in enumerate(small_board.draw()):
                y_index = coords[1] * (self.board.size_y + 1) + y
                x_index = coords[0] * 2
                res[y_index][x_index] = line

        return [''.join(i) for i in res]

    def turn(self, player, coords, small_coords):
        'All checks, chage cell owner, check if somebody has won.'
        # if player != self.player:
        #     return

        if not self.is_turn_possible(player, coords, small_coords):
            raise ValueError('Impossible turn: %s' % [coords, small_coords, self.possible_moves()])

        player.set_turn(coords, small_coords)
        self.get_small_board(coords).set_field(small_coords, player)
        if self.get_small_board(coords).check_captured():
            if not self.board.get_field(coords):
                self.board.set_field(coords, player)

        self.player_turn[player].append((coords, small_coords))
        winner = self.board.check_captured()
        if winner:
            self.winner = winner
            return True

        return True

    def undo_turn(self, player, coords, small_coords):
        'All checks, chage cell owner, check if somebody has won.'

        self.get_small_board(coords).clear_field(small_coords)
        owner_verified = self.get_small_board(coords).verify_owner()
        if not owner_verified:
            self.board.clear_field(coords)
            self.board.verify_owner()

        self.winner = self.board.check_captured()
        self.player_turn[player].pop()

    def get_last_turn(self, player=None):
        if player is None:
            player = self.get_next_player()
        turns = self.player_turn[player]
        return [player, turns[-1][0], turns[-1][1]] if turns else None

    def win(self):
        # if self.winner:
        #     print self.board.get_data(), self.winner.get_team(), self.board.win_coords
        return True if self.winner else False

    def is_over(self):
        return self.win()

    def show(self):
        print '\n'.join(self.draw_boards())

    def ttentry(self):
        return json.dumps((
            self.board.get_data(),
            self.board.get_data_win(),
            self.possible_moves(),
            self.player.get_team(),
            [[
                [self.get_small_board((x, y)).get_data(), self.get_small_board((x, y)).get_data_win()]
                for x in range(self.cells_x)]
                for y in range(self.cells_y)]
        ))

    def make_move(self, turn_data):
        # print 'make', turn_data, self.player.get_team(), self.possible_moves()
        coords, small_coords = turn_data
        player = self.player
        self.turn(player, coords, small_coords)

    def put_move(self, player, turn_data):
        # print 'make', turn_data, self.player.get_team(), self.possible_moves()
        if player != self.player:
            return False
        self.make_move(turn_data)

    def unmake_move(self, turn_data):
        # print 'unmake', turn_data, self.player.get_team(), self.possible_moves()
        player = self.player
        coords, small_coords = turn_data
        self.undo_turn(player, coords, small_coords)

    def get_score(self, player):
        score = 0
        if self.winner == player:
            score += 1000
        if self.player == player:
            score += 5

        for coords in self.board.iter_coords():
            board_owner = self.small_boards[coords].is_captured()
            if board_owner:
                if player == board_owner:
                    score += 200

        turns = self.possible_moves(player)
        last_turn = self.get_last_turn(player)
        for coords, small_coords in turns:
            if small_coords == (1, 1):
                score += 5

        if last_turn[1] == (1, 1):
            score += 50
        if last_turn[2] == (1, 1):
            score += 20

        if self.get_small_board(last_turn[1]).is_captured():
            score -= 50

        if not self.get_force_turn(player):
            score += 100

        return score

    def scoring(self):
        player = self.player
        opp = self.get_next_player()
        return self.get_score(player) - self.get_score(opp)

    def get_force_turn(self, player):
        player_turn = self.player_turn[player] and self.player_turn[player][-1] or None
        opp = self.get_next_player()
        opp_turn = self.player_turn[opp] and self.player_turn[opp][-1] or None

        if not opp_turn:
            return None

        if player_turn and player_turn[0] == opp_turn[1]:
            return None

        # print player_turn, opp_turn, opp_turn[1]
        return opp_turn[1]

    def possible_moves(self, player=None):
        'Get all cell coords that player can turn into.'
        result = []
        force_turn = False
        if player is None:
            player = self.player

        force_turn_coords = self.get_force_turn(player)
        if force_turn_coords:
            small_board = self.get_small_board(force_turn_coords)
            if not small_board.is_full():
                force_turn = True

        for coords in self.board.iter_coords():
            if force_turn and force_turn_coords != coords:
                continue

            small_board = self.get_small_board(coords)
            for small_coords in small_board.iter_coords():
                if small_board.is_field_empty(small_coords):
                    result.append((coords, small_coords))

        return result

        def play(self):
            self.history = []

            for self.nmove in range(100):
                
                if self.is_over():
                    break
                
                move = self.player.ask_move(self)
                history.append((deepcopy(self), move))
                self.make_move(move)
                
                if verbose:
                    print( "\nMove #%d: player %d plays %s :"%(
                                 self.nmove, self.nplayer, str(move)) )
                    self.show()
                    
                self.switch_player()
            
            history.append(deepcopy(self))
            
            return history

    def play_step(self, move=None):
        if self.is_over():
            return

        if move is None:
            move = self.player.ask_move(self)

        self.history.append((copy.deepcopy(self), move))
        self.make_move(move)

        # print("\nMove #%d: player %d plays %s :" % (
        #     self.nmove, self.nplayer, str(move)))
        self.show()
        self.switch_player()

        if self.player.is_bot():
            self.play_step()


if __name__ == "__main__":
    from room import GameRoom
    from player import Player
    room = GameRoom('test')
    player1 = Player()
    player2 = Player()
    room.join(player1)
    room.join(player2)
    game = Game([AIPlayer(), AIPlayer()])
    game.play_step()

    # print game.get_data()
    print '\n'.join(game.board.draw())
    print '\n'.join(game.draw_boards())
    print game.winner.get_team()
