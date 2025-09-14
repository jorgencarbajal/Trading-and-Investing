# region imports
# This line imports all the core QuantConnect framework
from AlgorithmImports import *
from execution import MarketOpenExecutionModel
# import other files/modules
from portfolio import SparseOptimizationPortfolioConstructionModel
from universe import MarketIndexETFUniverseSelectionModel
# endregion


class EquityETFBeta(QCAlgorithm):

    def initialize(self):
        self.set_end_date(datetime.now())
        self.set_start_date(self.end_date - timedelta(5*365))
        self.set_cash(100000)  # Set Strategy Cash

        self.universe_settings.resolution = Resolution.MINUTE
        self.universe_settings.data_normalization_mode = DataNormalizationMode.RAW

        # Use SPY as reference
        spy = self.add_equity("SPY",
            resolution = self.universe_settings.resolution,
            data_normalization_mode = self.universe_settings.data_normalization_mode).symbol
        self.set_benchmark(spy)
        
        self.set_brokerage_model(BrokerageName.INTERACTIVE_BROKERS_BROKERAGE, AccountType.MARGIN)

        # Our sparse index will be composed by selected SPY's constituents
        self.set_universe_selection(MarketIndexETFUniverseSelectionModel(spy, self.universe_settings))

        self.add_alpha(ConstantAlphaModel(InsightType.PRICE, InsightDirection.UP, timedelta(90)))

        # We will be using sparse optimization to construct an index to simulate the upward movement of the benchmark
        self.pcm = SparseOptimizationPortfolioConstructionModel(self, spy, 252, Resolution.DAILY)
        self.pcm.rebalance_portfolio_on_security_changes = False     # avoid constant rebalancing
        self.set_portfolio_construction(self.pcm)

        # Only execute the portfolio target if the market is open
        self.set_execution(MarketOpenExecutionModel())

    def on_data(self, slice):
        if slice.splits or slice.dividends:
            self.pcm.handle_corporate_actions(self, slice)