#region imports
from AlgorithmImports import *
from PortfolioConstructionModel import PortfolioConstructionModel
from Portfolio.EqualWeightingPortfolioConstructionModel import EqualWeightingPortfolioConstructionModel
from utils import reset_and_warm_up
#endregion

class EqualWeightingPortfolioConstructionModel(PortfolioConstructionModel):
    def __init__(self, rebalance=None, portfolio_bias=PortfolioBias.LongShort):
        super().__init__(rebalance, portfolio_bias)

    def create_targets(self, algorithm, insights):
        # Equally weight all symbols with active insights
        active_symbols = [insight.symbol for insight in insights]
        if not active_symbols:
            return []
        weight = 1.0 / len(active_symbols)
        return [PortfolioTarget(symbol, weight) for symbol in active_symbols]

class SparseOptimizationPortfolioConstructionModel(EqualWeightingPortfolioConstructionModel):

    '''Using sparse optimization to construct our own replicated portfolio compared to a benchmark
    In this model, we only model the upside while discarding downside datapoints. For details, refer to
    https://www.quantconnect.com/docs/v2/research-environment/applying-research/sparse-optimization
    '''
    def __init__(self, algorithm, benchmark, lookback = 252, resolution = None, 
                 rebalance = Expiry.END_OF_QUARTER, portfolio_bias = PortfolioBias.LONG_SHORT):
        super().__init__(rebalance, portfolio_bias)
        self.algorithm = algorithm
        self.lookback = lookback
        self.resolution = resolution
        self.benchmark = benchmark
        self.w = None

    def determine_target_percent(self, active_insights):
        result = {}

        # get the log return series for the benchmark and composites to construct the replicated portfolio
        pct_change = {symbol: self.returns(self.algorithm.securities[symbol]) for symbol in self.algorithm.securities.keys() \
                        if symbol in [x.symbol for x in active_insights]+[self.benchmark]}
        pct_change = pd.DataFrame(pct_change)
        pct_change = pct_change.fillna(pct_change.mean())
        pct_change_portfolio = pct_change[[x for x in pct_change.columns if x != self.benchmark]].dropna(axis=1)
        if pct_change_portfolio.empty: 
            return {insight: 0 for insight in active_insights}

        pct_change_benchmark = pct_change[self.benchmark].values.reshape(-1, 1)
        active_symbols = pct_change_portfolio.columns
        pct_change_portfolio = pct_change_portfolio.values

        p = 0.1                     # penalty term for exceeding upper limit, between 0 & 1
        M = 0.01                    # huber loss term size to adapt for outliers, between 0 & 1
        l = 0.005                   # minimum size of inclusive constituents, between 0 & 1
        u = 0.10                    # maximum size of inclusive constituents, between 0 & 1
        tol = 0.001                 # optimization problem tolerance
        max_iter = 100               # optimization maximum iteration for speed
        iters = 1                   # counter for number of iteration
        hdr = 10000                 # optimization function output, an arbitary large number as initial state
        
        m = pct_change_portfolio.shape[0]; n = pct_change_portfolio.shape[1]
        # Use previous weightings as starting point if valid, otherwise use equal size
        w_ = self.w.values.reshape(-1, 1) if self.w is not None and self.w.size == n \
            else np.array([1/n] * n).reshape(n, 1)
        # placeholders
        weights = pd.Series()
        a = np.array([None] * m).reshape(m, 1)
        c = np.array([None] * m).reshape(m, 1)
        d = np.array([None] * n).reshape(n, 1)

        # Optimization Methods for Financial Index Tracking: From Theory to Practice. K. Benidis, Y. Feng, D. P. Palomer (2018)
        # https://palomar.home.ece.ust.hk/papers/2018/BenidisFengPalomar-FnT2018.pdf
        while iters < max_iter:
            x_k = (pct_change_benchmark - pct_change_portfolio @ w_)
            for i in range(n):
                w = w_[i]
                d[i] = d_ = 1/(np.log(1+l/p)*(p+w))
            for i in range(m):
                xk = float(x_k[i])
                if xk < 0:
                    a[i] = M / (M - 2*xk)
                    c[i] = xk
                else:
                    c[i] = 0
                    if 0 <= xk <= M:
                        a[i] = 1
                    else:
                        a[i] = M/abs(xk)

            L3 = 1/m * pct_change_portfolio.T @ np.diagflat(a.T) @ pct_change_portfolio
            eig_val, eig_vec = np.linalg.eig(L3.astype(float))
            eig_val = np.real(eig_val); eig_vec = np.real(eig_vec)
            q3 = 1/max(eig_val) * (2 * (L3 - max(eig_val) * np.eye(n)) @ w_ + eig_vec @ d \
                - 2/m * pct_change_portfolio.T @ np.diagflat(a.T) @ (c - pct_change_benchmark))
            
            mu = float(-(np.sum(q3) + 2)/n); mu_ = 0
            while mu > mu_:
                mu = mu_
                index1 = [i for i, q in enumerate(q3) if mu + q < -u*2]
                index2 = [i for i, q in enumerate(q3) if -u*2 < mu + q < 0]
                mu_ = float(-(np.sum([q3[i] for i in index2]) + 2 - len(index1)*u*2)/max(1, len(index2)))

            # Obtain the weights and HDR (optimization function result) of this iteration.
            w_ = np.amax(np.concatenate((-(mu + q3)/2, u*np.ones((n, 1))), axis=1), axis=1).reshape(-1, 1)
            w_ = w_/np.sum(abs(w_))
            hdr_ = float(w_.T @ w_ + q3.T @ w_)

            # If the HDR converges, we take the current weights
            if abs(hdr - hdr_) < tol:
                break

            # Else, we would increase the iteration count and use the current weights for the next iteration.
            iters += 1
            hdr = hdr_
            if all([x != np.nan for x in w_]):
                self.w = pd.Series(data = w_.flatten(), index = active_symbols)
        
        # Normalize the weights
        total_weight = np.sum(np.abs(self.w.values))
        for insight in active_insights:
            symbol = insight.symbol
            if symbol in active_symbols:
                result[insight] = self.w[symbol] / total_weight

        return result

    # added after the fact...
    def create_targets(self, algorithm, insights):
        """Create PortfolioTarget objects from active insights using the
        optimized weights computed by determine_target_percent.
        """
        # Filter active insights (framework typically passes active insights)
        active_insights = [ins for ins in insights if ins is not None]
        if not active_insights:
            return []

        # determine_target_percent returns a mapping insight -> percent
        target_percents = self.determine_target_percent(active_insights)

        targets = []
        for insight in active_insights:
            pct = target_percents.get(insight, 0)
            targets.append(PortfolioTarget(insight.symbol, pct))

        return targets
        
    def on_securities_changed(self, algorithm, changes):
        super().on_securities_changed(algorithm, changes)
        for added in changes.added_securities:
            self.init_security_data(algorithm, added)
        
        for removed in changes.removed_securities:
            self.dispose_security_data(algorithm, removed)

    def handle_corporate_actions(self, algorithm, slice):
        symbols = set(slice.dividends.keys())
        symbols.update(slice.splits.keys())

        for symbol in symbols:
            self.warm_up_indicator(algorithm.securities[symbol])
    
    def warm_up_indicator(self, security):
        self.reset(security)
        security['consolidator'] = reset_and_warm_up(self.algorithm, security, self.resolution, self.lookback)

    def init_security_data(self, algorithm, security):
        # To store the historical daily log return
        security['window'] = RollingWindow[IndicatorDataPoint](self.lookback)

        # Use daily log return to predict cointegrating vector
        security['logr'] = LogReturn(1)
        security['logr'].updated += lambda sender, updated: security['window'].add(IndicatorDataPoint(updated.end_time, updated.value))
        security['consolidator'] = TradeBarConsolidator(timedelta(1))

        # Subscribe the consolidator and indicator to data for automatic update
        algorithm.register_indicator(security.symbol, security['logr'], security['consolidator'])

        self.warm_up_indicator(security)

    def reset(self, security):
        security['logr'].reset()
        security['window'].reset()

    def dispose_security_data(self, algorithm, security):
        self.reset(security)
        algorithm.subscription_manager.remove_consolidator(security.symbol, security['consolidator'])

    def returns(self, security):
        return pd.Series(
            data = [x.value for x in security['window']],
            index = [x.end_time for x in security['window']])[::-1]
    

