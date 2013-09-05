# -*- coding: utf-8 -*-
from collections import Counter

# TODO: all public funcs shold accept tuple(x, y) except x, y
class Board(object):
    def __init__(self, size_x, size_y):
        self.size_x = size_x
        self.size_y = size_y

        self.fields = [[None for x in range(size_x)] for y in range(size_y)]
        self.owner = None
        self.win_coords = None

    def is_field_empty(self, coords):
        x, y = coords
        return self.fields[y][x] is None

    def is_captured(self):
        return self.owner

    def set_field(self, coords, player=None):
        x, y = coords
        self.fields[y][x] = player

    def get_field(self, coords):
        x, y = coords
        return self.fields[y][x]

    def __iter__(self):
        return self.fields

    def iter_coords(self):
        for x in range(self.size_x):
            for y in range(self.size_y):
                yield (x, y)

    def is_full(self):
        for x, y in self.iter_coords():
            if self.is_field_empty((x, y)):
                return False

        return True

    def iter_lines(self):
        'Iter all lines to check. Nice func, use it.'
        coords = [(x, y) for x, y in self.iter_coords()]
        for x_line in range(self.size_x):
            yield filter(lambda coords: coords[0] == x_line, coords)

        for y_line in range(self.size_x):
            yield filter(lambda coords: coords[1] == y_line, coords)

        yield filter(lambda coords: coords[0] == coords[1], coords)
        yield filter(lambda coords: coords[0] == self.size_y - 1 - coords[1], coords)

    def check_captured(self):
        'Return board owner if there is one, check if board was captured right now.'
        if self.owner:
            return self.owner

        owner = self._check_captured()

        if owner:
            self.owner = owner

        return owner

    def _check_captured(self):
        'Check if there\'s three-in-a-row or domination'
        for line_coords in self.iter_lines():
            if self.is_field_empty(line_coords[0]):
                continue

            value = self.get_field(line_coords[0])
            for cell_coords in line_coords[1:]:
                if self.get_field(cell_coords) != value:
                    break
            else:
                self.win_coords = (line_coords[0], line_coords[-1])
                return value

        if self.is_full():
            values = [self.get_field((x, y)) for x, y in self.iter_coords()]
            counter = Counter(values).items()
            counter.sort(key=lambda x: x[1])
            return counter[0][0]

    def get_data(self):
        return [[value and value.get_team() or '' for value in row] for row in self.fields]

    def get_data_win(self):
        'Get owner and win line.'
        if not self.is_captured():
            return None
        return [self.owner.get_team(), self.win_coords]