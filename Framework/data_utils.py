from BinanceDataPipeline import binance_data_pipeline as bdp
import pandas as pd
import pandas_ta as ta
import numpy as np
import random

class Data:

    def __init__(self, ticker: str, frequency: str, start_date: str, end_date: str):
        """Constructor for the object which will store the raw and processed data.

        Args:
            ticker (str): Ticker of the crypto trading pair (e.g., "BTCUSDT")
            frequency (str): Time intervals of the historical data (e.g., "1h")
            start_date (str): Start date of the historical data (e..g, "1 Jan 2025")
            end_date (str): End date of the historical data (e.g., "1 Jan 2025")
        """
        data_pipeline = bdp.BinanceDataPipeline()
        self.ticker = ticker
        self.data = data_pipeline.import_historical_data(ticker, frequency, start_date, end_date)
        self.data_bt = None # To be set by the define_windows() method from the DataUtils class.
        self.data_wf = None # To be set by the define_windows() method from the DataUtils class.


class DataUtils:

    # INSERT DATA UTILS METHODS HERE


    @staticmethod
    def define_windows(data_obj: Data):
        """
        Class method to divide the historical data into two sections. One will be designated for backtesting, and
        the other will be designated for the walk forward test. This method should be called after any other
        data_utils methods so that both data_obj.data_bt and data_obj.data_wf have all the data needed to run
        tests on them.

        Parameters:
            data_obj (Data): Data object.

        Returns:
            (pd.DataFrame, pd.DataFrame): Two DataFrames: one for 'Backtest' rows, and one for 'Walk Forward' rows.
        """
        raw_data = data_obj.data

        # Total number of rows in the DataFrame
        n = len(raw_data)
        # Vectorized assigning of window labels based on the row's relative position in the DataFrame.
        import numpy as np
        raw_data["Window"] = np.where((np.arange(n) + 1) / n <= 0.7, "Backtest", "Walk Forward")

        # Splitting the DataFrame into two separate DataFrames based on the assigned window labels.
        backtest_data = raw_data.loc[raw_data["Window"] == "Backtest"].copy()
        walkforward_data = raw_data.loc[raw_data["Window"] == "Walk Forward"].copy()        
        return backtest_data, walkforward_data
    

    @staticmethod
    def log_trade(trade: dict, data: pd.DataFrame):
        """Method to be called during algorithm execution which will log a trade.
        A bunch of acrobatics had to be performed in this code to actually store the trade dictionary
        in the dataframe because for some reason it just wouln't work with normal attempts.
        In the future this code may be made more clean.

        Args:
            trade (dict): Dictionary containing the trade details.
            data (pd.DataFrame): This should be one of the Data instance variables which hold a dataframe of historical data. It is where the trades will be logged.
        """
        # If "Trade Log" does not exist, create it as an empty list for each row.
        if "Trade Log" not in data.columns:
            data["Trade Log"] = [[] for _ in range(len(data))]  # Initialize as lists

        # Creating a copy of the "Trade Log" column
        trade_log_copy = data["Trade Log"].copy()

        # Identifying the rows where the "Open time" equals trade["time"] (should only be one)
        matching_indices = data.index[data["Open time"] == trade["time"]]

        # Iterating over each matching row and append the trade dict to the corresponding list (again, should only be one row, but for some reason only using one row didn't work).
        for index in matching_indices:
            # Using .loc for safe scalar access.
            trade_log_copy.loc[index] = trade_log_copy.loc[index] + [trade]

        # Assigning the modified copy back to data["Trade Log"]
        data["Trade Log"] = trade_log_copy
