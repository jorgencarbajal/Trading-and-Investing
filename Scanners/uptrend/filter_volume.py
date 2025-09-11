# LIBRARIES ***************************************************************************************
from ib_insync import *  # For connecting to Interactive Brokers TWS API
import pandas as pd  # For handling the stock list and data manipulation
import time  # For adding delays to respect IB API rate limits
from tqdm import tqdm  # For progress bar tracking

# FUNCTION TO FILTER STOCKS BY AVERAGE VOLUME ******************************************************
def filter_by_avg_volume(csv_file, min_avg_volume=2000000, days=20):
    # docstring, explaining the function
    """
    Filter stocks from a CSV file based on average daily volume over a specified period.
    Args:
        csv_file (str): Path to the CSV file with stock symbols
        min_avg_volume (int): Minimum average daily volume (default: 2M shares)
        days (int): Number of days to calculate average volume (default: 20)
    Returns:
        pd.DataFrame: Filtered DataFrame with stocks meeting the volume criterion
    """
    # Read the CSV file containing stock symbols and store in a DataFrame
    df = pd.read_csv(csv_file)
    
    # Initialize IB connection
    ib = IB()
    try:
        # Connect to TWS or IB Gateway (update host/port/clientId as needed)
        ib.connect('127.0.0.1', 7497, clientId=1)
        
        # Suppress IB API error messages for invalid contracts
        ib.errorEvent += lambda reqId, errorCode, errorString, contract: None
        
        # Initialize list for filtered stocks
        filtered_stocks = []
        
        # Get total symbols for progress tracking
        total_symbols = len(df)
        
        # Loop through each stock symbol in the DataFrame with progress bar
        for symbol in tqdm(df['Symbol'], total=total_symbols, desc="Scanning stocks"):
            try:
                # Create a Stock contract for the symbol (NYSE, USD, common stock)
                contract = Stock(symbol, 'NYSE', 'USD', primaryExchange='NYSE')
                
                # Qualify the contract to resolve ambiguities
                qualified_contracts = ib.qualifyContracts(contract)
                
                # Check if a valid contract was found
                if qualified_contracts:
                    contract = qualified_contracts[0]  # Use the first valid contract
                    
                    # Request historical data (20 days, daily bars, regular trading hours)
                    bars = ib.reqHistoricalData(
                        contract,
                        endDateTime='',
                        durationStr=f'{days} D',
                        barSizeSetting='1 day',
                        whatToShow='TRADES',    # 'TRADES' — Trade data (price/volume of trades, most common for stocks)
                                                # 'MIDPOINT' — Midpoint between bid and ask
                                                # 'BID' — Bid prices only
                                                # 'ASK' — Ask prices only
                                                # 'BID_ASK' — Both bid and ask prices
                                                # 'HISTORICAL_VOLATILITY' — Historical volatility
                                                # 'OPTION_IMPLIED_VOLATILITY' — Option implied volatility
                                                # 'YIELD_BID', 'YIELD_ASK', 'YIELD_BID_ASK', 'YIELD_LAST' — For bonds
                        useRTH=True, # regular trading hours
                        formatDate=1,       # Controls the date format in the returned data (1 = 
                                            # human-readable, 2 = UNIX timestamp).
                        keepUpToDate=False  # If True, keeps streaming new data as it comes in; if False, 
                                            # just gets a snapshot.
                    )
                    
                    # Check if data was returned
                    if bars:
                        # a helper function from the ib_insync library that converts this list of bar objects 
                        # into a pandas DataFrame.
                        hist_data = util.df(bars)
                        
                        # Calculate average volume over the period
                        avg_volume = hist_data['volume'].mean()
                        
                        # Check if average volume exceeds the threshold
                        if avg_volume >= min_avg_volume:
                            # Add symbol to filtered list (preserve other columns if they exist)
                            stock_data = df[df['Symbol'] == symbol].to_dict('records')[0]
                            filtered_stocks.append(stock_data)
                            print(f"✓ {symbol}: Avg vol {avg_volume:,.0f} (passed)")
                    else:
                        print(f"✗ {symbol}: No data returned")
                else:
                    print(f"✗ {symbol}: Invalid contract")
                    
            except Exception as e:
                print(f"✗ {symbol}: Error - {str(e)[:50]}...")
            
            # Reduced delay for speed (0.2s = ~5 req/s, safe under limits)
            time.sleep(0.2)
        
        # Convert filtered stocks to DataFrame
        filtered_df = pd.DataFrame(filtered_stocks)
        
        return filtered_df
    
    except Exception as e:
        print(f"Error during IB API operations: {e}")
        return pd.DataFrame()
    
    finally:
        # Disconnect from IB to clean up
        ib.disconnect()

# MAIN SCRIPT ************************************************************************************
if __name__ == "__main__":
    # Path to the input CSV file (fixed extension)
    csv_file = r'C:\Users\jorge_388iox0\OneDrive\OneDrive\Trading\QuantitativeTrading\all_stocks\merged_stocks.csv'  # Update with your actual path
    
    # Filter stocks by average volume (> 2M over 20 days)
    filtered_stocks = filter_by_avg_volume(csv_file, min_avg_volume=2000000, days=20)
    
    # Check if the filtered DataFrame is not empty
    if not filtered_stocks.empty:
        # Print the number of stocks meeting the volume criterion
        print(f"\nFound {len(filtered_stocks)} stocks with average volume > 2M")
        
        # Print the first few rows to verify
        print(filtered_stocks.head())
        
        # Save the filtered DataFrame to a new CSV file
        filtered_stocks.to_csv('nyse_high_volume_stocks.csv', index=False)
        
        # Confirm the file was saved
        print("Saved to 'nyse_high_volume_stocks.csv'")
    else:
        print("No stocks met the average volume criterion or an error occurred.")