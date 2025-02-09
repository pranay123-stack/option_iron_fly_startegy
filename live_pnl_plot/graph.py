import pandas as pd
import matplotlib.pyplot as plt

# Load the Excel file
file_path = '/Users/pranaygaurav/Downloads/AlgoTrading/pnl_report.xlsx'
pnl_data = pd.read_excel(file_path, sheet_name='pnl_report')

# Convert the 'Time' column from decimal to time format
pnl_data['Time'] = pd.to_timedelta(pnl_data['Time'], unit='D')

# Combine 'Date' and 'Time' into a single datetime column
pnl_data['datetime'] = pd.to_datetime(pnl_data['Date'].astype(str)) + pnl_data['Time']

# Filter the data to include only times between 09:15 and 15:30
start_time = pd.to_datetime('09:15').time()
end_time = pd.to_datetime('15:30').time()
pnl_data_filtered = pnl_data[(pnl_data['datetime'].dt.time >= start_time) &
                             (pnl_data['datetime'].dt.time <= end_time)].copy()

# Round 'datetime' to the nearest hour
pnl_data_filtered.loc[:, 'Hour'] = pnl_data_filtered['datetime'].dt.round('H')

# Get unique dates
unique_dates = pnl_data_filtered['Date'].unique()

# Create a line chart for each unique date
for date in unique_dates:
    daily_data = pnl_data_filtered[pnl_data_filtered['Date'] == date]
    
    # Group by hour and take the first available value
    hourly_data = daily_data.groupby('Hour').first().reset_index()
    
    # Convert 'Hour' to a string format for plotting
    hourly_data['Hour'] = hourly_data['Hour'].dt.strftime('%H:%M')
    
    # Plot the data
    plt.figure(figsize=(10, 6))
    plt.plot(hourly_data['Hour'], hourly_data['PNL'], marker='o')
    plt.xlabel('Time')
    plt.ylabel('PnL')
    plt.title(f'PnL vs Time for {date}')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.show()
