# region imports
from AlgorithmImports import *
# endregion

class JumpingBlueGuanaco(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2020, 1, 1)  # Set Start Date
        self.SetEndDate(2021,1,1)
        self.SetCash(100000)  # Set Strategy Cash
        self.spy = self.AddEquity("SPY", Resolution.Daily).Symbol

        self.sma = self.SMA (self.spy,30,Resolution.Daily)
        self.SetWarmUp(timedelta(30))


    def OnData(self, data):
        if not self.sma.IsReady:  # check difference, warup or isready
            return
        hist = self.History(self.spy,timedelta(260),Resolution.Daily)
        high = max(hist["high"])
        low = min(hist["low"])
        
        price = self.Securities["SPY"].Price

        if price * 1.05 >= high and self.sma.Current.Value < price:
            #if not self.Portfolio[self.spy].IsLong:
                self.SetHoldings(self.spy,1)
        elif price * 0.95 <= low and self.sma.Current.Value > price:
            if not self.Portfolio[self.spy].IsShort:
                self.SetHoldings(self.spy,-1)
        else:
            self.Liquidate(self.spy)
        
        self.Plot("Benchmark","52w-high",high)
        self.Plot("Benchmark","high area",high*0.95)
        self.Plot("Benchmark","52w-low",low)
        self.Plot("Benchmark","low area",low*1.05)
        self.Plot("Benchmark","sma",self.sma.Current.Value)


