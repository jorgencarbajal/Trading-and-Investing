class MeasuredOrangeFish(QCAlgorithm):

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
  self.period = time 

  

def OnData(self, data): 
  pass


  
