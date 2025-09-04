# NECESSARY LIBRARIES *************************************************************************************************************************

import numpy as np # library for arrays/math
import pandas as pd # library for data handling
import matplotlib.pyplot as plt # provides functions to create various plots: line plots, scatter plots, histograms, bar charts, etc.
import statsmodels.api as sm # statsmodels is a Python library designed for statistical modeling, estimation, and hypothesis testing.
# It provides tools for conducting statistical analyses, including regression models, time-series analysis, and more.
from ib_insync import *  # For TWS API (data fetching)

# CONNECT TO IB *******************************************************************************************************************************

# Connect to TWS (must be open, API port 7497 for paper, 7496 live)
# The IB object is the main interface for interacting with Interactive Brokers' Trader Workstation (TWS) or IB Gateway. It allows you 
# to connect to the IB platform, request market data, place orders, and manage account information programmatically.
ib = IB() 
# This line connects the IB object to the Interactive Brokers platform (TWS or IB Gateway) running on your local machine.
ib.connect('127.0.0.1', 7497, clientId=1)  # Adjust port/clientId

# FETCH DATA ***********************************************************************************************************************************

# Fetch historical data (daily bars, 3 years)
gld_contract = Stock('GLD', 'SMART', 'USD')
gdx_contract = Stock('GDX', 'SMART', 'USD')
bars_gld = ib.reqHistoricalData(gld_contract, endDateTime='', durationStr='3 Y', barSizeSetting='1 day', whatToShow='ADJUSTED_LAST', useRTH=True)
bars_gdx = ib.reqHistoricalData(gdx_contract, endDateTime='', durationStr='3 Y', barSizeSetting='1 day', whatToShow='ADJUSTED_LAST', useRTH=True)

# Convert to DataFrames
df_gld = util.df(bars_gld)
df_gdx = util.df(bars_gdx)
print(f"GLD rows: {len(df_gld)}, GDX rows: {len(df_gdx)}")  # Debug
df_gld = df_gld[['date', 'close']].rename(columns={'close': 'Adj Close_GLD'})
df_gdx = df_gdx[['date', 'close']].rename(columns={'close': 'Adj Close_GDX'})
df = pd.merge(df_gld, df_gdx, on='date', how='inner')
df.set_index('date', inplace=True)
df.sort_index(inplace=True)
print(f"Data rows after merge: {len(df)}")  # Debug

# Disconnect after fetch
ib.disconnect()

# Rest of code
train_end = int(len(df) * 0.7)
trainset = np.arange(0, train_end)
testset = np.arange(train_end, len(df))
print(f"Train rows: {len(trainset)}, Test rows: {len(testset)}")  # Debug

exog = sm.add_constant(df['Adj Close_GDX'].iloc[trainset])
model = sm.OLS(df['Adj Close_GLD'].iloc[trainset], exog)
results = model.fit()
hedgeRatio = results.params.iloc[1]  # Fixed to avoid warning
print(f"Hedge ratio: {hedgeRatio}")  # Debug

spread = df['Adj Close_GLD'] - hedgeRatio * df['Adj Close_GDX']
plt.plot(spread.iloc[trainset], label='Train Spread')
plt.plot(spread.iloc[testset], label='Test Spread')
plt.legend()
plt.savefig('C:/Users/jorge_388iox0/Desktop/pairs_trading2/spread_plot.png')
plt.show()
print("Spread plot displayed")  # Debug

spreadMean = np.mean(spread.iloc[trainset])
spreadStd = np.std(spread.iloc[trainset])
print(f"Spread mean: {spreadMean}, Std: {spreadStd}")  # Debug

df['zscore'] = (spread - spreadMean) / spreadStd
df['positions_GLD_Long'] = 0
df['positions_GDX_Long'] = 0
df['positions_GLD_Short'] = 0
df['positions_GDX_Short'] = 0

df.loc[df.zscore >= 2, ('positions_GLD_Short', 'positions_GDX_Short')] = [-1, 1]
df.loc[df.zscore <= -2, ('positions_GLD_Long', 'positions_GDX_Long')] = [1, -1]
df.loc[df.zscore <= 1, ('positions_GLD_Short', 'positions_GDX_Short')] = 0
df.loc[df.zscore >= -1, ('positions_GLD_Long', 'positions_GDX_Long')] = 0

df = df.ffill()
print("Positions assigned")  # Debug

positions_Long = df[['positions_GLD_Long', 'positions_GDX_Long']]
positions_Short = df[['positions_GLD_Short', 'positions_GDX_Short']]
positions = np.array(positions_Long) + np.array(positions_Short)
positions = pd.DataFrame(positions, index=df.index, columns=['GLD', 'GDX'])

dailyret = df[['Adj Close_GLD', 'Adj Close_GDX']].pct_change()
pnl = (np.array(positions.shift()) * np.array(dailyret)).sum(axis=1)
print(f"P&L sample: {pnl[:5]}")  # Debug

sharpeTrainset = np.sqrt(252) * np.mean(pnl[trainset[1:]]) / np.std(pnl[trainset[1:]]) if np.std(pnl[trainset[1:]]) > 0 else 0
sharpeTestset = np.sqrt(252) * np.mean(pnl[testset]) / np.std(pnl[testset]) if np.std(pnl[testset]) > 0 else 0
print(f'Training Sharpe: {sharpeTrainset}')
print(f'Test Sharpe: {sharpeTestset}')

plt.plot(np.cumsum(pnl[testset]))
plt.savefig('C:/Users/jorge_388iox0/Desktop/pairs_trading2/pnl_plot.png')
plt.show()
print("P&L plot displayed")  # Debug

positions.to_pickle('C:/Users/jorge_388iox0/Desktop/pairs_trading2/example3_6_positions.pkl')
print("Positions saved")  # Debug
