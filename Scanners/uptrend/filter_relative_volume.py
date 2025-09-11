# LIBRARIES ***************************************************************************************
from ib_insync import *  # For connecting to Interactive Brokers TWS API
import pandas as pd  # For handling the stock list and data manipulation
import time  # For adding delays to respect IB API rate limits
from tqdm import tqdm  # For progress bar tracking

# FUNCTION TO FILTER STOCKS BY RELATIVE VOLUME *****************************************************
def filter_by_relative_volume(csv_file, min_rel_volume=1.0, avg_days=20):
    """
    Filter stocks from a CSV file based on relative volume (current day volume / average volume).
    Args:
        csv_file (str): Path to the CSV file with stock symbols
        min_rel_volume (float): Minimum relative volume (default: 1.0)
        avg_days (int): Number of days for average volume calculation (default: 20)
    Returns:
        pd.DataFrame: Filtered DataFrame with stocks meeting the relative volume criterion
    """
    # Read the CSV file containing stock symbols
    df = pd.read_csv(csv_file)
    
    # Initialize IB connection
    ib = IB()
    try:
        # Connect to TWS or IB Gateway
        ib.connect('127.0.0.1', 7497, clientId=1)
        
        # Suppress IB API error messages
        ib.errorEvent += lambda reqId, errorCode, errorString, contract: None
        
        # Initialize list for filtered stocks
        filtered_stocks = []
        
        # Get total symbols for progress tracking
        total_symbols = len(df)
        
        # Loop through each stock symbol with progress bar
        for symbol in tqdm(df['Symbol'], total=total_symbols, desc="Scanning stocks for Rel Volume"):
            try:
                # Create a Stock contract (US stock, SMART exchange for better coverage)
                contract = Stock(symbol, 'SMART', 'USD', primaryExchange='NYSE')
                
                # Qualify the contract
                qualified_contracts = ib.qualifyContracts(contract)
                
                if qualified_contracts:
                    contract = qualified_contracts[0]
                    
                    # Request historical data for average volume (20 days)
                    hist_bars = ib.reqHistoricalData(
                        contract,
                        endDateTime='',
                        durationStr=f'{avg_days} D',
                        barSizeSetting='1 day',
                        whatToShow='TRADES',
                        useRTH=True,
                        formatDate=1,
                        keepUpToDate=False
                    )
                    
                    # Request latest day’s volume (1 day)
                    latest_bar = ib.reqHistoricalData(
                        contract,
                        endDateTime='',
                        durationStr='1 D',
                        barSizeSetting='1 day',
                        whatToShow='TRADES',
                        useRTH=True,
                        formatDate=1,
                        keepUpToDate=False
                    )
                    
                    if hist_bars and latest_bar:
                        # Convert to DataFrames
                        hist_data = util.df(hist_bars)
                        latest_data = util.df(latest_bar)
                        
                        # Calculate average volume
                        avg_volume = hist_data['volume'].mean()
                        
                        # Get current day’s volume
                        current_volume = latest_data['volume'].iloc[-1]
                        
                        # Calculate relative volume
                        if avg_volume > 0:  # Avoid division by zero
                            rel_volume = current_volume / avg_volume
                            
                            # Check if relative volume exceeds threshold
                            if rel_volume >= min_rel_volume:
                                stock_data = df[df['Symbol'] == symbol].to_dict('records')[0]
                                filtered_stocks.append(stock_data)
                                print(f"✓ {symbol}: Rel Volume {rel_volume:.2f} (passed)")
                            else:
                                print(f"✗ {symbol}: Rel Volume {rel_volume:.2f} < {min_rel_volume}")
                        else:
                            print(f"✗ {symbol}: Average volume is zero")
                    else:
                        print(f"✗ {symbol}: No data returned")
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
    csv_file = r'C:\Users\jorge_388iox0\OneDrive\OneDrive\Trading\QuantitativeTrading\Scanners\golden_stack_uptrend\nyse_high_volume_stocks.csv'
    
    # Filter stocks by relative volume (> 1.0)
    filtered_stocks = filter_by_relative_volume(csv_file, min_rel_volume=1.0, avg_days=20)
    
    # Check if the filtered DataFrame is not empty
    if not filtered_stocks.empty:
        # Print the number of stocks meeting the relative volume criterion
        print(f"\nFound {len(filtered_stocks)} stocks with relative volume > 1.0:")
        
        # Print the first few rows to verify
        print(filtered_stocks.head())
        
        # Save the filtered DataFrame to a new CSV file
        filtered_stocks.to_csv(r'C:\Users\jorge_388iox0\OneDrive\OneDrive\Trading\QuantitativeTrading\Scanners\golden_stack_uptrend\nyse_high_rel_volume_stocks.csv', index=False)
        
        # Confirm the file was saved
        print("Saved to 'nyse_high_rel_volume_stocks.csv'")
    else:
        print("No stocks met the relative volume criterion or an error occurred.")