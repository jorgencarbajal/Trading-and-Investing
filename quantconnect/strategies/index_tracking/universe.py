#region imports
from AlgorithmImports import *
#endregion

class MarketIndexETFUniverseSelectionModel(ETFConstituentsUniverseSelectionModel):
    def __init__(self, benchmark, universe_settings: UniverseSettings = None) -> None:
        super().__init__(benchmark, universe_settings, self.etf_constituents_filter)

    def etf_constituents_filter(self, constituents):
        # Get the 20 securities with the largest weight in the index
        selected = sorted([c for c in constituents if c.weight], 
                          key=lambda c: c.weight, reverse=True)
        return [c.symbol for c in selected[:20]]