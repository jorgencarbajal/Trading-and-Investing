# NECESSARY LIBRARIES

import numpy as np # library for arrays/math
import pandas as pd # library for data handling
import matplotlib.pyplot as plt # provides functions to create various plots: line plots, scatter plots, histograms, bar charts, etc.
import statsmodels.api as sm # statsmodels is a Python library designed for statistical modeling, estimation, and hypothesis testing.
# It provides tools for conducting statistical analyses, including regression models, time-series analysis, and more.
from ib_insync import *  # For TWS API (data fetching)

# CONNECT TO IB

# Connect to TWS (must be open, API port 7497 for paper, 7496 live)
# The IB object is the main interface for interacting with Interactive Brokers' Trader Workstation (TWS) or IB Gateway. It allows you 
# to connect to the IB platform, request market data, place orders, and manage account information programmatically.
ib = IB() 
# This line connects the IB object to the Interactive Brokers platform (TWS or IB Gateway) running on your local machine.
ib.connect('127.0.0.1', 7497, clientId=1)  # Adjust port/clientId

# FETCH DATA

# Fetch historical data (daily bars, adjust duration/endDate)
# variable = class with parameters
gld_contract = Stock('GLD', 'SMART', 'USD')
gdx_contract = Stock('GDX', 'SMART', 'USD')
# ib object was created earlier in line 11, "reqHistoricalData" is like a function call
# bars_gld stores a list of BarData objects from ib.reqHistoricalData, which fetches 10 years of daily 
# adjusted closing prices for GLD during regular trading hours.
bars_gld = ib.reqHistoricalData(gld_contract, endDateTime='', durationStr='10 Y', barSizeSetting='1 day', whatToShow='ADJUSTED_LAST', useRTH=True)
bars_gdx = ib.reqHistoricalData(gdx_contract, endDateTime='', durationStr='10 Y', barSizeSetting='1 day', whatToShow='ADJUSTED_LAST', useRTH=True)

# Convert to DataFrames
# Converts GLD/GDX historical data (from TWS API) to a Pandas DataFrame using ib_insync's utility function. Prepares GLD/GDX data for analysis.
df_gld = util.df(bars_gld)
df_gdx = util.df(bars_gdx)
# Selects 'date' and 'close' columns from GLD/GDX DataFrame, renames 'close' to 'Adj Close_GLD' for consistency with strategy.
df_gld = df_gld[['date', 'close']].rename(columns={'close': 'Adj Close_GLD'})
df_gdx = df_gdx[['date', 'close']].rename(columns={'close': 'Adj Close_GDX'})
# Merges GLD and GDX DataFrames on 'date' column, keeping only matching dates (inner join)
# GLD/GDX prices into a single DataFrame for pairs analysis.
df = pd.merge(df_gld, df_gdx, on='date', how='inner')
# Sets 'date' as the DataFrame index (time series format).Ensures data is indexed by date for chronological processing.
df.set_index('date', inplace=True)
# Sorts DataFrame by date (ascending) to ensure correct time order.
df.sort_index(inplace=True)

# Disconnect after fetch
ib.disconnect()

# Rest of code (with adjustments)
# Calculates index for splitting data: 70% for training, 30% for testing. Defines boundary for train/test split.
train_end = int(len(df) * 0.7)

trainset = np.arange(0, train_end)
testset = np.arange(train_end, len(df))

exog = sm.add_constant(df['Adj Close_GDX'].iloc[trainset])  # Add intercept
model = sm.OLS(df['Adj Close_GLD'].iloc[trainset], exog)
results = model.fit()
hedgeRatio = results.params[1]  # Beta (skip constant)

spread = df['Adj Close_GLD'] - hedgeRatio * df['Adj Close_GDX']
plt.plot(spread.iloc[trainset])
plt.plot(spread.iloc[testset])
plt.show()

spreadMean = np.mean(spread.iloc[trainset])
spreadStd = np.std(spread.iloc[trainset])

df['zscore'] = (spread - spreadMean) / spreadStd
df['positions_GLD_Long'] = 0
df['positions_GDX_Long'] = 0
df['positions_GLD_Short'] = 0
df['positions_GDX_Short'] = 0

df.loc[df.zscore >= 2, ('positions_GLD_Short', 'positions_GDX_Short')] = [-1, 1]
df.loc[df.zscore <= -2, ('positions_GLD_Long', 'positions_GDX_Long')] = [1, -1]
df.loc[df.zscore <= 1, ('positions_GLD_Short', 'positions_GDX_Short')] = 0
df.loc[df.zscore >= -1, ('positions_GLD_Long', 'positions_GDX_Long')] = 0

df = df.ffill()  # Updated fill

positions_Long = df[['positions_GLD_Long', 'positions_GDX_Long']]
positions_Short = df[['positions_GLD_Short', 'positions_GDX_Short']]
positions = np.array(positions_Long) + np.array(positions_Short)
positions = pd.DataFrame(positions, index=df.index, columns=['GLD', 'GDX'])

dailyret = df[['Adj Close_GLD', 'Adj Close_GDX']].pct_change()
pnl = (np.array(positions.shift()) * np.array(dailyret)).sum(axis=1)

sharpeTrainset = np.sqrt(252) * np.mean(pnl[trainset[1:]]) / np.std(pnl[trainset[1:]]) if np.std(pnl[trainset[1:]]) > 0 else 0
sharpeTestset = np.sqrt(252) * np.mean(pnl[testset]) / np.std(pnl[testset]) if np.std(pnl[testset]) > 0 else 0
print(f'Training Sharpe: {sharpeTrainset}')
print(f'Test Sharpe: {sharpeTestset}')

plt.plot(np.cumsum(pnl[testset]))
plt.show()

positions.to_pickle('example3_6_positions.pkl')
