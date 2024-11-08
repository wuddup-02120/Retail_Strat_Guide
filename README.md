# Retail Strat Guide

Welcome to the **Retail Strat Guide** repository! This guide will walk you through setting up and running a trading strategy backtest on various securities' historical price data. The repository includes a universal Python backtesting script and 51 different securities' 1-minute time series dataset managed through Git LFS (Git Large File Storage). This guide is designed to be accessible even for those new to programming.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Trading Strategy](#trading-strategy)
- [Data Cleaning with Bollinger Bands](#data-cleaning-with-bollinger-bands)
- [Repository Contents](#repository-contents)
- [Setup and Installation](#setup-and-installation)
  - [Step 1: Clone the Repository](#step-1-clone-the-repository)
  - [Step 2: Install Dependencies](#step-2-install-dependencies)
  - [Step 3: Run the Backtest](#step-3-run-the-backtest)
- [Understanding the Output](#understanding-the-output)
- [Explanation of the Code](#explanation-of-the-code)
- [Troubleshooting and FAQs](#troubleshooting-and-faqs)

---

## Project Overview

This repository is designed to help users backtest a quantitative trading strategy on securities' 1-minute historical data. A backtest allows you to simulate trades using historical data to see how a strategy might have performed in the past. The strategy focuses on detecting specific trading signals and tracking entries and exits based on configurable drawdown and stop-loss levels.

## Trading Strategy

The strategy uses the following logic:

1. **Valid Trading Day**:
   - Identify a day as a "valid trading day" if the opening price is at least 0.5% higher than the prior day’s closing price.

2. **Signal Detection at 11:15 AM**:
   - For each valid trading day, check the price at 11:15 AM. If the price at this time is higher than the opening price of the day, this signals a potential trade.

3. **Trade Entry with Drawdown**:
   - For each signal, test multiple drawdown levels (0.25% to 2.0% in 0.25% increments). If the price falls to a defined drawdown level before the market close, a trade entry is made.

4. **Stop-Loss and Exit**:
   - Each entry also has a stop-loss level (tested from 0.5% to 5.0% in 0.5% increments). There are three exit scenarios:
     - **Profit Target**: The price returns to the signal price before the end of the next trading day, exiting with a profit.
     - **Stop-Loss**: The price hits the stop-loss level, exiting to limit losses.
     - **Final Exit**: If neither of the above conditions is met, the trade is closed at the end of the second day.

The strategy tests various combinations of drawdown and stop-loss levels for each signal, storing results to analyze what levels may provide the best returns.

## Data Cleaning with Bollinger Bands

To enhance the quality of data used in backtesting, this repository includes a data cleaning step that leverages Bollinger Bands to identify and filter non-tradable candles, particularly those in the pre-market period.

### Purpose of the Data Cleaning Step

Bollinger Bands are used to detect candles that are likely due to overnight clearing orders processed through dark pools and similar mechanisms. These candles, often appearing in pre-market data, may not represent significant, tradable price swings and are therefore excluded from analysis.

### Logic of the Data Cleaning Step

1. **Calculate Bollinger Bands**:
   - Compute a 50-period moving average with bands set at 3 standard deviations above and below the average.

2. **Filter Specific Time Range**:
   - Focus on pre-market data between 8:00 AM and 9:00 AM.

3. **Identify Non-Tradable Candles**:
   - Highlight and remove candles where the high price exceeds the upper band or the low price falls below the lower band.

This step ensures that anomalous pre-market data that could skew backtest results is appropriately managed.

---

## Repository Contents

- **`backtest.py`**: A Python script for running the backtest on the AAPL dataset. The script is universally structured so that users can easily set file paths, start dates, and parameter levels to customize the backtest.
- **`process_bollinger.py`**: A Python script for data cleaning using Bollinger Bands to filter out non-tradable pre-market candles.
- **`AAPL_full_1min_UNADJUSTED.txt`**: A 1-minute interval time series dataset for AAPL (from January 1, 2012, onward), managed with Git LFS due to its size. The dataset includes columns for `datetime`, `open`, `high`, `low`, `close`, and `volume`.

---

## Setup and Installation

### Prerequisites

Ensure you have the following installed:

- **Python** (version 3.7 or above): [Download Python](https://www.python.org/downloads/)
- **Git**: [Download Git](https://git-scm.com/downloads)
- **Git Large File Storage (LFS)**: [Download Git LFS](https://git-lfs.github.com/)

### Step 1: Clone the Repository

1. **Clone the repository** using Git. Open a terminal or command prompt and run:

   ```bash
   git lfs install  # Initializes Git LFS
   git clone https://github.com/wuddup-02120/Retail_Strat_Guide.git
   cd Retail_Strat_Guide
   ```

   This command installs Git LFS (if not already installed), then clones the repository and navigates into the repository folder.

### Step 2: Install Dependencies

The script requires the `pandas` library for data processing. Install it by running:

   ```bash
   pip install pandas
   ```

### Step 3: Run the Backtest

1. **Open `backtest.py` in a text editor** (like VS Code or Notepad++).

2. **Set file paths** in the script:
   - `input_file`: Path to the dataset (`AAPL_full_1min_UNADJUSTED.txt`).
   - `output_file`: Desired path for the output CSV (e.g., `backtest_trade_details.csv`).

3. **Configure optional parameters**:
   - `start_date`: Filter data to start from a specific date (default is `"2020-01-01"`).
   - `drawdown_levels` and `stop_loss_levels`: Define levels in percentage terms.

4. **Run the script**:

   ```bash
   python backtest.py
   ```

The script will process the data and save results to the specified output file.

---

## Understanding the Output

The backtest results are saved in a CSV file (e.g., `backtest_trade_details.csv`) with the following columns:

| Column              | Description                                                                                       |
|---------------------|---------------------------------------------------------------------------------------------------|
| `signal_price`      | The price at the 11:15 AM signal time on a valid trading day.                                     |
| `entry_price`       | The price at which a trade is entered based on the drawdown level.                                |
| `entry_datetime`    | The exact date and time when the trade was entered.                                               |
| `lowest_price`      | The lowest price recorded during the holding period.                                              |
| `exit_price`        | The price at which the trade was exited.                                                          |
| `exit_datetime`     | The date and time when the trade was exited.                                                      |
| `trade_return (%)`  | The percentage return for the trade.                                                              |
| `drawdown_level (%)`| The drawdown level (e.g., 0.5%) at which the trade was entered.                                   |
| `stop_loss_level (%)`| The stop-loss level (e.g., 1.0%) applied to the trade.                                           |
| `exit_reason`       | Reason for exit (e.g., "Stop-loss", "Profit Target", or "Final Exit").                            |

This output allows users to analyze each trade, evaluate performance, and optimize drawdown and stop-loss levels.

---

## Explanation of the Code

The `backtest.py` script performs the following steps:

1. **Load Data**: Reads the dataset, assigns column names, and parses dates.
2. **Filter and Sort**: Filters data to start from a specified date and sorts it by datetime.
3. **Resampling for Daily Data**: Resamples the data to daily frequency to detect trading signals based on open and close prices.
4. **Backtest Loop**:
   - Iterates over each drawdown and stop-loss combination.
   - For each valid trading day, it checks for signals, entries, and exits.
5. **Record Results**: Appends each trade's details to a list and exports the results to a CSV file.

Each section of the script includes comments to guide users on modifying parameters and understanding each part of the logic.

---

## Troubleshooting and FAQs

**Q: I get a "File not found" error when running the script.**

- Make sure `input_file` points to the correct location of `AAPL_full_1min_UNADJUSTED.txt` and that Git LFS has successfully downloaded the dataset.

**Q: The script runs, but the output file is empty.**

- This could happen if the `start_date` filter is too restrictive, leaving no data to process. Ensure the start date matches dates in your dataset.

**Q: I get an error about a missing package.**

- Run `pip install pandas` to ensure that all dependencies are installed.

**Q: How can I modify the script for other datasets?**

- Update the `input_file` path, column names (if different), and ensure the file format is compatible with the script. Adjust parameters as needed.

---

## Additional Resources

- [Git LFS Documentation](https://git-lfs.github.com/) for handling large files.
- [Pandas Documentation](https://pandas.pydata.org/) to understand data manipulation with Python.

## License

This project is open for educational purposes. If you modify or build upon this work, please credit the original author.

---

This README provides comprehensive instructions, explanations, and troubleshooting to make it easy for anyone, even without programming experience, to replicate and understand the backtest process. Happy backtesting!

