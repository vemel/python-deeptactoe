# -*- coding: utf-8 -*-
from game import Game
from player import HumanPlayer, AIPlayer


class GameRoom(object):
    needed_players = 2
    teams = ["x", "o"]

    def __init__(self, name):
        self.game = None
        self.players = []
        self.player_teams = {}
        for team in self.teams:
            self.player_teams[team] = None
        self.name = name

    def join_ai(self):
        if self.name.startswith('ai'):
            self.join(AIPlayer())

    def is_full(self):
        'True is all game players are here.'
        for player in self.get_players():
            if player is None or player.is_left():
                return False
        return True

    def join(self, player):
        'Add player and assign its team'
        if self.is_full():
            return
        if player in self.players:
            return

        self.players.append(player)

        for team in self.teams:
            if self.player_teams[team] is None:
                player.set_team(team)
                break

        self.player_teams[player.get_team()] = player
        if self.game:
            self.game.reset_players(self.players)

        self.join_ai()

    def get_player_by_team(self, team):
        for player in self.players:
            if player.team == team:
                return player

    def get_players(self):
        'List all players as the should be in Game'
        return [self.player_teams[team] for team in self.teams]

    def leave(self, player):
        player.leave()

    def get_left_player(self):
        'Get vacant player if any'
        for player in self.players:
            if player.is_left():
                return player

    def get_game(self):
        'Players are here, let\'s rock'
        if not self.game:
            self.game = Game(self.players)
        else:
            self.game.reset_players()

        return self.game

    def get_player(self):
        'Get new player or vacant player if any'
        player = self.get_left_player()
        if player is None:
            return HumanPlayer()

        player.rejoin()
        return player
