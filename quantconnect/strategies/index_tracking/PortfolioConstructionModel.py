from AlgorithmImports import *

class PortfolioConstructionModel:
    def __init__(self, rebalance=None, portfolio_bias=PortfolioBias.LongShort):
        self.rebalance = rebalance
        self.portfolio_bias = portfolio_bias

    def create_targets(self, algorithm, insights):
        """
        Should be overridden by subclasses to return a list of PortfolioTarget objects
        based on the provided insights.
        """
        raise NotImplementedError("create_targets must be implemented by subclasses.")

    def on_securities_changed(self, algorithm, changes):
        """
        Optional: Handle logic when securities are added or removed from the universe.
        """
        pass