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

# Fetch historical data (daily bars, adjust duration/endDate)
# variable = class with parameters
gld_contract = Stock('GLD', 'SMART', 'USD')
gdx_contract = Stock('GDX', 'SMART', 'USD')
# ib object was created earlier in line 11, "reqHistoricalData" is like a function call
# bars_gld stores a list of BarData objects from ib.reqHistoricalData, which fetches 10 years of daily 
# adjusted closing prices for GLD during regular trading hours.
bars_gld = ib.reqHistoricalData(gld_contract, endDateTime='', durationStr='3 Y', barSizeSetting='1 day', whatToShow='ADJUSTED_LAST', useRTH=True)
bars_gdx = ib.reqHistoricalData(gdx_contract, endDateTime='', durationStr='3 Y', barSizeSetting='1 day', whatToShow='ADJUSTED_LAST', useRTH=True)

# CONVERT DATA ***********************************************************************************************************************************

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

# DISCONNECT AFTER DATA FETCH IS COMPLETE ****************************************************************************************************

# Disconnect after fetch
ib.disconnect()

# SPLIT THE DATA ***************************************************************************************************************************

# Rest of code (with adjustments)
# Calculates index for splitting data: 70% for training, 30% for testing. Defines boundary for train/test split.
train_end = int(len(df) * 0.7)
# Creates array of indices for training set (first 70% of rows)
trainset = np.arange(0, train_end)
# Creates array of indices for test set (remaining 30%)
testset = np.arange(train_end, len(df))

# OLS REGRESSION ****************************************************************************************************************************

# Adds a constant (intercept) to GDX prices in training set for OLS regression. Prepares independent variable (GDX) 
# for regression to estimate hedge ratio.
# This line is part of your pairs trading strategy, where you’re likely modeling the relationship between two assets 
# (GLD and GDX) using Ordinary Least Squares (OLS) regression via the statsmodels library (aliased as sm). The goal is to 
# estimate the hedge ratio (the coefficient $\beta$ in the regression $ Y = \beta X + \alpha $, where $ Y $ is GLD prices, 
# $ X $ is GDX prices, and $\alpha$ is the intercept). The exog variable is being prepared as the independent variable for this regression.
# Accesses the column labeled 'Adj Close_GDX' in the pandas DataFrame df.
# ".iloc[trainset]" Selects a subset of rows from the 'Adj Close_GDX' Series using the trainset indices.
# Example: If trainset = [0, 1, ..., 999] (first 1000 rows), df['Adj Close_GDX'].iloc[trainset] extracts the adjusted closing prices 
# for GDX for those 1000 rows.
# "sm.add_constant(...)" Adds a column of 1s to the GDX price data to represent the intercept term ($\alpha$) in the OLS regression.
# sm is the alias for statsmodels.api, and add_constant is a utility function that prepends a column of 1s to the input data 
# (a pandas Series or DataFrame).
# sm is the alias for statsmodels.api, and add_constant is a utility function that prepends a column of 1s to the input data 
# (a pandas Series or DataFrame).
# exog represents the GDX prices (plus the constant) used to predict GLD prices in the regression, yielding the hedge ratio.
exog = sm.add_constant(df['Adj Close_GDX'].iloc[trainset])  # Add intercept
# Sets up OLS regression: GLD prices (dependent) ~ GDX prices + constant (independent) on training data.
# Models relationship to find hedge ratio (β).
model = sm.OLS(df['Adj Close_GLD'].iloc[trainset], exog)
# Fits the OLS model, computing coefficients.
# Estimates β (hedge ratio) for spread calculation.
results = model.fit()
# Extracts β coefficient (GDX’s weight, index 1 due to intercept). Defines hedge ratio for spread (GLD - β * GDX).
hedgeRatio = results.params[1]  # Beta (skip constant)
# Computes spread = GLD - β * GDX for all dates. 
spread = df['Adj Close_GLD'] - hedgeRatio * df['Adj Close_GDX']

# PLOT DATA ****************************************************************************************************************************

# Plots spread for training and test sets to visualize mean reversion.
plt.plot(spread.iloc[trainset])
plt.plot(spread.iloc[testset])
plt.show()

# DATA CALCULATIONS ***********************************************************************************************************************

# Calculates mean of spread in training set. Used for z-score normalization.
spreadMean = np.mean(spread.iloc[trainset])
# Calculates standard deviation of spread in training set. Used for z-score scaling.
spreadStd = np.std(spread.iloc[trainset])

# Computes z-score: (spread - mean) / std for all dates. Standardizes spread for trade signals (entry/exit).
df['zscore'] = (spread - spreadMean) / spreadStd

# CONDITIONS FOR ENTRY AND EXIT *******************************************************************************************************

# Initializes position columns to 0 for long/short trades. Sets up columns to track trading positions (unit shares).
df['positions_GLD_Long'] = 0
df['positions_GDX_Long'] = 0
df['positions_GLD_Short'] = 0
df['positions_GDX_Short'] = 0

# If z-score ≥ 2, short spread: short 1 GLD, long 1 GDX. Signals entry for shorting overvalued spread.
df.loc[df.zscore >= 2, ('positions_GLD_Short', 'positions_GDX_Short')] = [-1, 1]
# If z-score ≤ -2, long spread: long 1 GLD, short 1 GDX. Signals entry for buying undervalued spread. 
df.loc[df.zscore <= -2, ('positions_GLD_Long', 'positions_GDX_Long')] = [1, -1]
# If z-score ≤ 1, exit short spread position. Closes short trade when spread reverts.
df.loc[df.zscore <= 1, ('positions_GLD_Short', 'positions_GDX_Short')] = 0
# If z-score ≥ -1, exit long spread position. Closes long trade when spread reverts.
df.loc[df.zscore >= -1, ('positions_GLD_Long', 'positions_GDX_Long')] = 0

# Forward-fills positions to carry forward until exit signal. Maintains open positions between entry/exit.
df = df.ffill()  # Updated fill

# Extracts long position columns. Isolates long trades for combining positions.
positions_Long = df[['positions_GLD_Long', 'positions_GDX_Long']]
# Extracts short position columns. Isolates short trades for combining positions.
positions_Short = df[['positions_GLD_Short', 'positions_GDX_Short']]
# Combines long and short positions into total positions (NumPy array). Aggregates net positions for GLD/GDX.
positions = np.array(positions_Long) + np.array(positions_Short)
# Converts positions back to DataFrame with proper index and column names. Formats positions for P&L calculation.
positions = pd.DataFrame(positions, index=df.index, columns=['GLD', 'GDX'])

# Computes daily % returns for GLD/GDX. Provides returns for P&L calculation.
dailyret = df[['Adj Close_GLD', 'Adj Close_GDX']].pct_change()
# Calculates daily P&L: lagged positions * daily returns, summed across assets. Computes strategy’s daily profit/loss. 
pnl = (np.array(positions.shift()) * np.array(dailyret)).sum(axis=1)

# Computes annualized Sharpe ratio for training set (skip first for lag). Measures risk-adjusted performance in training.
sharpeTrainset = np.sqrt(252) * np.mean(pnl[trainset[1:]]) / np.std(pnl[trainset[1:]]) if np.std(pnl[trainset[1:]]) > 0 else 0
# Computes Sharpe ratio for test set. Evaluates out-of-sample performance.
sharpeTestset = np.sqrt(252) * np.mean(pnl[testset]) / np.std(pnl[testset]) if np.std(pnl[testset]) > 0 else 0
# Prints Sharpe ratios for training and test sets. Displays performance metrics for analysis.
print(f'Training Sharpe: {sharpeTrainset}')
print(f'Test Sharpe: {sharpeTestset}')

# Plots cumulative P&L for test set. Visualizes strategy profitability over time. 
plt.plot(np.cumsum(pnl[testset]))
# Displays the P&L plot. Shows equity curve for manual review.
plt.show()

# Saves positions DataFrame to a pickle file in C:\Users\jorge_388iox0\Desktop\pairs_trading2. Stores results for future analysis.
positions.to_pickle('example3_6_positions.pkl')
