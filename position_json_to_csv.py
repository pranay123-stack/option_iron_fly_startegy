import json
import pandas as pd

# Load JSON file
json_file_path = "/Users/pranaygaurav/Downloads/AlgoTrading/1.Kredent_Strategy_And_Tasks/mohit_iron_fly_startegy/pnl_reports/MAR_2024_positions.json"
with open(json_file_path, 'r') as f:
    pnl_data = json.load(f)

# Prepare data for DataFrame
data = []
for pos_id, details in pnl_data.items():
    data.append({
        "strike": details["strike"],
        "optiontype": details["option_type"],
        "BUY/SELL": "BUY" if "buy" in pos_id else "SELL",
        "price": details["entry_price"],
        "current_price": details["current_price"],
        "Datetime": f"{details['date']} {details['time']}"
    })

# Create DataFrame
df = pd.DataFrame(data)

# Save DataFrame to CSV
csv_file_path = "/Users/pranaygaurav/Downloads/AlgoTrading/1.Kredent_Strategy_And_Tasks/mohit_iron_fly_startegy/pnl_reports/MAR_2024_positions2.csv"
df.to_csv(csv_file_path, index=False)

print(f"CSV file saved to {csv_file_path}")
