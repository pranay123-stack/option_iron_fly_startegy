import pandas as pd
import json

# Load the CSV data
df = pd.read_csv('/Users/pranaygaurav/Downloads/AlgoTrading/1.Kredent_Strategy_And_Tasks/mohit_iron_fly_startegy/combined_pnl_reports.csv')

# Ensure the 'Datetime' column is in datetime format
df['Datetime'] = pd.to_datetime(df['Datetime'])

# Calculate PnL for each trade based on BUY or SELL action, scaling by 25
df['PnL'] = df.apply(lambda row: 25 * ((row['price'] - row['current_price']) if row['BUY/SELL'] == 'SELL' 
                     else (row['current_price'] - row['price'])), axis=1)

# Add the 'Cumulative PnL' column to the DataFrame
df['Cumulative PnL'] = df['PnL'].cumsum()

# Group the data by month and calculate monthly PnL
monthly_pnl = df.groupby(df['Datetime'].dt.to_period('M'))['PnL'].sum()

# Initialize variables for winning and losing streaks
current_win_streak = 0
current_loss_streak = 0
max_win_streak = 0
max_loss_streak = 0

# Calculate the streaks
for pnl in monthly_pnl:
    if pnl > 0:
        current_win_streak += 1
        current_loss_streak = 0
    elif pnl < 0:
        current_loss_streak += 1
        current_win_streak = 0
    else:
        current_win_streak = 0
        current_loss_streak = 0

    max_win_streak = max(max_win_streak, current_win_streak)
    max_loss_streak = max(max_loss_streak, current_loss_streak)

# Compute other metrics
total_months = len(monthly_pnl)
overall_pnl = monthly_pnl.sum()
average_month_pnl = overall_pnl / total_months

max_profit_month_value = monthly_pnl.max()
max_profit_month = str(monthly_pnl.idxmax())
max_loss_month_value = monthly_pnl.min()
max_loss_month = str(monthly_pnl.idxmin())

win_percentage = (monthly_pnl > 0).mean() * 100
loss_percentage = (monthly_pnl < 0).mean() * 100
average_profit_on_win_month = monthly_pnl[monthly_pnl > 0].mean()
average_loss_on_loss_month = monthly_pnl[monthly_pnl < 0].mean()
reward_to_risk_ratio = abs(average_profit_on_win_month / average_loss_on_loss_month)
expectancy = (reward_to_risk_ratio * (win_percentage / 100)) - (loss_percentage / 100)

# Calculate Maximum Drawdown (MDD) based on the correct method
cumulative_pnl = monthly_pnl.cumsum()
peak = cumulative_pnl[0]
trough = cumulative_pnl[0]

# Iterate over the cumulative PnL values to find the peaks and troughs
for value in cumulative_pnl:
    if value > peak:
        peak = value  # Update the peak to the new high
    elif value < trough:
        trough = value  # Update the trough to the new low

# Calculate the final drawdown after the loop
max_drawdown = peak - trough
max_drawdown_percentage = (max_drawdown / peak) * 100

# Organize metrics into a dictionary
metrics = {
    "Overall PnL": overall_pnl,
    "Average Month PnL": average_month_pnl,
    "Max Profit Month": {"Month": max_profit_month, "Value": max_profit_month_value},
    "Max Loss Month": {"Month": max_loss_month, "Value": max_loss_month_value},
    "Total Months": total_months,
    "Win %": win_percentage,
    "Loss %": loss_percentage,
    "Reward to Risk Ratio": reward_to_risk_ratio,
    "Expectancy": expectancy,
    "Max Winning Streak": max_win_streak,
    "Max Losing Streak": max_loss_streak,
    "Average Profit on Winning Month": average_profit_on_win_month,
    "Average Loss on Losing Month": average_loss_on_loss_month,
    "Max Drawdown": max_drawdown,
    "Max Drawdown Percentage": max_drawdown_percentage
}

# Display the metrics
print(metrics)

# Optionally, save the metrics to a JSON file for better usability
with open('/Users/pranaygaurav/Downloads/AlgoTrading/1.Kredent_Strategy_And_Tasks/mohit_iron_fly_startegy/combined_metrics.json', 'w') as f:
    json.dump(metrics, f, indent=4)



# overall pnl = sum of each month pnl
# average month pnl =  overall pnl/total no of months
# max profit = max in all  month profit[month name]
# max loss = max in all  month loss[month name]
# win % = no of  profit months +ve/no of total months
# loss % = no of  loss months -ve/no of total months

# Maximum Winning Streak:

# Definition: The highest number of consecutive winning months.

# Maximum Losing Streak:

# Definition: The highest number of consecutive losing months.

# Average Profit on Winning month:

# Formula: Sum of profits on winning months divided by the number of winning months.


# Average Loss on Losing month:

# Formula: Sum of losses on losing months divided by the number of losing month.


# Reward to Risk Ratio:

# Formula: Average Profit on Winning months divided by Average Loss on Losing months.


# Expectancy:

# Formula: (Reward to Risk Ratio * Win Ratio) - Loss Ratio.
