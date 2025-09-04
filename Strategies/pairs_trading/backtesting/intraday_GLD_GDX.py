import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from ib_insync import *

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

gld_contract = Stock('GLD', 'SMART', 'USD')
gdx_contract = Stock('GDX', 'SMART', 'USD')
bars_gld = ib.reqHistoricalData(gld_contract, endDateTime='', durationStr='30 D', barSizeSetting='5 mins', whatToShow='ADJUSTED_LAST', useRTH=True)
bars_gdx = ib.reqHistoricalData(gdx_contract, endDateTime='', durationStr='30 D', barSizeSetting='5 mins', whatToShow='ADJUSTED_LAST', useRTH=True)

df_gld = util.df(bars_gld)[['date', 'close']].rename(columns={'close': 'Adj Close_GLD'})
df_gdx = util.df(bars_gdx)[['date', 'close']].rename(columns={'close': 'Adj Close_GDX'})
df = pd.merge(df_gld, df_gdx, on='date', how='inner')
df.set_index('date', inplace=True)
df.sort_index(inplace=True)
print(f"Data rows: {len(df)}")

ib.disconnect()

train_end = int(len(df) * 0.7)
trainset = np.arange(0, train_end)
testset = np.arange(train_end, len(df))

exog = sm.add_constant(df['Adj Close_GDX'].iloc[trainset])
model = sm.OLS(df['Adj Close_GLD'].iloc[trainset], exog)
results = model.fit()
hedgeRatio = results.params.iloc[1]
print(f"Hedge ratio: {hedgeRatio}")

spread = df['Adj Close_GLD'] - hedgeRatio * df['Adj Close_GDX']

best_sharpe = -np.inf
best_entry = 1.5
for entry in np.arange(1.0, 2.1, 0.1):
    df['zscore'] = (spread - np.mean(spread.iloc[trainset])) / np.std(spread.iloc[trainset])
    df['positions_GLD_Long'] = 0
    df['positions_GDX_Long'] = 0
    df['positions_GLD_Short'] = 0
    df['positions_GDX_Short'] = 0
    df.loc[df.zscore >= entry, ('positions_GLD_Short', 'positions_GDX_Short')] = [-1, 1]
    df.loc[df.zscore <= -entry, ('positions_GLD_Long', 'positions_GDX_Long')] = [1, -1]
    df.loc[df.zscore <= 0.5, ('positions_GLD_Short', 'positions_GDX_Short')] = 0
    df.loc[df.zscore >= -0.5, ('positions_GLD_Long', 'positions_GDX_Long')] = 0
    df = df.ffill()
    positions = df[['positions_GLD_Long', 'positions_GDX_Long']] + df[['positions_GLD_Short', 'positions_GDX_Short']]
    positions = pd.DataFrame(positions, index=df.index, columns=['GLD', 'GDX'])
    dailyret = df[['Adj Close_GLD', 'Adj Close_GDX']].pct_change()
    pnl = (np.array(positions.shift()) * np.array(dailyret)).sum(axis=1)
    sharpe = np.sqrt(252 * 78) * np.mean(pnl[trainset[1:]]) / np.std(pnl[trainset[1:]]) if np.std(pnl[trainset[1:]]) > 0 else 0
    if sharpe > best_sharpe:
        best_sharpe = sharpe
        best_entry = entry

spreadMean = np.mean(spread.iloc[trainset])
spreadStd = np.std(spread.iloc[trainset])
df['zscore'] = (spread - spreadMean) / spreadStd
df['positions_GLD_Long'] = 0
df['positions_GDX_Long'] = 0
df['positions_GLD_Short'] = 0
df['positions_GDX_Short'] = 0
df.loc[df.zscore >= best_entry, ('positions_GLD_Short', 'positions_GDX_Short')] = [-1, 1]
df.loc[df.zscore <= -best_entry, ('positions_GLD_Long', 'positions_GDX_Long')] = [1, -1]
df.loc[df.zscore <= 0.5, ('positions_GLD_Short', 'positions_GDX_Short')] = 0
df.loc[df.zscore >= -0.5, ('positions_GLD_Long', 'positions_GDX_Long')] = 0
df = df.ffill()

positions_Long = df[['positions_GLD_Long', 'positions_GDX_Long']]
positions_Short = df[['positions_GLD_Short', 'positions_GDX_Short']]
positions = np.array(positions_Long) + np.array(positions_Short)
positions = pd.DataFrame(positions, index=df.index, columns=['GLD', 'GDX'])

dailyret = df[['Adj Close_GLD', 'Adj Close_GDX']].pct_change()
pnl = (np.array(positions.shift()) * np.array(dailyret)).sum(axis=1)

sharpeTrainset = np.sqrt(252 * 78) * np.mean(pnl[trainset[1:]]) / np.std(pnl[trainset[1:]]) if np.std(pnl[trainset[1:]]) > 0 else 0
sharpeTestset = np.sqrt(252 * 78) * np.mean(pnl[testset]) / np.std(pnl[testset]) if np.std(pnl[testset]) > 0 else 0
print(f"Training Sharpe: {sharpeTrainset}")
print(f"Test Sharpe: {sharpeTestset}")
print(f"Trade entries: {len(df.loc[abs(df.zscore) >= best_entry])}")
print(f"Spread std: {spreadStd}")
print(f"Best entry threshold: {best_entry}")

plt.plot(spread.iloc[trainset], label='Train Spread')
plt.plot(spread.iloc[testset], label='Test Spread')
plt.legend()
plt.savefig('C:/Users/jorge_388iox0/Desktop/pairs_trading/pairs_trading_intraday/spread_plot.png')
plt.show()

plt.plot(np.cumsum(pnl[testset]), label='Test P&L')
plt.legend()
plt.savefig('C:/Users/jorge_388iox0/Desktop/pairs_trading/pairs_trading_intraday/pnl_plot.png')
plt.show()

positions.to_pickle('C:/Users/jorge_388iox0/Desktop/pairs_trading/pairs_trading_intraday/intraday_positions.pkl')
