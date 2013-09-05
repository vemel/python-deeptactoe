# -*- coding: utf-8 -*-
from board import Board


class Game(object):
    cells_x = 3
    cells_y = 3

    def __init__(self, room):
        self.room = room
        self.reset_players()
        self.active_player = self.players[0]
        self.winner = None
        self.last_turn = None

        self.board = Board(self.cells_x, self.cells_y)
        self.small_boards = {}
        for coords in self.board.iter_coords():
            self.small_boards[coords] = Board(self.cells_x, self.cells_y)

    def reset_players(self):
        self.players = self.room.get_players()

    def get_next_player(self):
        player_index = self.players.index(self.active_player)
        next_player_index = (player_index + 1) % len(self.players)
        return self.players[next_player_index]

    def set_active_player(self, player):
        self.active_player = player

    def get_small_board(self, coords):
        return self.small_boards[coords]

    def is_turn_possible(self, player, coords, small_coords):
        if not self.get_small_board(coords).is_field_empty(small_coords):
            return False

        force_turn_coords = player.get_force_turn()
        if force_turn_coords is None:
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
            "active_player": self.active_player.get_team(),
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

    def get_winner(self):
        return self.winner

    def turn(self, player, coords, small_coords):
        'All checks, chage cell owner, check if somebody has won.'
        if player != self.active_player:
            return

        if not self.is_turn_possible(player, coords, small_coords):
            return

        # print player.get_team(), coords, small_coords

        player.set_turn(coords, small_coords)
        self.get_small_board(coords).set_field(small_coords, player)
        if self.get_small_board(coords).check_captured():
            self.board.set_field(coords, player)

        winner = self.board.check_captured()
        if winner:
            self.winner = winner
            return True

        next_player = self.get_next_player()
        next_player.set_force_turn(small_coords)
        self.set_active_player(next_player)
        self.last_turn = [player, coords, small_coords]
        return True

    def get_last_turn(self):
        return self.last_turn


if __name__ == "__main__":
    from room import GameRoom
    from player import Player
    room = GameRoom('test')
    player1 = Player()
    player2 = Player()
    room.join(player1)
    room.join(player2)
    game = Game(room)
    game.turn(player1, (1, 1), (1, 1))
    game.turn(player2, (1, 1), (1, 2))
    game.turn(player1, (1, 2), (1, 1))
    game.turn(player1, (2, 2), (1, 1))  # False
    game.turn(player2, (0, 0), (2, 2))
    game.turn(player1, (2, 2), (1, 1))
    game.turn(player1, (2, 2), (2, 1))  # False
    game.turn(player2, (1, 1), (0, 2))
    game.turn(player1, (0, 2), (1, 1))
    game.turn(player2, (1, 1), (2, 2))
    print game.get_data()
