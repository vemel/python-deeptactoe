# -*- coding: utf-8 -*-
import copy


class Counter(object):
    def __init__(self, iterable):
        self.d = {}
        for i in iterable:
            if i not in self.d:
                self.d[i] = 0
            self.d[i] += 1

    def items(self):
        return self.d.items()

    def get_best(self):
        l = self.d.items()
        l.sort(key=lambda x: x[1])
        return l[-1][0]


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

    def draw(self):
        res = []
        for y in range(self.size_y):
            res.append([])
            for x in range(self.size_x):
                val = self.get_field((x, y))
                val = val.get_team() if val else ' '
                res[-1].append(val)

        return [''.join(i) for i in res]

    def is_captured(self):
        return self.owner

    def set_field(self, coords, player=None):
        x, y = coords
        if self.fields[y][x]:
            raise TypeError('Field %s is filled with %s' % (coords, self.fields[y][x]))
        self.fields[y][x] = player

    def clear_field(self, coords):
        x, y = coords
        if not self.fields[y][x]:
            raise TypeError('Field %s is empty' % (coords, ))
        self.fields[y][x] = None

    def verify_owner(self):
        if not self.is_captured():
            return True

        owner = self._check_captured()
        if not owner:
            self.owner = None
            return False

        return True

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

            value = self.get_field(line_coords[0]).get_team()
            for cell_coords in line_coords[1:]:
                if self.is_field_empty(cell_coords):
                    break
                if self.get_field(cell_coords).get_team() != value:
                    break
            else:
                self.win_coords = (line_coords[0], line_coords[-1])
                return self.get_field(line_coords[0])

        if self.is_full():
            values = [self.get_field((x, y)).get_team() for x, y in self.iter_coords()]
            counter = Counter(values)
            # print 'domination', [i for i in values], counter.get_best()
            return self.get_player(counter.get_best())

    def set_players(self, players):
        self.teams_dict = {}
        for player in players:
            self.teams_dict[player.get_team()] = player

    def get_player(self, team):
        return self.teams_dict[team]

    def get_data(self):
        return [[value and value.get_team() or '' for value in row] for row in self.fields]

    def get_data_win(self):
        'Get owner and win line.'
        if not self.is_captured():
            return None
        return [self.owner.get_team(), self.win_coords]

    def dump(self):
        return {
            'fields': copy.deepcopy(self.fields),
            'owner': self.owner,
            'win_coords': copy.deepcopy(self.win_coords),
        }

    def load(self, data):
        self.fields = data['fields']
        self.owner = data['owner']
        self.win_coords = data['win_coords']
