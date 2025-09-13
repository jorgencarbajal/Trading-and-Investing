"""
Buy and hold a given stock or ETF.
Create a trailing stopping order to sell if the price drops by a certain percentage
"""
from AlgorithmImports import *  # Provides QCAlgorithm, Resolution, OrderStatus, etc.
from datetime import datetime
import decimal  # For decimal.Decimal precision

class LogicalRedAlbatross(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2020, 1, 1)  # Set Start Date
        self.set_end_date(2021, 1, 1)  # Set End Date
        self.set_cash(100000)  # Set Cash

        self.qqq = self.add_equity("QQQ", Resolution.HOUR).Symbol

        # helper variables
        # variables to hold order tickets of entry and exit orders
        self.entryTicket = None
        self.stopTicket = None

        # track the fill time of entry and exit orders
        self.entryTime = datetime.min
        self.stopMarketOrderFillTime = datetime.min

        # keeps track of the highest price since entry
        self.highestPrice = 0

    def on_data(self, data: Slice):
        # wait 30 days after last exit
        if (self.time - self.stopMarketOrderFillTime).days < 30:
            return

        price = self.securities[self.qqq].Close

        # send entry limit order
        if not self.portfolio.invested and not self.transactions.get_open_orders(self.qqq):
            quantity = self.calculate_order_quantity(self.qqq, 0.9)
            self.entryTicket = self.limit_order(self.qqq, int(quantity), price, "Entry Limit Order")  # Updated: Removed explicit Decimal cast for price, as API accepts float/decimal automatically from Close
            self.entryTime = self.time

        # move limit price if not filled after 1 day
        if (self.time - self.entryTime).days > 1 and self.entryTicket.Status != OrderStatus.FILLED:
            self.entryTime = self.entryTime
            updateFields = UpdateOrderFields()
            updateFields.limit_price = price  # Updated: Removed explicit Decimal cast for limit_price, using price directly
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
            self.stopTicket = self.stop_market_order(self.qqq, -self.entryTicket.Quantity, 0.95 * self.entryTicket.AverageFillPrice)  # Updated: Removed explicit Decimal cast for stop price, using float multiplication; removed tag to match overload without str

        # save fill time of stop loss order
        if self.stopTicket is not None and self.stopTicket.OrderId == orderEvent.OrderId:
            self.stopMarketOrderFillTime = self.time
            self.highestPrice = 0