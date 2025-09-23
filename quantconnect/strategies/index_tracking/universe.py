"""In summary, this file defines a custom universe selection model that selects the 
top 20 securities by weight from a given market index ETF."""

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
        # constituents is a list of ETFConstituent objects, each having 'symbol' 
        # and 'weight' attributes
        # "sorted(..., key=..., reverse=True)" sorts the list in descending order
        # "[c for c in constituents if c.weight]" is a list comprehension that filters 
        # out any constituents with a weight of zero or None
        # key=lambda c: c.weight tells sorted to sort the constituents based on their 
        # weight attribute
        # reverse=True sorts the list in descending order (highest weight first)
        # finally, we return a list of the symbols of the top 20 constituents by weight
        selected = sorted([c for c in constituents if c.weight], 
                          key=lambda c: c.weight, reverse=True)
        return [c.symbol for c in selected[:20]]