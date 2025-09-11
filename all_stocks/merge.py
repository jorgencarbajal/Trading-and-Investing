import pandas as pd
import os
import glob

# Debug: List files in the directory that contain "stocks"
directory = r"C:\Users\jorge_388iox0\OneDrive\OneDrive\Trading\QuantitativeTrading\all_stocks"
files = glob.glob(os.path.join(directory, "*stocks*"))
print("Files found in directory:", files)

# Define file paths (update these based on the print output above)
file_paths = [
    r"C:\Users\jorge_388iox0\OneDrive\OneDrive\Trading\QuantitativeTrading\all_stocks\nasdaq-stocks-stocks.csv",
    r"C:\Users\jorge_388iox0\OneDrive\OneDrive\Trading\QuantitativeTrading\all_stocks\nyse-stocks-stocks.csv",
    r"C:\Users\jorge_388iox0\OneDrive\OneDrive\Trading\QuantitativeTrading\all_stocks\otc-stocks-stocks.csv"
]

# Read and merge CSV files, assuming they have a 'Symbol' column
dfs = []
for file in file_paths:
    if os.path.exists(file):
        df = pd.read_csv(file)
        dfs.append(df)
        print(f"Loaded {file} with {len(df)} rows")
    else:
        print(f"File not found: {file}")

if dfs:
    merged_df = pd.concat(dfs, ignore_index=True)

    # Remove duplicates based on 'Symbol' column
    merged_df = merged_df.drop_duplicates(subset=['Symbol'], keep='first')

    # Save merged list to a new CSV file
    output_path = r"C:\Users\jorge_388iox0\OneDrive\OneDrive\Trading\QuantitativeTrading\all_stocks\merged_stocks.csv"
    merged_df.to_csv(output_path, index=False)

    print(f"Merged stock list saved to {output_path} with {len(merged_df)} unique symbols")
else:
    print("No files were loaded. Check the file paths.")