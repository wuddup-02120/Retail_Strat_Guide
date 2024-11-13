import pandas as pd
import os

def process_file(file_path, output_folder_filtered, output_folder_analysis):
    # Load the data into a DataFrame
    print(f"Loading data from {file_path}...")
    columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
    df = pd.read_csv(file_path, names=columns, parse_dates=['datetime'])
    df.set_index('datetime', inplace=True)
    print(f"Data loaded successfully. DataFrame shape: {df.shape}")

    # Calculate Bollinger Bands with a 50-period moving average and 3 standard deviations
    print("Calculating Bollinger Bands...")
    df['moving_avg'] = df['close'].rolling(window=50, min_periods=1).mean()
    df['std_dev'] = df['close'].rolling(window=50, min_periods=1).std()
    df['upper_band'] = df['moving_avg'] + (3 * df['std_dev'])
    df['lower_band'] = df['moving_avg'] - (3 * df['std_dev'])

    # Filter data between 8:00 am and 9:00 am only
    print("Filtering data between 8:00 am and 8:30 am...")
    df_filtered = df.between_time('08:00', '08:30')
    print(f"Filtered DataFrame shape: {df_filtered.shape}")

    # Identify candles that exceed the upper or lower Bollinger Bands
    print("Identifying candles that exceed the Bollinger Bands...")
    results = []

    for i in range(len(df_filtered)):
        current = df_filtered.iloc[i]

        # Check if the high or low exceeds the upper or lower Bollinger Bands
        if current['high'] > current['upper_band'] or current['low'] < current['lower_band']:
            results.append({
                'datetime': current.name,
                'open': current['open'],
                'high': current['high'],
                'low': current['low'],
                'close': current['close'],
                'moving_avg': current['moving_avg'],
                'upper_band': current['upper_band'],
                'lower_band': current['lower_band']
            })
            print(f"Candle exceeding Bollinger Bands found at {current.name}")

    # Create a DataFrame for the results
    print("Creating results DataFrame...")
    results_df = pd.DataFrame(results)
    print(f"Results DataFrame created. Number of identified candles: {len(results_df)}")

    # Save the filtered dataset (excluding identified weird candles)
    print("Removing identified candles from the original dataset...")
    if not results_df.empty:
        df_filtered_cleaned = df.drop(index=results_df['datetime'])
        filtered_output_path = os.path.join(output_folder_filtered, os.path.basename(file_path))
        os.makedirs(output_folder_filtered, exist_ok=True)
        df_filtered_cleaned.to_csv(filtered_output_path)
        print(f"Filtered dataset saved to {filtered_output_path}")

    # Save the analysis of weird candles
    if not results_df.empty:
        analysis_output_path = os.path.join(output_folder_analysis, f"{os.path.splitext(os.path.basename(file_path))[0]}_weird_candles_analysis.csv")
        os.makedirs(output_folder_analysis, exist_ok=True)
        results_df.to_csv(analysis_output_path, index=False)
        print(f"Weird candles analysis saved to {analysis_output_path}")
    else:
        print("No weird candles identified.")

# Input and output folder paths (use environment variables or relative paths)
input_folder = os.getenv('INPUT_FOLDER', 'input_data')
output_folder_filtered = os.getenv('OUTPUT_FOLDER_FILTERED', 'output/filtered_data')
output_folder_analysis = os.getenv('OUTPUT_FOLDER_ANALYSIS', 'output/weird_candles_analysis')

# Process all files in the input folder
print("Processing all files in the input folder...")
os.makedirs(input_folder, exist_ok=True)

for file_name in os.listdir(input_folder):
    if file_name.endswith(".txt"):
        file_path = os.path.join(input_folder, file_name)
        process_file(file_path, output_folder_filtered, output_folder_analysis)

print("All files processed.")
