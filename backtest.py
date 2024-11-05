import pandas as pd

# Load the data, add column names, and parse dates
print("Loading data...")
data = pd.read_csv(
    r"C:\1 Minute Data\stocks\A_data_unzipped\AAPL_full_1min_UNADJUSTED.txt",
    header=None,
    names=["datetime", "open", "high", "low", "close", "volume"],
    parse_dates=["datetime"]
)
print("Data loaded successfully with shape:", data.shape)

# Sort the data by datetime to ensure temporal structure is correct
data.sort_values(by="datetime", inplace=True)
print("Data sorted by datetime.")

# Filter the data to include only records from January 1, 2020, onward
start_date = "2020-01-01"
data = data[data["datetime"] >= start_date]
print(f"Data filtered to start from {start_date}. New shape: {data.shape}")

# Set datetime as the index
print("Setting datetime as index...")
data.set_index("datetime", inplace=True)

# Resample the data to get the daily open and close prices for signal identification, only during market hours
print("Resampling data to daily frequency for open and close prices (9:30 to 16:00)...")
market_open = "09:30"
market_close = "16:00"
daily_data = data.between_time(market_open, market_close).resample("D").agg({"open": "first", "close": "last"})
print("Daily data created with shape:", daily_data.shape)

# Parameters for backtest
drawdown_levels = [x * 0.25 for x in range(1, 5)]  # [0.25, 0.5, ..., 2.0]
stop_loss_levels = [x * 0.5 for x in range(1, 5)]  # [0.5, 1.0, ..., 5.0]
trades = []  # Store details of each trade for each drawdown and stop-loss combination

# Iterate over each drawdown level
print("Starting backtest over drawdown levels:", drawdown_levels)
for drawdown in drawdown_levels:
    print(f"Processing drawdown level: {drawdown}%")
    
    # Iterate over each stop-loss level for the current drawdown level
    for stop_loss in stop_loss_levels:
        print(f"Testing stop-loss level: {stop_loss}% with drawdown level: {drawdown}%")
        
        # Loop through each day to check for valid signals
        for date in daily_data.index:
            print(f"\nChecking date: {date}")
            try:
                # Signal 1: Open >= prior day's close * 1.005
                prior_close = daily_data.loc[date - pd.Timedelta(days=1), "close"]
                print("Prior day close:", prior_close)
                
                if daily_data.loc[date, "open"] >= prior_close * 1.005:
                    print("Valid trading day signal found for date:", date)
                    
                    # Define the 11:15 AM timestamp on the signal day
                    signal_time = pd.Timestamp(date.year, date.month, date.day, 11, 15)
                    if signal_time not in data.index:
                        print(f"No data available at signal time {signal_time}, skipping this date.")
                        continue  # Skip if the 11:15 AM data is missing

                    signal_price = data.loc[signal_time, "close"]
                    print("Signal price at 11:15:", signal_price)
                    
                    # Signal 2: 11:15 close price > open price of the day
                    if signal_price > daily_data.loc[date, "open"]:
                        print("Valid signal confirmed at 11:15 on:", date)
                        
                        # Monitor drawdown within the trading hours of the signal day (11:15 AM to 4:00 PM)
                        drawdown_entry_price = signal_price * (1 - drawdown / 100)
                        print(f"Checking for entry at drawdown entry price: {drawdown_entry_price}")
                        
                        # Define the intraday window from 11:15 AM to 4:00 PM on the signal day
                        intraday_data = data.between_time("11:15", "16:00").loc[date:date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)]
                        if intraday_data.empty:
                            print(f"No intraday data available for {date} from 11:15 to 16:00, skipping this date.")
                            continue  # Skip if no intraday data is available

                        entry = intraday_data[intraday_data["close"] <= drawdown_entry_price]
                        
                        if not entry.empty:
                            entry_price = entry.iloc[0]["close"]
                            entry_time = entry.index[0]
                            print("Entry found at", entry_time, "with price:", entry_price)
                            
                            # Calculate stop-loss price based on entry price
                            stop_loss_price = entry_price * (1 - stop_loss / 100)
                            print(f"Stop-loss price set at: {stop_loss_price}")
                            
                            # Define the next day's trading hours (9:30 AM to 4:00 PM) for exit conditions
                            next_day_open = entry_time + pd.Timedelta(days=1)
                            next_day_open = next_day_open.replace(hour=9, minute=30)
                            next_day_close = next_day_open.replace(hour=16, minute=0)
                            
                            # Capture the lowest price until the exit condition is met
                            holding_period_data = data.loc[entry_time:next_day_close]
                            min_price = holding_period_data["low"].min()
                            print("Lowest price during holding period:", min_price)
                            
                            # Check for exit conditions within the holding period until next day's 4:00 PM
                            next_day_data = data.loc[next_day_open:next_day_close]
                            if next_day_data.empty:
                                print(f"No next-day data available for {next_day_open.date()} from 09:30 to 16:00, skipping this trade.")
                                continue  # Skip if no next-day data is available

                            profit_exit = next_day_data[next_day_data["close"] >= signal_price]
                            stop_loss_exit = next_day_data[next_day_data["close"] <= stop_loss_price]
                            
                            # Determine exit based on stop-loss or profit exit
                            if not stop_loss_exit.empty:
                                # Exit at stop-loss
                                exit_price = stop_loss_exit.iloc[0]["close"]
                                exit_time = stop_loss_exit.index[0]
                                trade_return = (exit_price - entry_price) / entry_price * 100
                                exit_reason = "Stop-loss"
                                print(f"Stop-loss exit at {exit_time} with exit price: {exit_price}")
                            elif not profit_exit.empty:
                                # Exit at profit target
                                exit_price = profit_exit.iloc[0]["close"]
                                exit_time = profit_exit.index[0]
                                trade_return = (exit_price - entry_price) / entry_price * 100
                                exit_reason = "Profit Target"
                                print(f"Profit exit achieved at {exit_time} with exit price: {exit_price}")
                            else:
                                # Final exit at close of the second day if no other exits met
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

# Convert trades to DataFrame and save to CSV for detailed analysis
trades_df = pd.DataFrame(trades)
output_path = r"C:\Users\Brandon\Desktop\Tutorial_Video_Files\backtest_trade_details.csv"
trades_df.to_csv(output_path, index=False)
print(f"Trade details saved to '{output_path}'.")
