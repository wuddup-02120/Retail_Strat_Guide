import pandas as pd

# User Instructions:
# 1. Set the `input_file` variable to the path of your dataset file.
# 2. Set the `output_file` variable to the desired path for the output file.
# 3. Adjust the `start_date`, `drawdown_levels`, and `stop_loss_levels` as desired.

# Path to the dataset file
input_file = "path/to/your/AAPL_1min_data.csv"  # Replace with your file path
output_file = "path/to/output/backtest_trade_details.csv"  # Replace with your desired output path

# Load the data, add column names, and parse dates
print("Loading data...")
data = pd.read_csv(
    input_file,
    header=None,
    names=["datetime", "open", "high", "low", "close", "volume"],
    parse_dates=["datetime"]
)
print("Data loaded successfully with shape:", data.shape)

# Ensure the data is sorted by datetime for correct temporal order
data.sort_values(by="datetime", inplace=True)
print("Data sorted by datetime.")

# Filter the data to include only records from January 1, 2020, onward (or modify as needed)
start_date = "2020-01-01"  # Modify to your preferred start date
data = data[data["datetime"] >= start_date]
print(f"Data filtered to start from {start_date}. New shape: {data.shape}")

# Set datetime as the index for easier time-based operations
print("Setting datetime as index...")
data.set_index("datetime", inplace=True)

# Resample data to daily frequency for signal detection; include only market hours
market_open = "09:30"
market_close = "16:00"
print("Resampling data to daily frequency for open and close prices (9:30 to 16:00)...")
daily_data = data.between_time(market_open, market_close).resample("D").agg({"open": "first", "close": "last"})
print("Daily data created with shape:", daily_data.shape)

# Define parameters for backtesting
drawdown_levels = [x * 0.25 for x in range(1, 5)]  # Test drawdowns [0.25%, 0.5%, ..., 1.0%]
stop_loss_levels = [x * 0.5 for x in range(1, 5)]  # Test stop-losses [0.5%, 1.0%, ..., 2.0%]
trades = []  # List to store detailed trade information for each test

# Begin backtest loop
print("Starting backtest over drawdown levels:", drawdown_levels)
for drawdown in drawdown_levels:
    print(f"Processing drawdown level: {drawdown}%")
    
    # Loop through each stop-loss level for the current drawdown level
    for stop_loss in stop_loss_levels:
        print(f"Testing stop-loss level: {stop_loss}% with drawdown level: {drawdown}%")
        
        # Iterate over each day to identify valid trading signals
        for date in daily_data.index:
            print(f"\nChecking date: {date}")
            try:
                # Signal 1: Check if today's open is >= prior day's close * 1.005
                prior_close = daily_data.loc[date - pd.Timedelta(days=1), "close"]
                print("Prior day close:", prior_close)
                
                if daily_data.loc[date, "open"] >= prior_close * 1.005:
                    print("Valid trading day signal found for date:", date)
                    
                    # Define 11:15 AM timestamp on the signal day for signal price check
                    signal_time = pd.Timestamp(date.year, date.month, date.day, 11, 15)
                    if signal_time not in data.index:
                        print(f"No data available at signal time {signal_time}, skipping this date.")
                        continue

                    signal_price = data.loc[signal_time, "close"]
                    print("Signal price at 11:15:", signal_price)
                    
                    # Signal 2: Check if 11:15 close price > open price of the day
                    if signal_price > daily_data.loc[date, "open"]:
                        print("Valid signal confirmed at 11:15 on:", date)
                        
                        # Monitor drawdown within the signal day (11:15 to 4:00 PM)
                        drawdown_entry_price = signal_price * (1 - drawdown / 100)
                        print(f"Checking for entry at drawdown entry price: {drawdown_entry_price}")
                        
                        # Define intraday window for drawdown check (11:15 AM to 4:00 PM)
                        intraday_data = data.between_time("11:15", "16:00").loc[date:date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)]
                        if intraday_data.empty:
                            print(f"No intraday data available for {date} from 11:15 to 16:00, skipping this date.")
                            continue

                        entry = intraday_data[intraday_data["close"] <= drawdown_entry_price]
                        
                        if not entry.empty:
                            entry_price = entry.iloc[0]["close"]
                            entry_time = entry.index[0]
                            print("Entry found at", entry_time, "with price:", entry_price)
                            
                            # Calculate stop-loss based on entry price
                            stop_loss_price = entry_price * (1 - stop_loss / 100)
                            print(f"Stop-loss price set at: {stop_loss_price}")
                            
                            # Define next day's market hours (9:30 AM to 4:00 PM)
                            next_day_open = entry_time + pd.Timedelta(days=1)
                            next_day_open = next_day_open.replace(hour=9, minute=30)
                            next_day_close = next_day_open.replace(hour=16, minute=0)
                            
                            # Record the lowest price during the holding period
                            holding_period_data = data.loc[entry_time:next_day_close]
                            min_price = holding_period_data["low"].min()
                            print("Lowest price during holding period:", min_price)
                            
                            # Check for exit conditions (profit target, stop-loss, or final close)
                            next_day_data = data.loc[next_day_open:next_day_close]
                            if next_day_data.empty:
                                print(f"No next-day data available for {next_day_open.date()} from 09:30 to 16:00, skipping this trade.")
                                continue

                            profit_exit = next_day_data[next_day_data["close"] >= signal_price]
                            stop_loss_exit = next_day_data[next_day_data["close"] <= stop_loss_price]
                            
                            # Exit based on stop-loss or profit target
                            if not stop_loss_exit.empty:
                                exit_price = stop_loss_exit.iloc[0]["close"]
                                exit_time = stop_loss_exit.index[0]
                                trade_return = (exit_price - entry_price) / entry_price * 100
                                exit_reason = "Stop-loss"
                                print(f"Stop-loss exit at {exit_time} with exit price: {exit_price}")
                            elif not profit_exit.empty:
                                exit_price = profit_exit.iloc[0]["close"]
                                exit_time = profit_exit.index[0]
                                trade_return = (exit_price - entry_price) / entry_price * 100
                                exit_reason = "Profit Target"
                                print(f"Profit exit achieved at {exit_time} with exit price: {exit_price}")
                            else:
                                final_exit_price = next_day_data.iloc[-1]["close"]
                                final_exit_time = next_day_data.index[-1]
                                trade_return = (final_exit_price - entry_price) / entry_price * 100
                                exit_price = final_exit_price
                                exit_time = final_exit_time
                                exit_reason = "Final Exit"
                                print(f"No profit or stop-loss exit, final exit at {final_exit_time} with price: {final_exit_price}")
                            
                            # Store detailed trade information
                            trades.append({
                                "signal_price": signal_price,
                                "entry_price": entry_price,
                                "entry_datetime": entry_time,
                                "lowest_price": min_price,
                                "exit_price": exit_price,
                                "exit_datetime": exit_time,
                                "trade_return (%)": trade_return,
                                "drawdown_level (%)": drawdown,
                                "stop_loss_level (%)": stop_loss,
                                "exit_reason": exit_reason
                            })
                            print("Trade recorded:", trades[-1])
            
            except KeyError as e:
                # Handle any missing data issues gracefully
                print("KeyError encountered:", e)
                continue

# Save trades to a CSV file for analysis
trades_df = pd.DataFrame(trades)
trades_df.to_csv(output_file, index=False)
print(f"Trade details saved to '{output_file}'.")
