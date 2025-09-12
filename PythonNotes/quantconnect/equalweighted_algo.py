# This is a simple equal-weighted portfolio algorithm. At the start,
# it splits your capital equally among SPY, BND, and AAPL, and then holds those positions.

# region imports
# brings in all the necessary QuantConnect Lean libraries
from AlgorithmImports import *
# endregion

#random class name
class DancingRedOrangeChicken(QCAlgorithm):

    def initialize(self):
        # sets the backtest start date
        self.set_start_date(2024, 3, 11)
        # starting cash
        self.set_cash(100000)
        # adding three algorithms to the library, all with minute level data
        self.add_equity("SPY", Resolution.MINUTE)
        self.add_equity("BND", Resolution.MINUTE)
        self.add_equity("AAPL", Resolution.MINUTE)

    # this method is called when new market data arrives
    def on_data(self, data: Slice):
        # if the portfolio is not invested in any assets, it invests 33% of the portfolio in each
        if not self.portfolio.invested:
            self.set_holdings("SPY", 0.33)
            self.set_holdings("BND", 0.33)
            self.set_holdings("AAPL", 0.33)
