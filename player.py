# -*- coding: utf-8 -*-
from easyAI import Human_Player, AI_Player, Negamax, DictTT


class Player(object):
    def __init__(self):
        self.turns = []
        self.force_turn = None
        self.team = 'spectator'
        self.left = False

    def set_team(self, team):
        self.team = team

    def get_team(self):
        return self.team

    def set_turn(self, coords, small_coords):
        self.turns.append((coords, small_coords))

    def set_force_turn(self, coords):
        'Set coords for next turn, check if last turn was in that cell'
        last_turn = self.get_last_turn()
        if last_turn and last_turn[0] == coords:
            self.force_turn = None
            return

        self.force_turn = coords

    def get_force_turn(self):
        return self.force_turn

    def get_last_turn(self):
        if not self.turns:
            return None
        return self.turns[-1]

    def undo_turn(self):
        self.turns = self.turns[:-1]

    def is_left(self):
        return self.left

    def leave(self):
        self.left = True

    def rejoin(self):
        self.left = False

    def is_bot(self):
        return isinstance(self, AI_Player)

    def __bool__(self):
        return not self.is_left()


class HumanPlayer(Human_Player, Player):
    def __init__(self):
        Human_Player.__init__(self)
        Player.__init__(self)
        self.moves = []

    def ask_move(self, game):
        if self.moves:
            print 'move poped'
            return self.moves.pop()

    def put_move(self, move):
        print 'move arrived'
        self.moves.append(move)


class AIPlayer(AI_Player, Player):
    def __init__(self):
        self.table = DictTT()
        self.algo = Negamax(
            4,
            win_score=1000,
            tt=self.table
        )
        AI_Player.__init__(self, self.algo)
        Player.__init__(self)
