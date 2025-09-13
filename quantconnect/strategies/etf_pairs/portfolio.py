from AlgorithmImports import *

class CointegratedVectorPortfolioConstructionModel(EqualWeightingPortfolioConstructionModel):
    def __init__(self, algorithm, lookback=252, resolution=Resolution.DAILY, rebalance=None):
        super().__init__(rebalance or Expiry.END_OF_WEEK, PortfolioBias.LONG_SHORT)
        self._algorithm = algorithm
        self.lookback = lookback
        self.resolution = resolution

    def should_create_target_for_insight(self, insight):
        quantity = self._algorithm.portfolio[insight.symbol].quantity
        return quantity == 0 or insight.direction != np.sign(quantity)

    def determine_target_percent(self, active_insights):
        if len(active_insights) < 2:
            return {insight: 0.0 for insight in active_insights}

        # Get log return for cointegrating vector regression
        logr = {
            symbol: self._returns(security._symbol_data)
            for symbol, security in self._algorithm.securities.items()
            if any(insight.symbol == symbol for insight in active_insights) and hasattr(security, "_symbol_data") \
                and security._symbol_data is not None and security._symbol_data.is_ready
        }
        if len(logr) < 2:
            return {insight: 0.0 for insight in active_insights}

        # Fit linear regression model for cointegration
        y = np.array(list(logr.values())[0])
        exog = list(logr.values())[1:]
        X = np.array([[x[i] for x in exog] for i in range(y.size)])
        coefficients, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        n = len(coefficients) + 1
        coint_vector = np.zeros(n)
        coint_vector[0] = 1.0
        coint_vector[1:] = coefficients

        # Calculate the residuals
        residuals = y - np.dot(X, coefficients)
        if not self._is_significant(residuals):
            return {insight: 0.0 for insight in active_insights}

        # Normalization for budget constraint
        total_weight = sum(abs(x) for x in coint_vector)
        result = {}
        for i, insight in enumerate(active_insights):
            result[insight] = abs(coint_vector[i]) / total_weight * insight.direction

        return result

    def on_securities_changed(self, algorithm, changes):
        super().on_securities_changed(algorithm, changes)
        for added in changes.added_securities:
            added._symbol_data = SymbolData(algorithm, added.symbol, self.lookback, self.resolution)

        for removed in changes.removed_securities:
            if hasattr(removed, "_symbol_data") and removed._symbol_data is not None:
                removed._symbol_data.dispose(algorithm)
                delattr(removed, "_symbol_data")

    def _returns(self, symbol_data):
        return np.array(list(symbol_data.window))

    def _is_significant(self, residuals):
        n = len(residuals)
        mean = np.mean(residuals)
        variance = np.var(residuals, ddof=0)
        adf_statistic = mean / np.sqrt(variance / n)
        critical_val = -1.941 - 0.2686 / n - 3.365 / n**2 + 31.223 / n**3
        return adf_statistic < critical_val

class SymbolData:
    def __init__(self, algorithm, symbol, lookback, resolution):
        self._algorithm = algorithm
        self.window = RollingWindow[float](lookback)
        self._log_return = LogReturn(1)
        self._consolidator = TradeBarConsolidator(timedelta(days=1) if resolution == Resolution.DAILY else timedelta(minutes=1))

        def on_updated(sender, updated):
            self.window.add(updated.value)
        self._log_return.updated += on_updated
        algorithm.register_indicator(symbol, self._log_return, self._consolidator)

        start = algorithm.time - timedelta(days=lookback * 2)
        history = algorithm.history[TradeBar](symbol, start, algorithm.time, resolution, data_normalization_mode=DataNormalizationMode.RAW)
        for bar in list(history)[:-1]:
            self._consolidator.update(bar)

    def dispose(self, algorithm):
        self._log_return.reset()
        self.window.reset()
        algorithm.deregister_indicator(self._log_return)

    @property
    def is_ready(self):
        return self.window.is_ready