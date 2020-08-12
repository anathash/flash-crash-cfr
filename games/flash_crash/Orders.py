from math import floor
from typing import List


class NoLimitOrder:
    def __init__(self, asset_symbol: str, num_shares: float):
        int_num_shares = int(floor(num_shares))
        self.asset_symbol = asset_symbol
        self.num_shares = int_num_shares

    def __eq__(self, other):
        return isinstance(other, NoLimitOrder) and \
               self.asset_symbol == other.asset_symbol and \
               self.num_shares == other.num_shares


class Buy(NoLimitOrder):
    def __init__(self, asset_symbol: str, num_shares: int):
        super().__init__(asset_symbol, num_shares)

    def __repr__(self):
        return 'Buy ' + self.asset_symbol + ' ' + str(self.num_shares)


class Sell(NoLimitOrder):
    def __init__(self, asset_symbol: str, num_shares: float):
        super().__init__(asset_symbol, num_shares)

    def __repr__(self):
        return 'Sell ' + self.asset_symbol + ' ' + str(self.num_shares)


#class EmptyOrder(NoLimitOrder):
#    def __init__(self):
#        super().__init__('', 0)
#
#    def __repr__(self):
#        return 'Empty Order'

Move = List[NoLimitOrder]

"""class Action:
    def __init__(self, orders: List[Order]):
        self.orders = orders
"""