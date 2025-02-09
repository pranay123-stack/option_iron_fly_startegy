# import pandas as pd
# import os

# # Define the directory containing the CSV files
# directory_path = '/Users/pranaygaurav/Downloads/AlgoTrading/1.Kredent_Strategy_And_Tasks/mohit_iron_fly_startegy/pnl_reports'

# # Initialize an empty list to hold DataFrames
# dataframes = []

# # Iterate over each file in the directory
# for filename in os.listdir(directory_path):
#     if filename.endswith('.csv'):  # Ensure the file is a CSV
#         file_path = os.path.join(directory_path, filename)  # Construct full file path
#         df = pd.read_csv(file_path)  # Read the CSV file into a DataFrame
#         dataframes.append(df)  # Append the DataFrame to the list

# # Combine all DataFrames into a single DataFrame
# combined_df = pd.concat(dataframes, ignore_index=True)

# # Define the path for the output CSV file
# output_path = os.path.join(directory_path, '/Users/pranaygaurav/Downloads/AlgoTrading/1.Kredent_Strategy_And_Tasks/mohit_iron_fly_startegy/combined_pnl_reports.csv')

# # Save the combined DataFrame to a new CSV file
# combined_df.to_csv(output_path, index=False)

# print(f"All CSV files have been combined into {output_path}")







#sorting
import pandas as pd

# Load the CSV data
df = pd.read_csv('/Users/pranaygaurav/Downloads/AlgoTrading/1.Kredent_Strategy_And_Tasks/mohit_iron_fly_startegy/combined_pnl_reports.csv')

# Convert the 'Datetime' column to datetime type
df['Datetime'] = pd.to_datetime(df['Datetime'], format='%d/%m/%Y %H:%M:%S')

# Sort the DataFrame by the 'Datetime' column in ascending order
df = df.sort_values('Datetime', ascending=True)

# Optionally, you can reset the index after sorting if you want a clean, sequential index
df = df.reset_index(drop=True)

# Save the sorted DataFrame back to CSV if needed
df.to_csv('/Users/pranaygaurav/Downloads/AlgoTrading/1.Kredent_Strategy_And_Tasks/mohit_iron_fly_startegy/combined_pnl_reports.csv', index=False)

print("Data sorted by Datetime and saved to combined_pnl")
