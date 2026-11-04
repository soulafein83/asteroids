#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Copyright (C) 2008  Nick Redshaw
#    Copyright (C) 2018  Francisco Sanchez Arroyo
#


import math


class Vector2d:

    def __init__(self, x, y):
        self.x = x
        self.y = y

    # Copy-constructor style arithmetic: operators always return a NEW
    # vector and never mutate the operands (M-6).
    def __add__(self, other):
        return Vector2d(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector2d(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        return Vector2d(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar):
        return self.__mul__(scalar)

    def __eq__(self, other):
        return (isinstance(other, Vector2d)
                and self.x == other.x and self.y == other.y)

    def __repr__(self):
        return f"Vector2d(x={self.x}, y={self.y})"

    def magnitude(self):
        return math.hypot(self.x, self.y)
