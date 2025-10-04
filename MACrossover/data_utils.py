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

    @staticmethod
    def calculate_ma(data_obj: Data, data_extended: Data, fast_sma_len: int, slow_sma_len: int):
        """Method that calculates the two moving averages for the data. It is required that the user
        initializes two Data objects in the driver class/method to pass in for data_obj and data_extended.
        data_extended will be appended to the start of data_obj so that the data in data_extended
        can be used to calculate the moving averages so that the first moving average values in
        data_obj.data are not NaN. After this method, data_extended will be removed.

        Args:
            data_obj (Data): The Data object which will store the resulting data.
            data_extended (Data): The end_data argument for the initialization of this object should be 1 day before the start_date of data_obj (for example if data_obj's start date is 1 Jan 2025, extended_data's end_date should be 31 Dec 2024), and start_data should be long enough before data_extended's end_date to acommodate the moving average's size.
            fast_sma_len (int): The length of the window to be used in the fast SMA calculation.
            slow_sma_len (int): The length of the window to be used in the slow SMA calculation.
        """
        # Combine the extended data (which precedes data_obj.data) to data_obj.data.
        combined_data = pd.concat([data_extended.data, data_obj.data], ignore_index=False)

        # Calculate first and second moving averages. `append=True` creates new columns: SMA_{length}
        # The moving average values are shifted since pandas_ta uses the current row in its calculation, which would cause
        # look ahead bias since order execution is based on opening price.
        combined_data["Fast SMA"] = ta.sma(combined_data["Close"], length=fast_sma_len).shift(1)
        combined_data["Slow SMA"] = ta.sma(combined_data["Close"], length=slow_sma_len).shift(1)

        # Remove the extended data and set the data_obj.data DataFrame to include the moving average data.
        data_obj.data = combined_data.drop(data_extended.data.index)


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
