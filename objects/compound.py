from objects.node import Node


class Compound(Node):
    __slots__ = ('op', 'lvalue', 'rvalue', 'coord')

    def __init__(self, op, left, right, coord=None):
        self.op = op
        self.lvalue = left
        self.rvalue = right
        self.coord = coord

    def children(self):
        nodelist = []
        if self.lvalue is not None: nodelist.append(("lvalue", self.lvalue))
        if self.rvalue is not None: nodelist.append(("rvalue", self.rvalue))
        return tuple(nodelist)

    attr_names = ('op',)