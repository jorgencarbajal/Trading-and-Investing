# region imports
# This line imports all the core QuantConnect framework
from AlgorithmImports import *
from execution import MarketOpenExecutionModel
# import other files/modules
from portfolio import SparseOptimizationPortfolioConstructionModel
from universe import MarketIndexETFUniverseSelectionModel
# endregion

# This is the main class that defines the algorithm
# Inherits from QCAlgorithm, which is the base class for all algorithms in QuantConnect
# The QC framework calls the methods in this and other classes at the appropriate times
class EquityETFBeta(QCAlgorithm):

    # explicitly called "initialize" by the QC framework at the start of the algorithm
    def initialize(self):

        # datetime.now() creates a datetime object representing the current date and time
        # set the starting and ending dates for backtesting
        self.set_end_date(datetime.now())
        # self.set_end_date(...) sets the algorithm’s end date to that datetime
        self.set_start_date(self.end_date - timedelta(5*365))
        self.set_cash(100000)  # Set Strategy Cash

        # universe_settings is an attribute of QCAlgorithm (the main QuantConnect algorithm base class)
        # Resolution is an enum (enumeration) provided by QuantConnect, typically imported via from 
        # AlgorithmImports import *
        # The algorithm uses universe_settings to define how it analyzes and selects securities, 
        # and setting resolution to Resolution.MINUTE means it processes and analyzes data at a 
        # 1-minute frequency for universe selection and related operations.
        self.universe_settings.resolution = Resolution.MINUTE
        # DataNormalizationMode is also an enum provided by QuantConnect
        # Setting data_normalization_mode to DataNormalizationMode.RAW means the algorithm will use
        # raw, unadjusted price data for its calculations and decisions, without any adjustments 
        # for corporate actions like dividends or stock splits.
        self.universe_settings.data_normalization_mode = DataNormalizationMode.RAW

        # add_equity is a method of QCAlgorithm that adds a specific equity (stock) to the algorithm's
        # add_equity(symbol, resolution, data_normalization_mode, fill_forward, leverage, 
        # extended_hours)
        # "SPY" is a positoinal argument, the rest are keyword arguments
        spy = self.add_equity("SPY",
            resolution = self.universe_settings.resolution,
            data_normalization_mode = self.universe_settings.data_normalization_mode).symbol
        # set_benchmark is a method of QCAlgorithm that sets the benchmark for the algorithm
        # used for backtesting or live trading to compare the algorithm's performance against 
        # a standard
        self.set_benchmark(spy)
        
        # configures your algorithm to simulate the rules and behavior of a specific brokerage 
        # and account type
        self.set_brokerage_model(BrokerageName.INTERACTIVE_BROKERS_BROKERAGE, AccountType.MARGIN)

        # Our sparse index will be composed by selected SPY's constituents
        self.set_universe_selection(MarketIndexETFUniverseSelectionModel(spy, self.universe_settings))

        self.add_alpha(ConstantAlphaModel(InsightType.PRICE, InsightDirection.UP, timedelta(90)))

        # We will be using sparse optimization to construct an index to simulate the upward movement 
        # of the benchmark
        self.pcm = SparseOptimizationPortfolioConstructionModel(self, spy, 252, Resolution.DAILY)
        self.pcm.rebalance_portfolio_on_security_changes = False     # avoid constant rebalancing
        self.set_portfolio_construction(self.pcm)

        # This is enforced by your MarketOpenExecutionModel, which checks if the exchange is open 
        # before submitting orders. It prevents trades from being placed during closed market hours
        self.set_execution(MarketOpenExecutionModel())

    def on_data(self, slice):
        if slice.splits or slice.dividends:
            self.pcm.handle_corporate_actions(self, slice)