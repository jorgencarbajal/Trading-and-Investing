"""The lean engine is a piplin of pluggable models. Each model answers one responsibility 
(what symbols to consider, what signals to produce, how to turn signals into positions, how to 
place orders, how to apply risk/fees, etc.).

You wire up the models in initialize() (or rely on the framework defaults). The engine calls them 
in a defined order so the algorithm can make decisions from top (universe/alpha) to bottom (execution).

Example of a model driven pipleine:
- UniverseSelectionModel: defines the securities to consider (e.g. ETF constituents)
- AlphaModel (or any code that generates signals/insights): produces signals on what to do
- PortfolioConstructionModel: converts signals/insights into portfolio targets objects
- ExecutionModel (optional if you will use the algorithm's own order calls, but normally set to 
control how targets become orders)

The models are called in the following order:
1. UniverseSelectionModel: called when the universe needs to be updated (e.g. daily, monthly, etc.)
2. AlphaModel: called on every new data slice (e.g. every minute, second, etc.)
3. PortfolioConstructionModel: called after the AlphaModel, to convert insights into portfolio targets
4. ExecutionModel: called after the PortfolioConstructionModel, to convert portfolio targets into orders

HIGH LEVEL: 
1. Engine instantiates your QCAlgorithm subclass (e.g., EquityETFBeta).
2. Calls initialize() once so you can configure the algorithm.
3. Enters the main loop (backtest replay or live streaming). On each data update the engine:
    - Updates subscriptions/universe (calls universe models when needed)
    - Calls alpha/risk/portfolio/execution pipeline as appropriate
    - Calls OnData (and other event hooks) for your algorithm
4. Calls end-of-day / end-of-algorithm shutdown hooks when appropriate and then stops.

LIFECYCLE HOOKS:
- initialize(self)
    - Called once at the start to set up the algorithm (dates, cash, models, etc.)
    - Purpose: register securites (add_equity), set start/end dates/cash/brokerage, and register
    models (set_universe_selection, add_alpha, set_portfolio_construction, set_execution, etc.)
    - Do heavy setup here -- nothing else runs until this completes.
- on_data(self, slice)
    - Called repeatedly whenever new data arrives (per bar or tick depending on Resolution). Recieves
    a Slice containing all current subscriptions' data.
    - Purpose:  inspect incoming data, update custom indicators, place manual orders if your arent 
    using the model pipline. When you use the model pipeline, you rearely place raw orders here, 
    models handle that.
- on_secturites_changed(self, changes)
    - Called whenever the universe changes (securities added/removed). Recieves a SecurityChanges 
    object with lists of added and removed securities.
    - Purpose: inspect changes, initialize custom data structures/indicators for new securities, 
    clean up resources for removed securities.
- on_order_event(self, order_event)
    - Called whenever an order's status changes (submitted, filled, cancelled, etc.). Recieves an 
    OrderEvent object with details about the order change.
    - Purpose: track order status, implement custom order handling logic (e.g., logging, notifications).
- on_end_of_day(self, symbol)
    - Called at the end of each trading day for each security. Recieves the security's symbol.
    - Purpose: perform end-of-day processing (e.g., logging, custom indicator updates).
"""


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

        # creates an object of your custom universe selection model
        # and sets it as the universe selection model for your algorithm
        self.set_universe_selection(MarketIndexETFUniverseSelectionModel(spy, self.universe_settings))

        # add_alpha is a method of QCAlgorithm that adds an alpha model to the algorithm
        # ConstantAlphaModel is a built-in alpha model that generates constant insights
        # simple representation of a bullish signal for the next 90 days
        self.add_alpha(ConstantAlphaModel(InsightType.PRICE, InsightDirection.UP, timedelta(90)))

        # defines attribute self.pcm and assigns it an instance of your custom portfolio construction 
        # model SparseOptimizationPortfolioConstructionModel
        self.pcm = SparseOptimizationPortfolioConstructionModel(self, spy, 252, Resolution.DAILY)
        self.pcm.rebalance_portfolio_on_security_changes = False     # avoid constant rebalancing
        # the construction model created above is now sent to the method set_portfolio_construction
        self.set_portfolio_construction(self.pcm)

        # This is enforced by your MarketOpenExecutionModel, which checks if the exchange is open 
        # before submitting orders. It prevents trades from being placed during closed market hours
        self.set_execution(MarketOpenExecutionModel())

    def on_data(self, slice):
        if slice.splits or slice.dividends:
            self.pcm.handle_corporate_actions(self, slice)