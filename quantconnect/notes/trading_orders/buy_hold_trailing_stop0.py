"""
Buy and hold a given stock or ETF.
Create a trailing stopping order to sell if the price drops by a certain percentage

"""
class BuyAndHoldWithTrailingStop(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2020, 1, 1) # Set Start Date
        self.set_end_date(2021, 1, 1) # Set End Date
        self.set_cash(100000) # Set Cash

        #self.qqq = self.add_equity("QQQ", Resolution.HOURLY).Symbol
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


    def OnData(self, data):
        
        # wait 30 days after last exit
        if (self.Time - self.stopMarketOrderFillTime).days < 30:
            return

        #price = self.Securities[self.qqq].Price
        price = self.securities[self.qqq].Close

        # send entry limit order
        #if not self.Portfolio.Invested and not self.Transactions.GetOpenOrders(self.qqq):
        if not self.portfolio.invested and not self.transactions.get_open_orders(self.qqq):
            #quantity = self.CalculateOrderQuantity(self.qqq, 0.9)
            quantity = self.calculate_order_quantity(self.qqq, 0.9)
            #self.entryTicket = self.LimitOrder(self.qqq, quantity, price, "Entry Limit Order")
            self.entryTicket = self.limit_order(self.qqq, 100, float(price))
            #self.entryTime = self.Time
            self.entryTime = self.time

        # move limit price if not filled after 1 day
        if (self.Time - self.entryTime).days > 1 and self.entryTicket.Status != OrderStatus.Filled:
            self.entryTime = self.entryTime
            updateFields = UpdateOrderFields()
            #updateFields.LimitPrice = price
            updateFields.limit_price = price
            self.entryTicket.Update(updateFields)

        # move up the price of the trailing stop price
        #if self.stopMarketTicket is not None and self.Portfolio.Invested:
        if self.stopTicket is not None and self.portfolio.invested:
            if price > self.highestPrice:
                self.highestPrice = price
                updateFields = UpdateOrderFields()
                #updateFields.StopPrice = price * 0.95
                updateFields.stop_price = price * 0.95
                #self.stopMarketTicket.Update(updateFields)
                self.stopTicket.Update(updateFields)
                #self.Debug(updateFields.StopPrice)
                self.debug(str(updateFields.stop_price))
        #pass

    #def OnOrderEvent(self, orderEvent):
    def on_order_event(self, orderEvent):
        if orderEvent.Status != OrderStatus.Filled:
            return

        # send stop loss order if entry lmit order is filled
        if self.entryTcket is not None and self.entryTicket.OrderId == orderEvent.OrderId:
            #self.stopMarketTicket - self.StopMarketOrder(self.qqq, -self.entryTicket.Quantity,
                                                        #0.95 * self.entryTicket.AverageFillPrice)
            self.stopTicket = self.stop_market_order(self.qqq, -self.entryTicket.Quantity, 0.95 
                                                     * self.entryTicket.AverageFillPrice)
            
        # save fill time of stop loss order
        #if self.stopMarketTicket is not None and self.stopMarketTicket.OrderId == orderEvent.OrderId:
        if self.stopTicket is not None and self.stopTicket.OrderId == orderEvent.OrderId:
            #self.stopMarketOrderFillTime = self.Time
            self.stopMarketOrderFillTime = self.time
            self.highestPrice = 0
        #pass