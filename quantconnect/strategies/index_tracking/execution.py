#region imports
from AlgorithmImports import *
#endregion


class MarketOpenExecutionModel(ExecutionModel):
    '''Provides an implementation of IExecutionModel that immediately submits market orders to achieve the desired portfolio targets,
    only when the market is open'''

    # Constructor in C++, self is like the C++ this pointer
    def __init__(self):
        # targets_collection is a class variable
        # PortfolioTargetCollection is a class fromt the QuantConnect framework, here we create an
        # instance of the class called targets_collection
        self.targets_collection = PortfolioTargetCollection()

    # Methods are functions in a class
    # self is always the first argument in a method
    # 
    def execute(self, algorithm, targets):
        # for performance we check count value, OrderByMarginImpact and ClearFulfilled are expensive to call
        self.targets_collection.add_range(targets)
        if not self.targets_collection.is_empty:
            for target in self.targets_collection.order_by_margin_impact(algorithm):
                security = algorithm.securities[target.symbol]
                # calculate remaining quantity to be ordered
                quantity = OrderSizing.get_unordered_quantity(algorithm, target, security)
                if quantity != 0:
                    above_minimum_portfolio = BuyingPowerModelExtensions.above_minimum_order_margin_portfolio_percentage(security.buying_power_model, security, quantity, algorithm.portfolio, algorithm.settings.minimum_order_margin_portfolio_percentage)
                    # check if the market exchange is opened
                    is_open = security.exchange.hours.is_open(algorithm.time, False)
                    if above_minimum_portfolio and is_open:
                        algorithm.market_order(security, quantity)

            self.targets_collection.clear_fulfilled(algorithm)