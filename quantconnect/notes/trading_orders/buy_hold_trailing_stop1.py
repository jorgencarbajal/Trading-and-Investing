"""
Buy and hold a given stock or ETF.
Create a trailing stopping order to sell if the price drops by a certain percentage
"""
from AlgorithmImports import *  # Provides QCAlgorithm, Resolution, OrderStatus, etc.
from datetime import datetime
import decimal  # For decimal.Decimal precision

class LogicalRedAlbatross(QCAlgorithm):
    """This line defines the initialize method, which is automatically called by 
    QuantConnect to set up your algorithm’s initial settings and variables. In the 
    context of the strategy, it is where you configure the trading environment, add securities, 
    and prepare any helper variables needed for your buy-and-hold with trailing stop logic."""
    def initialize(self):
        self.set_start_date(2020, 1, 1)  # Set Start Date
        self.set_end_date(2021, 1, 1)  # Set End Date
        self.set_cash(100000)  # Set Cash

        self.qqq = self.add_equity("QQQ", Resolution.HOUR).Symbol

        """These lines initialize variables to store the order tickets for your entry (buy) and stop 
        (sell) orders, setting them to None at the start. In the context of the strategy, this allows 
        you to track and manage your active entry and trailing stop orders throughout the algorithm’s execution."""
        # helper variables
        # variables to hold order tickets of entry and exit orders
        self.entryTicket = None
        self.stopTicket = None

        """These lines initialize the timestamps for when the entry order and the stop market order are filled, 
        setting them to the earliest possible datetime value. In the context of the strategy, this allows you to 
        track when trades occur and enforce waiting periods (like the 30-day cooldown after an exit) before placing 
        new trades."""
        # track the fill time of entry and exit orders
        self.entryTime = datetime.min
        self.stopMarketOrderFillTime = datetime.min

        # keeps track of the highest price since entry
        self.highestPrice = 0

    """This line defines the on_data method, which is automatically called by QuantConnect every time new market 
    data arrives (such as each bar or tick, depending on your resolution). In the context of the strategy, this is 
    where you implement your core trading logic—monitoring prices, placing orders, and managing your buy-and-hold 
    with trailing stop rules in response to live data updates."""
    def on_data(self, data: Slice):

        # wait 30 days after last exit
        if (self.time - self.stopMarketOrderFillTime).days < 30:
            return

        """This line retrieves the most recent closing price of QQQ from the Security object and stores it in the 
        variable price. In the context of the strategy, it provides the current market price needed for placing 
        new orders, updating limit prices, and managing the trailing stop logic."""
        price = self.securities[self.qqq].Close

        """This line checks if you are not currently invested in QQQ and have no open orders for QQQ, ensuring you 
        only place a new entry order when you have no active position or pending order. In the context of the strategy, 
        it prevents duplicate or overlapping trades and ensures a clean entry process."""
        # send entry limit order
        if not self.portfolio.invested and not self.transactions.get_open_orders(self.qqq):

            """This line calculates the number of QQQ shares to buy so that 90% of your portfolio value is allocated 
            to this position. For the strategy, it helps manage risk and position sizing by not using all available 
            capital in a single trade."""
            quantity = self.calculate_order_quantity(self.qqq, 0.9)

            """This line submits a limit order to buy 100 shares of QQQ at the current price and stores the order 
            ticket for tracking. In the strategy, it initiates a new position with precise control over the order 
            and enables later management of the trailing stop."""
            # Make sure price is a float or decimal.Decimal
            self.entryTicket = self.limit_order(self.qqq, 100, float(price))

            """This line records the current time as the entry time for the new position. In the context of the strategy, 
            it allows you to track how long the position has been open and manage order updates or cooldown periods accordingly."""
            self.entryTime = self.time


        """This line checks if more than one day has passed since the entry order was placed and if the order is still 
        not filled. In the context of the strategy, it ensures that stale limit orders are updated to keep them relevant 
        with current market prices."""
        if (self.time - self.entryTime).days > 1 and self.entryTicket.Status != OrderStatus.FILLED:
            """This line does nothing and can be removed; it may be a placeholder or leftover from previous code. In the 
            strategy, it has no effect on logic or execution."""
            self.entryTime = self.entryTime
            """This line creates an UpdateOrderFields object, which is used to specify what aspects of an existing order 
            you want to change. In the strategy, it prepares to update the limit price of the entry order."""
            updateFields = UpdateOrderFields()
            """This line sets the new limit price for the order update to the current market price. In the strategy, it 
            helps the entry order stay competitive and increases the chance of being filled."""
            updateFields.limit_price = price
            """This line applies the updates to the existing entry order using the new limit price. In the context of the 
            strategy, it actively manages open orders to adapt to changing market conditions and avoid missed opportunities."""
            self.entryTicket.Update(updateFields)

        # move up the price of the trailing stop price
        if self.stopTicket is not None and self.portfolio.invested:
            if price > self.highestPrice:
                self.highestPrice = price
                updateFields = UpdateOrderFields()
                updateFields.stop_price = price * 0.95  # Updated: Removed explicit Decimal cast for stop_price, using float multiplication
                self.stopTicket.Update(updateFields)
                self.debug(str(updateFields.stop_price))

    def on_order_event(self, orderEvent):
        if orderEvent.Status != OrderStatus.FILLED:
            return

        # send stop loss order if entry limit order is filled
        if self.entryTicket is not None and self.entryTicket.OrderId == orderEvent.OrderId:
            self.stopTicket = self.stop_market_order(self.qqq, -self.entryTicket.Quantity, 0.95 * self.entryTicket.AverageFillPrice)  
        # save fill time of stop loss order
        if self.stopTicket is not None and self.stopTicket.OrderId == orderEvent.OrderId:
            self.stopMarketOrderFillTime = self.time
            self.highestPrice = 0