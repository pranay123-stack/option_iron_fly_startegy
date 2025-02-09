import pandas as pd
import os
from pathlib import Path
import json
from datetime import datetime, timedelta
import logging
import coloredlogs
import csv
import threading
import time

# Set up logging
log_file_path = 'strategy_logs_sept.log'

# Configure basic logging to file

# Configure basic logging to file
logging.basicConfig(level=logging.DEBUG, filename=log_file_path, filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')


# Set up colored logs for console output
coloredlogs.install(level='DEBUG',
                    fmt='%(asctime)s - %(levelname)s - %(message)s',
                    level_styles={
                        'info': {'color': 'green'},
                        'debug': {'color': 'white'},
                        'error': {'color': 'red'},
                    })

# Initialize the global position dictionary
position_dict = {}


def round_to_nearest_50(x):
    try:
        # logging.debug(f"Rounding value {x} to the nearest 50.")
        result = round(x / 50) * 50
        # logging.debug(f"Rounded value: {result}")
        return result
    except Exception as e:
        logging.error(f"Error rounding value {x} to nearest 50 - {e}")
        return None

def load_and_preprocess(file_path, time_filter=None):
    try:
        # logging.debug(f"Loading file: {file_path}")
        df = pd.read_csv(file_path)
        df['Time'] = pd.to_datetime(df['Time']).dt.time
        # logging.debug(f"File loaded successfully. Applying time filter: {time_filter}")
        if time_filter:
            df = df[df['Time'] >= datetime.strptime(time_filter, '%H:%M:%S').time()]
        # logging.info(f"Loaded and preprocessed file: {file_path}")
        return df
    except Exception as e:
        logging.error(f"Error loading and preprocessing file: {file_path} - {e}")
        return pd.DataFrame()

def find_strike_prices(atm):
    try:
        # logging.debug(f"Calculating strike prices for ATM: {atm}")
        ce_sell_strike = atm
        pe_sell_strike = atm
        ce_buy_strike = atm + 700  # Not rounding these values
        pe_buy_strike = atm - 700  # Not rounding these values
        # logging.debug(f"Calculated strike prices - CE Sell: {ce_sell_strike}, PE Sell: {pe_sell_strike}, CE Buy: {ce_buy_strike}, PE Buy: {pe_buy_strike}")
        return ce_sell_strike, pe_sell_strike, ce_buy_strike, pe_buy_strike
    except Exception as e:
        logging.error(f"Error finding strike prices for ATM: {atm} - {e}")
        return None, None, None, None


def extract_option_prices(option_df, ce_sell_strike, pe_sell_strike, ce_buy_strike, pe_buy_strike, expiry_date, time):
    try:
        # logging.debug(f"Extracting option prices for strikes - CE Sell: {ce_sell_strike}, PE Sell: {pe_sell_strike}, CE Buy: {ce_buy_strike}, PE Buy: {pe_buy_strike} at time: {time}")

        # Filter option_df by time and ticker
        option_prices = {
            'ce_sell': option_df[(option_df['Ticker'].str.contains(f'NIFTY{expiry_date}{ce_sell_strike}CE.NFO')) & (option_df['Time'] == time)]['Close'].values[0],
            'pe_sell': option_df[(option_df['Ticker'].str.contains(f'NIFTY{expiry_date}{pe_sell_strike}PE.NFO')) & (option_df['Time'] == time)]['Close'].values[0],
            'ce_buy': option_df[(option_df['Ticker'].str.contains(f'NIFTY{expiry_date}{ce_buy_strike}CE.NFO')) & (option_df['Time'] == time)]['Close'].values[0],
            'pe_buy': option_df[(option_df['Ticker'].str.contains(f'NIFTY{expiry_date}{pe_buy_strike}PE.NFO')) & (option_df['Time'] == time)]['Close'].values[0]
        }
        
        # logging.debug(f"Extracted option prices: {option_prices}")
        return option_prices
    except IndexError:
        logging.error(f"No matching data found for the provided strikes and time - CE Sell: {ce_sell_strike}, PE Sell: {pe_sell_strike}, CE Buy: {ce_buy_strike}, PE Buy: {pe_buy_strike} at time: {time}")
        return {}
    except Exception as e:
        logging.error(f"Error extracting option prices - CE Sell: {ce_sell_strike}, PE Sell: {pe_sell_strike}, CE Buy: {ce_buy_strike}, PE Buy: {pe_buy_strike} at time: {time} - {e}")
        return {}


def create_position_dict(date, time, strike, price, option_type, qty=25):
    try:
        # logging.debug(f"Creating position dictionary for Date: {date}, Time: {time}, Strike: {strike}, Price: {price}, Option Type: {option_type}, Quantity: {qty}")
        position_dict = {
            'entry_price': price,
            'strike': strike,
            'option_type': option_type,
            'date': date,
            'time': time.strftime('%H:%M:%S'),  # Serialize time to string
            'qty': qty,
            'current_price': price
        }
        # logging.debug(f"Created position dictionary: {position_dict}")
        return position_dict
    except Exception as e:
        logging.error(f"Error creating position dictionary - Date: {date}, Time: {time}, Strike: {strike}, Price: {price}, Option Type: {option_type} - {e}")
        return {}


def get_current_price(option_df, strike, option_type, expiry_date, time, option_file):
    try:
        pattern = f'NIFTY{expiry_date}{strike}{option_type}.NFO'
        # logging.debug(f"Fetching current price for pattern: {pattern} at time: {time}")

        # Initialize the time to search
        search_time = time

        # Loop to check up to 5 minutes ahead
        for i in range(6):  # 0 to 5 (total 6 iterations)
            filtered_df = option_df[(option_df['Ticker'].str.contains(pattern)) & (option_df['Time'] == search_time)]
            
            if not filtered_df.empty:
                current_price = filtered_df['Close'].values[0]
                # logging.debug(f"Current price for pattern {pattern} at time {search_time}: {current_price}")
                return current_price
            
            # logging.debug(f"No matching data found for pattern: {pattern} at time: {search_time}. Checking the next minute.")

            # Increment time by one minute, keeping the seconds at 59
            new_time = datetime.combine(datetime.today(), search_time) + timedelta(minutes=1)
            search_time = new_time.time().replace(second=59)

        logging.error(f"No matching data found for pattern: {pattern} within 5 minutes of time: {time} in option file: {option_file}. Skipping price update.")
        return None
    except Exception as e:
        logging.error(f"Error fetching current price for pattern: {pattern} at time: {time} in option file: {option_file} - {e}")
        return None

def save_position_to_file(position_dict, month_name, position_file):
    try:
        # logging.debug(f"Saving position to file: {position_file}")

        # Load existing data if the file exists
        if Path(position_file).exists():
            with open(position_file, 'r') as f:
                data = json.load(f)
        else:
            data = {}

        # Add each position with a unique key
        for key, new_pos in position_dict.items():
            unique_key = f"{key}"
            data.setdefault(month_name, {})[unique_key] = new_pos

        # Save the updated data back to the JSON file
        with open(position_file, 'w') as f:
            json.dump(data, f, indent=4)

        # logging.info(f"Saved position to file: {position_file} for month: {month_name}")
    except Exception as e:
        logging.error(f"Error saving position to file: {position_file} for month: {month_name} - {e}")

def find_all_matching_option_files(option_dir, month):
    try:
        # logging.debug(f"Searching for all option CSV files in directory: {option_dir} for month: {month}")
        option_month_dir = Path(option_dir) / month
        
        option_files = list(option_month_dir.glob("*.csv"))
        
        # Sort option files by date extracted from the filename
        option_files.sort(key=lambda x: datetime.strptime(x.stem.split('_')[-1], '%d%m%Y'))
        
        if option_files:
            # logging.info(f"Found {len(option_files)} option files for month: {month}")
            pass
        else:
            # logging.warning(f"No option files found in directory for month: {month}")
            pass
        
        return option_files
    except Exception as e:
        logging.error(f"Error finding option CSV files for month: {month} - {e}")
        return []




def monitor_positions(option_df, option_file, ce_buy_strike, pe_buy_strike, ce_sell_strike, pe_sell_strike, expiry_date, month_name, position_file, output_dir):
    global position_dict
    try:
        # logging.debug(f"Monitoring positions from 09:20:59 to 15:30:59 for option file: {option_file}.")
        pos_id = len(position_dict)  # Start pos_id based on the existing position length

        # Filter option_df to only include rows with strikes in position_dict
        relevant_strikes = {str(pos['strike']) for pos in position_dict.values()}  # Convert strikes to strings
        option_df_filtered = option_df[(option_df['Ticker'].str.contains('|'.join(relevant_strikes))) & (option_df['Time'] <= pd.to_datetime('15:29:59').time())]

        # Track the last processed time to prevent reprocessing
        last_processed_time = None

        # Iterate directly over the filtered dataframe
        for _, row in option_df_filtered.iterrows():
            time = row['Time']

            # Skip the row if it has already been processed
            if last_processed_time is not None and time <= last_processed_time:
                # logging.debug(f"Skipping already processed time: {time.strftime('%H:%M:%S')}")
                continue

            time_str = time.strftime('%H:%M:%S')
            # logging.debug(f"Processing time: {time_str}")

            # Update last processed time
            last_processed_time = time

          
             # Update current price for matching positions
            for key, pos in position_dict.items():
                        if pos['strike'] == ce_sell_strike and pos['option_type'] == 'CE':
                            current_price_ce_sell = get_current_price(option_df_filtered, ce_sell_strike, 'CE', expiry_date, time, option_file)
                            if current_price_ce_sell is not None:   
                                position_dict[key]['current_price'] = current_price_ce_sell
                            # logging.debug(f"Updated current price for {key} (Type: {pos['option_type']}): {current_price_ce_sell}")
                        elif pos['strike'] == pe_sell_strike and pos['option_type'] == 'PE':
                            current_price_pe_sell = get_current_price(option_df_filtered, pe_sell_strike, 'PE', expiry_date, time, option_file)
                            if current_price_pe_sell is not None: 
                                position_dict[key]['current_price'] = current_price_pe_sell
                            # logging.debug(f"Updated current price for {key} (Type: {pos['option_type']}): {current_price_pe_sell}")
                        elif pos['strike'] == ce_buy_strike and pos['option_type'] == 'CE':
                            current_price_ce_buy = get_current_price(option_df_filtered, ce_buy_strike, 'CE', expiry_date, time, option_file)
                            if current_price_ce_buy is not None: 
                                position_dict[key]['current_price'] = current_price_ce_buy
                            # logging.debug(f"Updated current price for {key} (Type: {pos['option_type']}): {current_price_ce_buy}")
                        elif pos['strike'] == pe_buy_strike and pos['option_type'] == 'PE':
                            current_price_pe_buy = get_current_price(option_df_filtered, pe_buy_strike, 'PE', expiry_date, time, option_file)
                            if current_price_pe_buy is not None: 
                                position_dict[key]['current_price'] = current_price_pe_buy
                            # logging.debug(f"Updated current price for {key} (Type: {pos['option_type']}): {current_price_pe_buy}")
                        else:
                            # logging.debug(f"No matching position to update their current price.")
                            pass
            


         
            # Save the final state of position_dict to the JSON file after processing
            with open(position_file, 'w') as f:
                json.dump(position_dict, f, indent=4)

            # Re-calculate the highest CE Sell and PE Sell positions after every update
            highest_ce_sell_key = max([k for k in position_dict if k.startswith('ce_sell_pos_')], key=lambda k: int(k.split('_')[-1]))
            highest_pe_sell_key = max([k for k in position_dict if k.startswith('pe_sell_pos_')], key=lambda k: int(k.split('_')[-1]))

            # logging.debug(f"Highest CE Sell Key: {highest_ce_sell_key}, Highest PE Sell Key: {highest_pe_sell_key}")

            # Check for stop-loss on CE Sell
            if  position_dict[highest_ce_sell_key]['current_price'] and position_dict[highest_ce_sell_key]['current_price'] <= position_dict[highest_ce_sell_key]['entry_price'] * 0.9:
                # logging.debug("CE Sell strike hit stop-loss, creating a new hedge position.")
                if position_dict[highest_ce_sell_key]['current_price'] is not None and current_price_ce_buy is not None :
                    new_position = create_position_dict(row['Date'], time, ce_sell_strike, position_dict[highest_ce_sell_key]['current_price'], 'CE')
                    position_dict[f'ce_sell_pos_{pos_id}'] = new_position
            
                    pos_id += 1

                    # Create hedge position for CE Buy
                    hedge_ce_buy = create_position_dict(row['Date'], time, ce_buy_strike, current_price_ce_buy, 'CE')
                    position_dict[f'ce_buy_pos_{pos_id}'] = hedge_ce_buy
                 
                    pos_id += 1



                

                    # logging.info(f"Updated position with hedge for CE Sell at time {time_str}")
                    save_position_to_file(position_dict, month_name, position_file)

                continue  # Continue the loop to re-evaluate positions

            # Check for stop-loss on PE Sell
            if position_dict[highest_pe_sell_key]['current_price'] and position_dict[highest_pe_sell_key]['current_price'] < position_dict[highest_pe_sell_key]['entry_price'] * 0.9:
                # logging.debug("PE Sell strike hit stop-loss, creating a new hedge position.")
                if position_dict[highest_pe_sell_key]['current_price'] is not None and current_price_pe_buy is not None :
                    new_position = create_position_dict(row['Date'], time, pe_sell_strike, position_dict[highest_pe_sell_key]['current_price'], 'PE')
                    position_dict[f'pe_sell_pos_{pos_id}'] = new_position
                 
                    pos_id += 1

                    # Create hedge position for PE Buy
                    hedge_pe_buy = create_position_dict(row['Date'], time, pe_buy_strike, current_price_pe_buy, 'PE')
                    position_dict[f'pe_buy_pos_{pos_id}'] = hedge_pe_buy
         
                    pos_id += 1

                    # logging.info(f"Updated position with hedge for PE Sell at time {time_str}")
                    save_position_to_file(position_dict, month_name, position_file)

                continue  # Continue the loop to re-evaluate positions




     
            # Calculate PnL and update output
            try:
                total_pnl = 0  # Initialize total PnL

                for key, pos in position_dict.items():
                    # Skip if current_price is None
                    if pos['current_price'] is None:
                        # logging.warning(f"Skipping PnL update for position {key} as current_price is None.")
                        continue

                    if 'sell' in key and pos['current_price'] is not None and pos['entry_price'] is not None:
                        # For sell positions, calculate as (entry_price - current_price) * qty
                        # logging.debug(f"pos['entry_price']{pos['entry_price']}")
                        # logging.debug(f"pos['current_price']{pos['current_price']}")
                        pnl = (pos['entry_price'] - pos['current_price']) * pos['qty']
                        # logging.debug(f"PnL for {key}: Sell position: {pnl}")

                    elif 'buy' in key and pos['current_price'] is not None and pos['entry_price'] is not None:
                        # For buy positions, calculate as (current_price - entry_price) * qty
                        # logging.debug(f"pos['entry_price']{pos['entry_price']}")
                        # logging.debug(f"pos['current_price']{pos['current_price']}")
                        pnl = (pos['current_price'] - pos['entry_price']) * pos['qty']
                        # logging.debug(f"PnL for {key}: Buy position: {pnl}")
                    else:
                        # logging.debug(f"Position {key} is neither sell nor buy; skipping.")
                        pnl = 0

                    total_pnl += pnl  # Accumulate the PnL for all positions

                data = {'Date': [row['Date']], 'Time': [time_str], 'PnL': [total_pnl]}
                df = pd.DataFrame(data)
                output_path = Path(output_dir) / f"{month_name}.xlsx"

                # logging.debug(f"Ensuring directory exists for output: {output_path.parent}")
                output_path.parent.mkdir(parents=True, exist_ok=True)

                if not output_path.exists():
                    df.to_excel(output_path, index=False)
                else:
                    with pd.ExcelWriter(output_path, mode='a', if_sheet_exists='overlay') as writer:
                        df.to_excel(writer, index=False, header=False, startrow=writer.sheets['Sheet1'].max_row)
                        # logging.debug(f"========EXCEL UPDATE ON DATE TIME {row['Date'] }{time_str}")


                # logging.info(f"Recorded PnL for {row['Date']} {time_str}: {pnl}")

            except Exception as e:
                logging.error(f"Error calculating PnL for {row['Date']} {time_str} - {e}")

    except Exception as e:
        logging.error(f"Error monitoring positions for month: {month_name} - {e}")

def find_first_matching_csv(index_dir, option_dir, month):
    try:
        # logging.debug(f"Searching for the first matching CSV file in index directory: {index_dir} for month: {month}")
        index_month_dir = Path(index_dir) / month
        option_month_dir = Path(option_dir) / month
        
        for day in range(1, 32):  # Loop over days 01 to 31
            day_str = f"{day:02d}"  # Format day as '01', '02', ..., '31'
            
            # Construct the filename pattern for the index file
            index_pattern = f"NIFTY_GFDLCM_INDICES_{day_str}*{month[-4:]}.csv"
            index_file = next(index_month_dir.glob(index_pattern), None)
            
            if index_file and index_file.exists():
                # logging.debug(f"Found index file: {index_file}")
                # Construct the filename pattern for the option file using the same date
                date_str = index_file.stem.split('_')[-1]
                option_file = option_month_dir / f"NIFTY_GFDLNFO_NIFTY_BANKNIFTY_{date_str}.csv"
                
                if option_file.exists():
                    # logging.info(f"Found matching files: {index_file} and {option_file}")
                    return index_file, option_file
        
        # logging.warning(f"No matching files found in the range 01 to 31 for month: {month}")
        return None, None
    except Exception as e:
        logging.error(f"Error finding matching CSV files for month: {month} - {e}")
        return None, None






def process_month_folder(index_dir, option_dir, month_name, expiry_date, output_dir):
    global position_dict
    try:
        # logging.debug(f"Processing month folder for month: {month_name}")
        position_file = Path(output_dir) / f"{month_name}_positions.json"
        
        # Use index file once to set up initial positions
        index_file, first_option_file = find_first_matching_csv(index_dir, option_dir, month_name)
        
        if index_file and first_option_file:
            # logging.info(f"Processing index file: {index_file}")
            index_df = load_and_preprocess(index_file, '09:20:59')

            if not index_df.empty:
                atm = round_to_nearest_50(index_df.iloc[0]['Close'])
                # logging.info(f'==ATM before strike prices calculated {atm}')
                ce_sell_strike, pe_sell_strike, ce_buy_strike, pe_buy_strike = find_strike_prices(atm)
                
                option_df = load_and_preprocess(first_option_file,'09:20:59')

                                # Define the time as a datetime.time object
                time_to_search = datetime.strptime('09:20:59', '%H:%M:%S').time()

                # Call the function with the time parameter
                option_prices = extract_option_prices(option_df, ce_sell_strike, pe_sell_strike, ce_buy_strike, pe_buy_strike, expiry_date, time_to_search)
                #option_prices = extract_option_prices(option_df, ce_sell_strike, pe_sell_strike, ce_buy_strike, pe_buy_strike, expiry_date)

                # Initialize positions based on the first file
                position_dict = {
                    f'ce_sell_pos_0': create_position_dict(index_df.iloc[0]['Date'], index_df.iloc[0]['Time'], ce_sell_strike,option_prices['ce_sell'], 'CE'),
                    f'pe_sell_pos_1': create_position_dict(index_df.iloc[0]['Date'], index_df.iloc[0]['Time'], pe_sell_strike,option_prices['pe_sell'], 'PE'),
                    f'ce_buy_pos_2': create_position_dict(index_df.iloc[0]['Date'], index_df.iloc[0]['Time'], ce_buy_strike, option_prices['ce_buy'], 'CE'),
                    f'pe_buy_pos_3': create_position_dict(index_df.iloc[0]['Date'], index_df.iloc[0]['Time'], pe_buy_strike, option_prices['pe_buy'], 'PE'),
                }

            
      
           


                try:
                    total_pnl = 0  # Initialize total PnL

                    for key, pos in position_dict.items():
                        # Skip if current_price is None
                        if pos['current_price'] is None:
                            # logging.warning(f"Skipping PnL update for position {key} as current_price is None.")
                            continue

                        if 'sell' in key and pos['current_price'] is not None and pos['entry_price'] is not None:
                            # For sell positions, calculate as (entry_price - current_price) * qty
                            # logging.debug(f"pos['entry_price']{pos['entry_price']}")
                            # logging.debug(f"pos['current_price']{pos['current_price']}")
                            pnl = (pos['entry_price'] - pos['current_price']) * pos['qty']
                            # logging.debug(f"PnL for {key}: Sell position: {pnl}")

                        elif 'buy' in key and pos['current_price'] is not None and pos['entry_price'] is not None:
                            # For buy positions, calculate as (current_price - entry_price) * qty
                            # logging.debug(f"pos['entry_price']{pos['entry_price']}")
                            # logging.debug(f"pos['current_price']{pos['current_price']}")
                            pnl = (pos['current_price'] - pos['entry_price']) * pos['qty']
                            # logging.debug(f"PnL for {key}: Buy position: {pnl}")
                        else:
                            # logging.debug(f"Position {key} is neither sell nor buy; skipping.")
                            pnl = 0

                        total_pnl += pnl  # Accumulate the PnL for all positions

                    data = {'Date': [index_df.iloc[0]['Date']], 'Time': [index_df.iloc[0]['Time']], 'PnL': [total_pnl]}
                    df = pd.DataFrame(data)
                    output_path = Path(output_dir) / f"{month_name}.xlsx"

                    # logging.debug(f"Ensuring directory exists for output: {output_path.parent}")
                    output_path.parent.mkdir(parents=True, exist_ok=True)

                    if not output_path.exists():
                        df.to_excel(output_path, index=False)
                    else:
                        with pd.ExcelWriter(output_path, mode='a', if_sheet_exists='overlay') as writer:
                            df.to_excel(writer, index=False, header=False, startrow=writer.sheets['Sheet1'].max_row)
           


                

                except Exception as e:
                    logging.error(f"Error calculating PnL for {row['Date']} {time_str} - {e}")





                # pnl = (position_dict['ce_sell_pos_0']['current_price']*25 + position_dict['pe_sell_pos_1']['current_price'])*25 - (position_dict['ce_buy_pos_2']['current_price']*25 + position_dict['pe_buy_pos_3']['current_price']*25)

                # data = {'Date': [index_df.iloc[0]['Date']], 'Time': [index_df.iloc[0]['Time']], 'PnL': [pnl]}
                # df = pd.DataFrame(data)
                # output_path = Path(output_dir) / f"{month_name}.xlsx"
                
                # # logging.debug(f"Ensuring output directory exists: {output_path.parent}")
                # output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # if not output_path.exists():
                #     df.to_excel(output_path, index=False)
                # else:
                #     with pd.ExcelWriter(output_path, mode='a', if_sheet_exists='overlay') as writer:
                #         df.to_excel(writer, index=False, header=False, startrow=writer.sheets['Sheet1'].max_row)
                    
                # logging.info(f"Initial PnL calculated and recorded for {index_df.iloc[0]['Date']} {index_df.iloc[0]['Time']}: {pnl}")

                # Save initial position to the JSON file
                save_position_to_file(position_dict, month_name, position_file)

                # Continue processing the rest of the option files in the month
                all_option_files = find_all_matching_option_files(option_dir, month_name)
                
                for options_file in all_option_files:
                    # logging.info(f"===Processing option file=== {options_file}")
                    options_df = load_and_preprocess(options_file,'09:20:59')
                    monitor_positions(options_df, options_file, ce_buy_strike, pe_buy_strike, ce_sell_strike, pe_sell_strike, expiry_date, month_name, position_file, output_dir)

                # Save the final state of position_dict to the JSON file after processing
                with open(position_file, 'w') as f:
                    json.dump(position_dict, f, indent=4)

                # logging.info(f"Final position_dict saved to file: {position_file}")

            else:
                logging.error(f"Index file {index_file} is empty or failed to load.")
        else:
            logging.error(f"No matching files found for month: {month_name}")
    except Exception as e:
        logging.error(f"Error processing month folder: {month_name} - {e}")




# Simplified execution for APR_2023 only
option_dir = '/Users/pranaygaurav/Downloads/AlgoTrading/1.Kredent_Strategy_And_Tasks/0.Dataset/HarshulDaga_FNO+IDX/NIFTY+BANKNIFTY_FUT+OPT_Minute Data/2024'
index_dir = '/Users/pranaygaurav/Downloads/AlgoTrading/1.Kredent_Strategy_And_Tasks/0.Dataset/HarshulDaga_FNO+IDX/NIFTY+BANKNIFTY_SPOT IDX_Minute Data/2024'
output_dir = '/Users/pranaygaurav/Downloads/AlgoTrading/1.Kredent_Strategy_And_Tasks/mohit_iron_fly_startegy/pnl_reports'


# # List of expiry dates passed by the user
# expiry_dates = ['27APR23', '25MAY23','29JUN23', '27JUL23','31AUG23', '28SEP23', '26OCT23', '30NOV23', '28DEC23','25JAN24', '29FEB24','28MAR24']
# Run for APR_2023 only with the specified expiry date pattern (e.g., '27APR23')
expiry_date = '28MAR24'
process_month_folder(index_dir, option_dir, 'MAR_2024', expiry_date, output_dir)





#stoploss 100% ->(entryprice + entryprice*100) -if any sell position[ce or pe] sl hit,then remove that position and their corresponding hedge and also track the  position entry price ,,that if again that price come during market,,if come then atke gain that take smae position with their hedge else  continue