#region imports
from AlgorithmImports import *
#endregion

class MarketIndexETFUniverseSelectionModel(ETFConstituentsUniverseSelectionModel):
    # -> None means the function does not return any value
    # universe_settings: UniverseSettings means universe_settings is expected to be
    # of type UniverseSettings
    def __init__(self, benchmark, universe_settings: UniverseSettings = None) -> None:
        # super().init(...) calls the constructor of the base class 
        # ETFConstituentsUniverseSelectionModel, passing along the arguments.
        super().__init__(benchmark, universe_settings, self.etf_constituents_filter)

    def etf_constituents_filter(self, constituents):
        # Get the 20 securities with the largest weight in the index
        selected = sorted([c for c in constituents if c.weight], 
                          key=lambda c: c.weight, reverse=True)
        return [c.symbol for c in selected[:20]]