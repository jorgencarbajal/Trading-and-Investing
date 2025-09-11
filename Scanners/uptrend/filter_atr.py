# LIBRARIES ***************************************************************************************
from ib_insync import *  # For connecting to Interactive Brokers TWS API
import pandas as pd  # For handling the stock list and data manipulation
import talib  # For calculating Average True Range (ATR)
import time  # For adding delays to respect IB API rate limits
from tqdm import tqdm  # For progress bar tracking
import numpy as np  # For NaN checks in ATR calculations

# FUNCTION TO FILTER STOCKS BY ATR ***************************************************************
def filter_by_atr(csv_file, min_atr=1.0, atr_period=14, data_days=50):
    """
    Filter stocks from a CSV file based on the latest Average True Range (ATR) value.
    Args:
        csv_file (str): Path to the CSV file with stock symbols
        min_atr (float): Minimum ATR value (default: 1.0)
        atr_period (int): Period for ATR calculation (default: 14)
        data_days (int): Number of days of historical data to fetch (should be > atr_period * 2 for accuracy)
    Returns:
        pd.DataFrame: Filtered DataFrame with stocks where latest ATR > min_atr
    """
    # Read the CSV file containing stock symbols
    df = pd.read_csv(csv_file)
    
    # Initialize IB connection
    ib = IB()
    try:
        # Connect to TWS or IB Gateway
        ib.connect('127.0.0.1', 7497, clientId=1)
        
        # Suppress IB API error messages for invalid contracts
        ib.errorEvent += lambda reqId, errorCode, errorString, contract: None
        
        # Initialize list for filtered stocks
        filtered_stocks = []
        
        # Get total symbols for progress tracking
        total_symbols = len(df)
        
        # Loop through each stock symbol with progress bar
        for symbol in tqdm(df['Symbol'], total=total_symbols, desc="Scanning stocks for ATR"):
            try:
                # Create a Stock contract (US stock, SMART exchange for broader coverage)
                contract = Stock(symbol, 'SMART', 'USD', primaryExchange='NYSE')
                
                # Qualify the contract
                qualified_contracts = ib.qualifyContracts(contract)
                
                if qualified_contracts:
                    contract = qualified_contracts[0]
                    
                    # Request historical data
                    bars = ib.reqHistoricalData(
                        contract,
                        endDateTime='',
                        durationStr=f'{data_days} D',
                        barSizeSetting='1 day',
                        whatToShow='TRADES',
                        useRTH=True,
                        formatDate=1,
                        keepUpToDate=False
                    )
                    
                    if bars and len(bars) >= atr_period:
                        # Convert bars to DataFrame
                        hist_data = util.df(bars)
                        
                        # Calculate ATR using TA-Lib
                        atr_values = talib.ATR(
                            hist_data['high'].values,
                            hist_data['low'].values,
                            hist_data['close'].values,
                            timeperiod=atr_period
                        )
                        latest_atr = atr_values[-1]
                        
                        # Check if ATR is valid and exceeds threshold
                        if not np.isnan(latest_atr) and latest_atr > min_atr:
                            stock_data = df[df['Symbol'] == symbol].to_dict('records')[0]
                            filtered_stocks.append(stock_data)
                            print(f"✓ {symbol}: ATR {latest_atr:.2f} (passed)")
                        else:
                            print(f"✗ {symbol}: ATR {latest_atr:.2f} <= {min_atr} or invalid")
                    else:
                        print(f"✗ {symbol}: Insufficient data (need at least {atr_period} bars)")
                else:
                    print(f"✗ {symbol}: Invalid contract")
                    
            except Exception as e:
                print(f"✗ {symbol}: Error - {str(e)[:50]}...")
            
            # Delay for API rate limits (0.2s for ~5 req/s)
            time.sleep(0.2)
        
        # Convert filtered stocks to DataFrame
        filtered_df = pd.DataFrame(filtered_stocks)
        
        return filtered_df
    
    except Exception as e:
        print(f"Error during IB API operations: {e}")
        return pd.DataFrame()
    
    finally:
        ib.disconnect()

# MAIN SCRIPT ************************************************************************************
if __name__ == "__main__":
    # Path to the input CSV file
    csv_file = r'C:\Users\jorge_388iox0\OneDrive\OneDrive\Trading\QuantitativeTrading\Scanners\golden_stack_uptrend\nyse_high_rel_volume_stocks.csv'
    
    # Filter stocks by ATR (>1, 14-period, fetching 50 days of data)
    filtered_stocks = filter_by_atr(csv_file, min_atr=1.0, atr_period=14, data_days=50)
    
    # Check if the filtered DataFrame is not empty
    if not filtered_stocks.empty:
        # Print the number of stocks meeting the ATR criterion
        print(f"\nFound {len(filtered_stocks)} stocks with ATR > 1.0:")
        
        # Print the first few rows to verify
        print(filtered_stocks.head())
        
        # Save the filtered DataFrame to a new CSV file
        output_path = r'C:\Users\jorge_388iox0\OneDrive\OneDrive\Trading\QuantitativeTrading\Scanners\golden_stack_uptrend\nyse_high_atr_stocks.csv'
        filtered_stocks.to_csv(output_path, index=False)
        
        # Confirm the file was saved
        print(f"Saved to '{output_path}'")
    else:
        print("No stocks met the ATR criterion or an error occurred.")