# LIBRARIES ***************************************************************************************
from ib_insync import *  # For connecting to Interactive Brokers TWS API
import pandas as pd  # For handling the stock list and data manipulation
import talib  # For calculating Simple Moving Average (SMA)
import time  # For adding delays to respect IB API rate limits
from tqdm import tqdm  # For progress bar tracking

# FUNCTION TO FILTER STOCKS BY 50 SMA BELOW 20 SMA ***********************************************
def filter_by_50sma_below_20sma(csv_file, sma_short=20, sma_long=50, data_days=50):
    """
    Filter stocks from a CSV file where the 50-day SMA is below the 20-day SMA.
    Args:
        csv_file (str): Path to the CSV file with stock symbols
        sma_short (int): Period for shorter SMA (default: 20)
        sma_long (int): Period for longer SMA (default: 50)
        data_days (int): Number of days of historical data to fetch (default: 50)
    Returns:
        pd.DataFrame: Filtered DataFrame with stocks where 50 SMA < 20 SMA
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
        for symbol in tqdm(df['Symbol'], total=total_symbols, desc="Scanning stocks for 50 SMA < 20 SMA"):
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
                        sma_20 = talib.SMA(hist_data['close'].values, timeperiod=sma_short)
                        sma_50 = talib.SMA(hist_data['close'].values, timeperiod=sma_long)
                        latest_sma_20 = sma_20[-1]
                        latest_sma_50 = sma_50[-1]
                        
                        # Check if 50 SMA is below 20 SMA
                        if latest_sma_50 < latest_sma_20:
                            stock_data = df[df['Symbol'] == symbol].to_dict('records')[0]
                            filtered_stocks.append(stock_data)
                            print(f"✓ {symbol}: SMA50 {latest_sma_50:.2f} < SMA20 {latest_sma_20:.2f} (passed)")
                        else:
                            print(f"✗ {symbol}: SMA50 {latest_sma_50:.2f} >= SMA20 {latest_sma_20:.2f}")
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
    csv_file = r'C:\Users\jorge_388iox0\OneDrive\OneDrive\Trading\QuantitativeTrading\Scanners\golden_stack_uptrend\nyse_price_above_20sma_stocks.csv'
    
    # Filter stocks
    filtered_stocks = filter_by_50sma_below_20sma(csv_file, sma_short=20, sma_long=50, data_days=50)
    
    # Check if filtered DataFrame is not empty
    if not filtered_stocks.empty:
        print(f"\nFound {len(filtered_stocks)} stocks with 50 SMA < 20 SMA:")
        print(filtered_stocks.head())
        
        # Save to new CSV
        filtered_stocks.to_csv('nyse_50sma_below_20sma_stocks.csv', index=False)
        print("Saved to 'nyse_50sma_below_20sma_stocks.csv'")
    else:
        print("No stocks met the 50 SMA < 20 SMA criterion or an error occurred.")