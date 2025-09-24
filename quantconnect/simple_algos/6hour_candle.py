class TimeslicesTimeModelingAlgorithm(QCAlgorithm):
    def initialize(self) -> None:
        self.set_start_date(2020, 1, 1)
        self.set_end_date(2021, 1, 1)
        
        # Request AAPL data to trade it. We need a resolution denser than 6-hour for the consolidator.
        self.aapl = self.add_equity("AAPL", Resolution.Hour).symbol

        # Create a 6-hour consolidator for smoothing the noise.
        self.consolidator = TradeBarConsolidator(timedelta(hours=6))
        # Subscribe the consolidator to update with the security's data automatically.
        self.subscription_manager.add_consolidator(self.aapl, self.consolidator)

    def on_data(self, slice: Slice) -> None:
        bar = slice.bars.get(self.aapl)
        if bar and self.consolidator.working_bar is not None:
            # Trade on a rising trend, suggested by the current close is above the past hour open
            # and the past hour open is above the 6-hour bar open.
            if self.consolidator.working_bar.open < bar.open < bar.close:
                self.set_holdings(self.aapl, 1)
            # Trade on a down trend, suggested by the current close is below the past hour open
            # and the past hour open is below the 6-hour bar open.
            elif self.consolidator.working_bar.open > bar.open > bar.close:
                self.set_holdings(self.aapl, -1)
            # Otherwise, do not hold a position if there is no deterministic trend.
            else:
                self.liquidate()