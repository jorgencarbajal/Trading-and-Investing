# ***** ENHANCED TEMPLATE FOR A QUANTCONNECT ALGORITHM *****
# This template provides a comprehensive starting point for building trading algorithms on the QuantConnect platform.
# It includes detailed explanations, best practices, and expandable sections for common features like indicators,
# universe selection, risk management, and more. The code is written in Python, which is one of the supported languages
# alongside C#. QuantConnect uses a backtesting and live trading framework where algorithms inherit from QCAlgorithm.
#
# Key Concepts:
# - **Backtesting**: Simulate your strategy on historical data.
# - **Live Trading**: Deploy to brokers like Interactive Brokers or paper trading.
# - **Data Resolution**: Tick (highest frequency), Second, Minute, Hour, Daily.
# - **Securities**: Equities, Forex, Futures, Options, Crypto, CFDs.
# - **Universe Selection**: Dynamically select assets to trade.
# - **Indicators**: Technical analysis tools like Moving Averages, RSI, etc.
# - **Portfolio Management**: Handle positions, orders, cash, and risk.
# - **Logging and Debugging**: Use self.log(), self.debug(), and self.error() for output.
# - **Scheduling**: Use self.schedule to run methods at specific times.
# - **Warm-Up Period**: self.set_warm_up() to pre-load data for indicators.
#
# Best Practices:
# - Always check if data exists before accessing to avoid errors.
# - Use self.time for current algorithm time.
# - Handle events like splits, dividends, and delistings.
# - Implement risk management to limit drawdowns.
# - Test with different brokerages and account types (Cash vs. Margin).
# - Optimize for performance: Avoid heavy computations in on_data if possible.
#
# To extend: Add custom methods, override event handlers like on_order_event, on_end_of_algorithm, etc.

# Updated import for QuantConnect's 2025 cloud platform (LEAN master v17286)
# 'from AlgorithmImports import *' provides QCAlgorithm, Resolution, DataNormalizationMode, etc.
from AlgorithmImports import *

# Import timedelta for holding period calculations
from datetime import timedelta

class JumpingYellowGreenFrog(QCAlgorithm): 

    # ***** INITIALIZATION *****

    # Updated to lowercase: initialize (was Initialize) to match cloud API
    def initialize(self):

        # ***** SET TIMEFRAME/CASH/TIMEZONE *****

        # Set the backtest or live trading period
        self.set_start_date(2020, 1, 1)  # Start date (year, month, day)
        self.set_end_date(2021, 1, 1)    # End date; omit for live trading
        # self.set_start_date(datetime(2020, 1, 1))  # Alternative with datetime import
        
        # Initial cash allocation
        self.set_cash(100000)  # Starting capital in USD
        
        # Timezone settings: Default is UTC; set to match data or broker
        self.set_time_zone("America/New_York")  # Common for US equities
        
        # ***** WARM UP KEY? *****

        # Warm-up period: Pre-loads historical data to avoid missing data
        # Added to prevent 'NoneType' errors and ensure data availability
        # self.set_warm_up(...) is a QuantConnect method that specifies how much historical 
        #   data to load before the main algorithm loop starts.
        # timedelta(days=1) means 1 day of data will be loaded for each security you’ve added.
        # Set the warm-up period to match the historical data needs of your indicators or logic. 
        #   More than one day is needed if your strategy relies on multi-day calculations.
        self.set_warm_up(timedelta(days=1))  # 1 day for daily resolution
        
        # ***** ADD SECURITIES *****

        # Add assets to track
        # This line registers SPY for daily trading and saves its Symbol for use throughout your algorithm.
        self.spy = self.add_equity("SPY", Resolution.DAILY, Market.USA).Symbol
        # self.add_equity("AAPL", Resolution.MINUTE)  # Minute bars for Apple stock
        # self.add_forex("EURUSD", Resolution.HOUR, Market.OANDA)  # Forex pair
        # self.add_crypto("BTCUSD", Resolution.DAILY, Market.GDAX)  # Crypto
        # self.add_future(Futures.Currencies.BRITISH_POUND, Resolution.MINUTE)  # Futures
        # self.add_option("SPY", Resolution.MINUTE)  # Options chain
        
        # Data Normalization Modes
        # This line ensures that all price data for SPY in your algorithm is unadjusted for splits and 
        #   dividends, reflecting the actual prices as they occurred in the market.
        # self.securities[self.spy] accesses the Security object for SPY.
        # .Set DataNormalizationMode(...) sets how historical data is presented for that security.
        # DataNormalizationMode.RAW tells QuantConnect to use raw, unadjusted prices.
        # SIDENOTE: Adjusted or SplitAdjusted modes are preferred for strategies using indicators 
        #   (e.g., RSI, MACD) because they ensure continuity in price series, avoiding jumps from splits/dividends 
        #   that could skew signals. Your strategy doesn’t use indicators, so this isn’t relevant.
        self.securities[self.spy].SetDataNormalizationMode(DataNormalizationMode.RAW)
        
        # ***** LEVERAGE AND FEES *****

        # Leverage and Fees: Customize per security
        self.securities[self.spy].set_leverage(2.0)  # e.g., 2x leverage for margin accounts
        self.securities[self.spy].fee_model = ConstantFeeModel(0.01)  # Flat fee per share
        
        # ***** BENCHMARK AND BROKERAGE *****

        # Set benchmark for performance comparison
        self.set_benchmark("SPY")
        
        # Brokerage Model: Choose based on your trading account
        self.set_brokerage_model(BrokerageName.INTERACTIVE_BROKERS_BROKERAGE, AccountType.MARGIN)
        
        # ***** UNIVERSE SELECTION (OPTIONAL) *****
        
        # self.universe_settings.resolution = Resolution.DAILY
        # self.add_universe(self.coarse_selection_function, self.fine_selection_function)
        
        # ***** INDICATORS AND CONSOLIDATORS *****

        # Simplified to exclude indicators, matching your original code
        # self.sma = self.sma(self.spy, 20, Resolution.DAILY)  # 20-period SMA
        # self.rsi = self.rsi(self.spy, 14, MovingAverageType.WILDERS, Resolution.DAILY)  # RSI
        
        # ***** HELPER VARIABLES *****
        
        self.entryPrice = 0  # Entry price for the last position
        self.holdingPeriod = timedelta(days=31)  # Matches your 31-day period
        # This line initializes the next allowed trade time to the current time, enabling 
        #   immediate trading at the start.
        self.nextEntryTime = self.time
        
        # Disabled template's extra variables to match your original code
        # self.previousPrice = None
        # self.tradeCount = 0
        # self.symbolData = {}

    # ***** ON DATA HANDLING *****

    # This method is the core of your trading logic, processing new market data and executing trades as needed.
    # Updated to lowercase: on_data (was OnData) to match cloud API
    def on_data(self, data: Slice):
        # Slice Structure:
        # - Bars: Dict[Symbol, TradeBar] - OHLCV for trades.
        # - QuoteBars: Dict[Symbol, QuoteBar] - Bid/Ask data.
        # - Ticks: Dict[Symbol, List[Tick]] - Tick-level data (price/size).
        # - OptionChains/FuturesChains: For derivatives.
        # - Splits/Dividends/Delistings/SymbolChangedEvents: Corporate actions.
        
        # BaseData Properties (inherited by TradeBar, QuoteBar, Tick):
        # - Symbol: Asset identifier.
        # - Time: Start time of the bar.
        # - EndTime: End time of the bar.
        # - Value: Primary value (e.g., Close for TradeBar).
        # - DataType: MarketDataType (Trade, Quote, etc.).
        # - IsFillForward: If data was filled from previous bar.
        
        # TradeBar: Open, High, Low, Close, Volume.
        # QuoteBar: Bid (Open/High/Low/Close), Ask (Open/High/Low/Close), LastBidSize, LastAskSize.
        # Tick: LastPrice, Quantity, SaleCondition, Exchange, Suspicious, BidPrice, BidSize, AskPrice, AskSize.
        
        # ***** DATA VALIDATION *****

        # Check if data exists to avoid 'NoneType' error
        if not self.spy in data or data[self.spy] is None:
            self.log(f"No data for SPY at {self.time}")
            return
        
        # ***** RETRIEVE CURRENT PRICE *****

        # This line saves the latest closing price of SPY to the variable price, so you can use it for 
        #   trading decisions or logging.
        # data is a Slice object containing all new market data for the current time step.
        # Bars is a dictionary within data that maps each tracked Symbol to its latest TradeBar (OHLCV) data.
        # self.spy is the Symbol object for SPY, previously set in your algorithm.
        # data.Bars[self.spy] gets the TradeBar for SPY.
        # .Close accesses the closing price from that TradeBar.
        #price = data.Bars[self.spy].Close
        # another way to get the price
        price = data[self.spy].Close
        # third way
        #price = self.securities[self.spy].Close

        # ***** IMPLEMENT STRATEGY *****

        # logic: Buy SPY with 100% portfolio, sell at ±10% or after 31 days
        # This line ensures that your algorithm only enters a new trade when it is not already invested in any asset.
        if not self.portfolio.invested:
            
            if self.nextEntryTime <= self.time:
                # enter position
                self.set_holdings(self.spy, 1)  # invest 100% of portfolio in SPY
                #self.MarketOrder(self.spy, int(self.portfolio.Cash / price))  # buy as many shares as possible with available cash
                self.log("BUY SPY @ " + str(price))  # log the buy for reviewing and debugging
                self.entryPrice = price  # save entry price
        elif self.entryPrice * 1.1 < price or self.entryPrice * 0.9 > price:
            # Updated to snake_case: liquidate (was Liquidate)
            self.liquidate()  # sell all shares
            # Updated to snake_case: log (was Log)
            self.log("SELL SPY @ " + str(price))  # log the sell for reviewing and debugging
            # Updated to snake_case: time (was Time)
            self.nextEntryTime = self.time + self.holdingPeriod  # set next entry time

    # ***** OTHER EVENT HANDLERS (OPTIONAL) *****

    # These handlers let you monitor and respond to important events (orders, daily closes, 
    #   algorithm end, scheduled tasks) for better tracking, debugging, and control of your trading algorithm.
    # def on_order_event(self, orderEvent):
    #     if orderEvent.status == OrderStatus.FILLED:
    #         self.debug(f"Order Filled: {orderEvent.Symbol} | Quantity: {orderEvent.FillQuantity} | Price: {orderEvent.FillPrice}")
    
    # def on_end_of_day(self, symbol):
    #     self.debug(f"End of Day for {symbol}: Positions: {self.portfolio[symbol].Quantity}")
    
    # def on_end_of_algorithm(self):
    #     self.log(f"Algorithm Ended | Final Portfolio Value: {self.portfolio.TotalPortfolioValue}")
    
    # def rebalance(self):
    #     self.log("Scheduled Rebalance Executed")

# ***** END OF TEMPLATE *****
# To run: Deploy on QuantConnect.com in the cloud editor for your simple SPY backtest