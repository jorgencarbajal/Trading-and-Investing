# This template actually works in the QuantConnect cloud platform as of 09/2025
# modified version of template1 and template2

# ***** TEMPLATE FOR A BASIC ALGORITHM *****

# Use QuantConnect's 2025 cloud platform standard import
# Provides QCAlgorithm, Resolution, DataNormalizationMode, and other required classes/enums
from AlgorithmImports import *

# Import timedelta for holding period calculations
from datetime import timedelta

# Class name matches new project's default template
class JumpingYellowGreenFrog(QCAlgorithm):

    # ***** INITIALIZATION *****
    def initialize(self):
        # Updated to snake_case: set_start_date (was SetStartDate)
        self.set_start_date(2020, 1, 1)
        # Updated to snake_case: set_end_date (was SetEndDate)
        self.set_end_date(2021, 1, 1)
        # Updated to snake_case: set_cash (was SetCash)
        self.set_cash(100000)

        # Added warm-up period to ensure SPY data is pre-loaded
        # Helps avoid missing data at the start of the backtest
        self.set_warm_up(timedelta(days=1))

        # Fixed indentation to align with class
        # add_equity returns a Security object; store it to access Symbol
        # Updated to snake_case: add_equity (was AddEquity)
        # Updated enum: Resolution.DAILY (was Resolution.Daily)
        spy = self.add_equity("SPY", Resolution.DAILY)
        # self.AddForex, self.AddFuture...

        # data mode,
        # DataNormalizationMode.Adjusted: Splits and dividends are abackwards adjusted into the price of the asset. The price today is the identical to current market price.
        # DataNormalizationMode.Raw: No modifications to the asset price at all.
        # DataNormalizationMode.SplitAdjusted: Only equity splits are applied to the price adjustment, while dividends are still paid in cash to your portfolio. This allows for managment of the dividend payments while
        # while still given a smooth curve for indicators
        # DataNormalizationMode.TotalReturn: Return of the investment adding the dividend sum to the initail asset price
        # Updated enum: DataNormalizationMode.RAW (was DataNormalizationMode.Raw)
        spy.SetDataNormalizationMode(DataNormalizationMode.RAW)

        # Fixed: Changed spySymbol to spy.Symbol to resolve undefined variable error
        self.spy = spy.Symbol

        # sets the benchmark the algo
        # Updated to snake_case: set_benchmark (was SetBenchmark)
        self.set_benchmark("SPY")

        # sets broker so algorihm accounts for brokers fee structure and account type
        # Updated to snake_case: set_brokerage_model (was SetBrokerageModel)
        # Updated enum: BrokerageName.INTERACTIVE_BROKERS_BROKERAGE
        # Updated enum: AccountType.MARGIN (confirmed correct)
        self.set_brokerage_model(BrokerageName.INTERACTIVE_BROKERS_BROKERAGE, AccountType.MARGIN)

        # helper variables
        self.entryPrice = 0  # tracks entry price
        self.period = timedelta(31)  # holding period
        # Updated to snake_case: time (was Time)
        self.nextEntryTime = self.time  # next entry time

    # ***** ON DATA HANDLING *****
    # Updated to lowercase: on_data (was OnData) to match default template
    # Added type hint 'data: Slice' to match template style
    # this is called everytime the end of the bar is reached, or new tick data arrives
    def on_data(self, data: Slice):
        # data parameter is a slice object that contains all the new data for this time step
        # class Slice:
        #   TradeBar Bars;
        #   QuoteBars QuoteBars;
        #   Ticks Ticks;
        #   OptionChains OptionChains;
        #   FuturesChains FuturesChains
        #   Splits Splits;
        #   Dividends Dividends;
        #   Delistings Delistings;
        #   SymbolChangedEvents SymbolChangedEvents;

        # to check if data exists and is not None
        # Added check for data[self.spy] to prevent 'NoneType' error when accessing .Close
        if not self.spy in data or data[self.spy] is None:
            self.log(f"No data for SPY at {self.time}")  # Debug log to track missing data
            return

        # the most important datatype you can access with such a slice object is BaseData
        # BaseData class contiains: Symbol, Time, Value, EndTime, DataType, IsFillForward
        # trade bar data: type inherits from BaseData and contains: Open, High, Low, Close, Volume
        # tick data: last price, bid price, ask price, bid size, ask size (cautious)
        # quote bar data: bid open, bid high, bid low, bid close, ask open, ask high, ask low, ask close, last price

        # quote bar data is very interesting, there may be somthing there??? ********

        # save the current price
        # data is a Slice object containing all new market data for the current time step.
        # Bars is a dictionary within data that maps each tracked Symbol to its latest TradeBar (OHLCV) data.
        # self.spy is the Symbol object for SPY, previously set in your algorithm.
        # data.Bars[self.spy] gets the TradeBar for SPY.
        # .Close accesses the closing price from that TradeBar.
        #price = data.Bars[self.spy].Close
        # another way to get the price
        price = data[self.spy].Close
        # third way
        #price = self.Securities[self.spy].Close

        # ***** IMPLEMENT STRATEGY *****

        # popular portfolio property values:
        # self.Portfolio.Invested: bool if any position is held
        # self.Portfolio.Cash: available cash
        # self.Porfolio.UnsettledCash: cash from trades that have not yet settled
        # self.Portfolio.TotalPortfolioValue: total value of the portfolio
        # self.Portfolio.TotalUnrealizedProfit: profit from open positions
        # ...
        # Updated to snake_case: portfolio (was Portfolio)
        if not self.portfolio.invested:
            # Updated to snake_case: time (was Time)
            if self.nextEntryTime <= self.time:
                # enter position
                # Updated to snake_case: set_holdings (was SetHoldings)
                self.set_holdings(self.spy, 1)  # invest 100% of portfolio in SPY
                #self.MarketOrder(self.spy, int(self.portfolio.Cash / price))  # buy as many shares as possible with available cash
                # Updated to snake_case: log (was Log)
                self.log("BUY SPY @ " + str(price))  # log the buy for reviewing and debugging
                self.entryPrice = price  # save entry price
        elif self.entryPrice * 1.1 < price or self.entryPrice * 0.9 > price:
            # Updated to snake_case: liquidate (was Liquidate)
            self.liquidate()  # sell all shares
            # Updated to snake_case: log (was Log)
            self.log("SELL SPY @ " + str(price))  # log the sell for reviewing and debugging
            # Updated to snake_case: time (was Time)
            self.nextEntryTime = self.time + self.period  # set next entry time