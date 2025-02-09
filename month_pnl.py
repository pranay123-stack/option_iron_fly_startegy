import pandas as pd

# Load the CSV data
input_file = '/Users/pranaygaurav/Downloads/AlgoTrading/1.Kredent_Strategy_And_Tasks/mohit_iron_fly_startegy/combined_pnl_reports.csv'
df = pd.read_csv(input_file)

# Ensure the 'Datetime' column is in datetime format
df['Datetime'] = pd.to_datetime(df['Datetime'])

# Calculate PnL for each trade based on BUY or SELL action, scaling by 25
df['PnL'] = df.apply(lambda row: 25 * ((row['price'] - row['current_price']) if row['BUY/SELL'] == 'SELL' 
                     else (row['current_price'] - row['price'])), axis=1)

# Group the data by month and calculate the total PnL for each month
monthly_pnl = df.groupby(df['Datetime'].dt.to_period('M'))['PnL'].sum().reset_index()

# Rename columns to 'Month' and 'PnL'
monthly_pnl.columns = ['Month', 'PnL']

# Save the new data to a new CSV file
output_file = '/Users/pranaygaurav/Downloads/AlgoTrading/1.Kredent_Strategy_And_Tasks/mohit_iron_fly_startegy/monthly_pnl.csv'
monthly_pnl.to_csv(output_file, index=False)

print(f"New CSV file created: {output_file}")
