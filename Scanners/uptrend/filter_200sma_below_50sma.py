# LIBRARIES ***************************************************************************************
from ib_insync import *  # For connecting to Interactive Brokers TWS API
import pandas as pd  # For handling the stock list and data manipulation
import talib  # For calculating Simple Moving Average (SMA)
import time  # For adding delays to respect IB API rate limits
from tqdm import tqdm  # For progress bar tracking

# FUNCTION TO FILTER STOCKS BY 200 SMA BELOW 50 SMA **********************************************
def filter_by_200sma_below_50sma(csv_file, sma_short=50, sma_long=200, data_days=200):
    """
    Filter stocks from a CSV file where the 200-day SMA is below the 50-day SMA.
    Args:
        csv_file (str): Path to the CSV file with stock symbols
        sma_short (int): Period for shorter SMA (default: 50)
        sma_long (int): Period for longer SMA (default: 200)
        data_days (int): Number of days of historical data to fetch (default: 200)
    Returns:
        pd.DataFrame: Filtered DataFrame with stocks where 200 SMA < 50 SMA
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
        for symbol in tqdm(df['Symbol'], total=total_symbols, desc="Scanning stocks for 200 SMA < 50 SMA"):
            try:
                # Create a Stock contract (US stock, SMART exchange)
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
                    
                    if bars and len(bars) >= sma_long:
                        # Convert bars to DataFrame
                        hist_data = util.df(bars)
                        
                        # Calculate SMAs
                        sma_50 = talib.SMA(hist_data['close'].values, timeperiod=sma_short)
                        sma_200 = talib.SMA(hist_data['close'].values, timeperiod=sma_long)
                        latest_sma_50 = sma_50[-1]
                        latest_sma_200 = sma_200[-1]
                        
                        # Check if 200 SMA is below 50 SMA
                        if latest_sma_200 < latest_sma_50:
                            stock_data = df[df['Symbol'] == symbol].to_dict('records')[0]
                            filtered_stocks.append(stock_data)
                            print(f"✓ {symbol}: SMA200 {latest_sma_200:.2f} < SMA50 {latest_sma_50:.2f} (passed)")
                        else:
                            print(f"✗ {symbol}: SMA200 {latest_sma_200:.2f} >= SMA50 {latest_sma_50:.2f}")
                    else:
                        print(f"✗ {symbol}: Insufficient data (need at least {sma_long} bars)")
                else:
                    print(f"✗ {symbol}: Invalid contract")
                    
            except Exception as e:
                print(f"✗ {symbol}: Error - {str(e)[:50]}...")
            
            # Delay for IB API rate limits
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
    # Input CSV file
    csv_file = r'C:\Users\jorge_388iox0\OneDrive\OneDrive\Trading\QuantitativeTrading\Scanners\golden_stack_uptrend\nyse_50sma_below_20sma_stocks.csv'
    
    # Filter stocks
    filtered_stocks = filter_by_200sma_below_50sma(csv_file, sma_short=50, sma_long=200, data_days=200)
    
    # Check if filtered DataFrame is not empty
    if not filtered_stocks.empty:
        print(f"\nFound {len(filtered_stocks)} stocks with 200 SMA < 50 SMA:")
        print(filtered_stocks.head())
        
        # Save to new CSV
        filtered_stocks.to_csv('nyse_200sma_below_50sma_stocks.csv', index=False)
        print("Saved to 'nyse_200sma_below_50sma_stocks.csv'")
    else:
        print("No stocks met the 200 SMA < 50 SMA criterion or an error occurred.")