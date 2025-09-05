# IMPORT LIBRARIES **********************************************************************************************************************************
# Import numpy for numerical operations and array handling
import numpy as np
# Import pandas for data manipulation and DataFrame structures
import pandas as pd
# Import ib_insync for Interactive Brokers API to fetch real-time data and place orders
from ib_insync import *
# Import time for managing delays between API calls
import time
# Import os to create directories for saving logs
import os

# CONNECT TO INTERACTIVE BROKERS ********************************************************************************************************************
# Initialize Interactive Brokers client instance for paper trading
ib = IB()
# Connect to IB TWS or Gateway on localhost, port 7497, client ID 1 (paper trading mode)
ib.connect('127.0.0.1', 7497, clientId=1)

# DEFINE STOCK CONTRACTS AND INITIAL DATA ************************************************************************************************************
# Define GLD stock contract (SPDR Gold Shares ETF, traded in USD on SMART exchange)
gld_contract = Stock('GLD', 'SMART', 'USD')
# Define GDX stock contract (VanEck Gold Miners ETF, traded in USD on SMART exchange)
gdx_contract = Stock('GDX', 'SMART', 'USD')
# Qualify contracts with IB to ensure valid definitions
ib.qualifyContracts(gld_contract)
ib.qualifyContracts(gdx_contract)

# Set initial parameters (modifiable for optimization)
# Hedge ratio from backtest (0.48), can be updated with real-time regression if desired
hedge_ratio = 0.48
# Mean and standard deviation of spread from backtest (modify based on latest training data)
spread_mean = 285.0  # Approx from backtest, adjust with new data
spread_std = 2.25   # Approx from backtest, adjust with new data
# Entry threshold for z-score (1.0 from backtest), can be modified for better results
entry_threshold = 1.0
# Exit threshold for z-score (0.5 from backtest), can be modified for better results
exit_threshold = 0.5
# Position size in shares (100 here), can be modified based on account size or risk tolerance
position_size = 100

# Initialize position tracking (0 = flat, 1 = long spread, -1 = short spread)
current_position = 0
# Initialize DataFrame to store historical data for z-score calculation
data_df = pd.DataFrame(columns=['date', 'Adj Close_GLD', 'Adj Close_GDX'])

# CREATE OUTPUT DIRECTORY FOR LOGS ******************************************************************************************************************
# Define output directory path for saving trade logs
output_dir = 'C:/Users/jorge_388iox0/Desktop/pairs_trading/pairs_trading_intraday/paper_trading_logs'
# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# PAPER TRADING LOOP *******************************************************************************************************************************
# Main loop to run paper trading (runs indefinitely, stop manually or add condition)
while True:
    try:
        # Fetch latest market data for GLD and GDX
        # Request 1-minute bars for real-time updates, adjust duration/barSize for granularity
        bars_gld = ib.reqHistoricalData(gld_contract, endDateTime='', durationStr='1 D', barSizeSetting='1 min', whatToShow='ADJUSTED_LAST', useRTH=True)
        bars_gdx = ib.reqHistoricalData(gdx_contract, endDateTime='', durationStr='1 D', barSizeSetting='1 min', whatToShow='ADJUSTED_LAST', useRTH=True)

        # Convert to DataFrame, keeping only latest bar
        df_gld = util.df(bars_gld).tail(1)[['date', 'close']].rename(columns={'close': 'Adj Close_GLD'})
        df_gdx = util.df(bars_gdx).tail(1)[['date', 'close']].rename(columns={'close': 'Adj Close_GDX'})
        # Merge latest data
        latest_data = pd.merge(df_gld, df_gdx, on='date', how='inner')
        # Append to historical data
        data_df = pd.concat([data_df, latest_data]).drop_duplicates(subset=['date'], keep='last')

        # Calculate spread using latest prices
        current_spread = latest_data['Adj Close_GLD'].iloc[0] - hedge_ratio * latest_data['Adj Close_GDX'].iloc[0]
        # Calculate z-score using rolling mean and std (minimum 100 bars for stability, modifiable)
        if len(data_df) > 100:
            z_score = (current_spread - data_df['Adj Close_GLD'].rolling(100).mean().iloc[-1] + 
                       hedge_ratio * data_df['Adj Close_GDX'].rolling(100).mean().iloc[-1]) / \
                      (data_df['Adj Close_GLD'].rolling(100).std().iloc[-1] + 
                       hedge_ratio * data_df['Adj Close_GDX'].rolling(100).std().iloc[-1])
        else:
            z_score = (current_spread - spread_mean) / spread_std  # Fallback to backtest values

        # Log current state to file
        with open(f'{output_dir}/trade_log.txt', 'a') as f:
            f.write(f"Time: {time.ctime()}, Spread: {current_spread}, Z-Score: {z_score}, Position: {current_position}\n")

        # Decision logic for entering/exiting trades
        if current_position == 0:  # Flat position
            if z_score <= -entry_threshold:
                # Enter long spread: buy GLD, sell GDX (beta-adjusted)
                ib.placeOrder(gld_contract, MarketOrder('BUY', position_size))
                ib.placeOrder(gdx_contract, MarketOrder('SELL', int(position_size * hedge_ratio)))
                current_position = 1
                with open(f'{output_dir}/trade_log.txt', 'a') as f:
                    f.write(f"Entered Long Spread at Z-Score: {z_score}\n")
            elif z_score >= entry_threshold:
                # Enter short spread: sell GLD, buy GDX (beta-adjusted)
                ib.placeOrder(gld_contract, MarketOrder('SELL', position_size))
                ib.placeOrder(gdx_contract, MarketOrder('BUY', int(position_size * hedge_ratio)))
                current_position = -1
                with open(f'{output_dir}/trade_log.txt', 'a') as f:
                    f.write(f"Entered Short Spread at Z-Score: {z_score}\n")
        else:  # In a position
            if current_position == 1 and z_score >= exit_threshold:
                # Exit long spread
                ib.placeOrder(gld_contract, MarketOrder('SELL', position_size))
                ib.placeOrder(gdx_contract, MarketOrder('BUY', int(position_size * hedge_ratio)))
                current_position = 0
                with open(f'{output_dir}/trade_log.txt', 'a') as f:
                    f.write(f"Exited Long Spread at Z-Score: {z_score}\n")
            elif current_position == -1 and z_score <= -exit_threshold:
                # Exit short spread
                ib.placeOrder(gld_contract, MarketOrder('BUY', position_size))
                ib.placeOrder(gdx_contract, MarketOrder('SELL', int(position_size * hedge_ratio)))
                current_position = 0
                with open(f'{output_dir}/trade_log.txt', 'a') as f:
                    f.write(f"Exited Short Spread at Z-Score: {z_score}\n")

        # Wait before next iteration (e.g., 60 seconds, modifiable for frequency)
        time.sleep(60)

    except Exception as e:
        # Log any errors and continue
        with open(f'{output_dir}/trade_log.txt', 'a') as f:
            f.write(f"Error: {str(e)}\n")
        time.sleep(60)  # Wait before retrying

# Note: This loop runs indefinitely. Stop with Ctrl+C or add a condition (e.g., time limit) to exit.
