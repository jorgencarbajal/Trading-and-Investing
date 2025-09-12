# template from youtube video, outdated syntax...

# ***** TEMPLATE FOR A BASIC ALGORITHM *****


class MeasuredOrangeFish(QCAlgorithm):


  # ***** INITIALIZATION *****
  def Initialize(self):
    self.SetStartDate(2020, 1, 1)
    self.SetEndDate(2021, 1, 1)
    self.SetCash(100000)

  spy = self.AddEquity("SPY", Resolution.Daily)
  # self.AddForex, self.AddFuture...

  # data mode, 
  # DataNormalizationMode.Adjusted: Splits and dividends are abackwards adjusted into the price of the asset. The price today is the identical to current market price.
  # DataNormalizationMode.Raw: No modifications to the asset price at all.
  # DataNormalizationMode.SplitAdjusted: Only equity splits are applied to the price adjustment, while dividends are still paid in cash to your portfolio. This allows for managment of the dividend payments while
  # while still given a smooth curve for indicators
  # DataNormalizationMode.TotalReturn: Return of the investment adding the dividend sum to the initail asset price
  spy.SetDataNormalizationMode(DataNormalizationMode.Raw)

  self.spy = spySymbol

  # sets the benchmark the algo
  self.SetBenchmark("SPY")

  # sets broker so algorihm accounts for brokers fee structure and account type
  self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)
  
  # helper variables
  self.entryPrice = 0 # tracks entry price
  self.period = timedelta(31) # holding period
  self.nextEntryTime = self.Time # next entry time

  # ***** ON DATA HANDLING *****
  
# this is called everytime the end of the bar is reached, or new tick data arrives
def OnData(self, data): 
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

  # to check if data exists
  if not self.spy in data:
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
  if not self.Portfolio.Invested:
     if self.nextEntryTime <= self.Time:
        # enter position
        self.SetHoldings(self.spy, 1) # invest 100% of portfolio in SPY
        #self.MarketOrder(self.spy, int(self.Portfolio.Cash / price)) # buy as many shares as possible with available cash
        self.Log("BUY SPY @ " + str(price)) # log the buy for reviewing and debugging
        self.entryPrice = price # save entry price
  elif self.entryPrice * 1.1 < price or self.entryPrice * 0.9 > price:
    self.Liquidate() # sell all shares
    self.Log("SELL SPY @ " + str(price)) # log the sell for reviewing and debugging
    self.nextEntryTime = self.Time + self.period # set next entry time
  
