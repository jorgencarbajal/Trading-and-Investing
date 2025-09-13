"""
This QuantConnect algorithm implements a simple momentum-based trading strategy for the SPY ETF using daily resolution 
data in raw normalization mode. It runs a backtest from January 1, 2020, to January 1, 2021, starting with $100,000 
in cash, using Interactive Brokers as the brokerage model with a margin account, and benchmarks performance against SPY. 
The strategy includes a 1-day warm-up period to preload data and avoids trading until after a 31-day cooldown period 
following each exit.

Here's a step-by-step description of the strategy's logic, executed on each new data slice (at the end of each daily 
bar):

1. Check for Valid Data: The algorithm first verifies if SPY data is available in the current data slice. If not, 
it logs a message and skips the rest of the logic to prevent errors.

2. Retrieve Current Price: It fetches the closing price of SPY from the data slice.

3. Entry Condition (Buy if Not Invested and Cooldown Expired): If the portfolio is not currently invested (no holdings) 
and the current time is at or after the next allowed entry time (initially set to the algorithm's start time):
   - Invest 100% of the portfolio in SPY using the set_holdings method.
   - Log the buy action with the current price.
   - Record the entry price for future exit calculations.

4. Exit Condition (Sell on 10% Gain or Loss): If the portfolio is invested and the current price has moved 
significantly from the entry price—specifically, if it's risen by 10% (current price > entry price * 1.1) or fallen 
by 10% (current price < entry price * 0.9):
   - Liquidate all holdings in SPY.
   - Log the sell action with the current price.
   - Set the next entry time to the current time plus a 31-day holding/cooldown period, preventing immediate re-entry.

This cycle repeats, effectively buying SPY after any cooldown, holding until a 10% profit target or stop-loss is hit, 
then selling and waiting 31 days before potentially re-entering. The strategy does not include advanced risk management, 
indicators, or multi-asset logic beyond SPY.
"""


# Provides QCAlgorithm, Resolution, DataNormalizationMode, and other required classes/enums
from AlgorithmImports import *

# Import timedelta for holding period calculations
from datetime import timedelta

class JumpingYellowGreenFrog(QCAlgorithm):

    # ***** INITIALIZATION *****
    def initialize(self):
        self.set_start_date(2020, 1, 1) # Set Start Date
        self.set_end_date(2021, 1, 1) # Set End Date
        self.set_cash(100000) # Set Cash

        # Added warm-up period to ensure SPY data is pre-loaded
        # Helps avoid missing data at the start of the backtest
        self.set_warm_up(timedelta(days=1))

        # add_equity returns a Security object; store it to access Symbol
        spy = self.add_equity("SPY", Resolution.DAILY)
        # self.AddForex, self.AddFuture...
        # Resolution.MINUTE: One bar per minute
        # Resolution.HOUR: One bar per hour
        # Resolution.SECOND: One bar per second
        # Resolution.TICK: Every tick (individual trade)

        # data mode,
        # DataNormalizationMode.Adjusted: Splits and dividends are abackwards adjusted into the price of the 
        #   asset. The price today is the identical to current market price.
        # DataNormalizationMode.Raw: No modifications to the asset price at all.
        # DataNormalizationMode.SplitAdjusted: adjusts prices for splits only, not dividends, so you get a 
        #   smooth price chart and receive dividends as cash in your portfolio.
        # DataNormalizationMode.TotalReturn: Return of the investment adding the dividend sum to the initail asset price
        spy.SetDataNormalizationMode(DataNormalizationMode.RAW)

        # Fixed: Changed spySymbol to spy.Symbol to resolve undefined variable error
        self.spy = spy.Symbol

        # sets the benchmark the algo
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