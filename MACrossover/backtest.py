import pickle
import logging
from MACrossover import algorithm as alg
import pandas as pd
import matplotlib.pyplot as plt
import random
from MACrossover import data_utils as du
import pandas_ta as ta
import numpy as np


class RunBacktest:
    """Class that contains a method to run the backtest."""

    @staticmethod
    def run_backtest(algorithm: alg.Algorithm):
        """Iterates through the data, executes the algorithm, and stores the resulting data as a pickle file.

        Args:
            algorithm (alg.Algorithm): Algorithm object which contains everything needed to run the algorithm on the historical data.

        Raises:
            ValueError: ValueError is raised if something goes wrong processing the new row.
        """

        data = algorithm.data

        # Variable that will store the previous row in the iteration.
        previous_row = None

        # Iterates through each row in data.
        for index, row in data.iterrows():
            if previous_row is None:
                previous_row = row
                continue

            try:
                algorithm.on_new_row(previous_row, row)
            except Exception as e:
                raise ValueError(f"Error processing new row: {e}")
            previous_row = row

        # Saving all the data in a .pkl file
        try:
            with open("data_log.pkl", "wb") as file:
                pickle.dump(algorithm.data, file)
        except Exception as e:
            raise


class BacktestDataStorage:
    """Class that will store important data regarding the backtest."""
    def __init__(self):
        self.data = None # Will be set after all BacktestDataUtils methods are ran.
        self.beta = None # Will store the beta value (indicating the systematic risk of the strategy) after the calc_beta() method is called.
        self.total_return_usd = None # Will store the total dollar amount of profit/loss after the calc_total_returns() method is called.
        self.total_return_pct = None # Will store the total % of profit/loss during after the calc_total_returns() method is called.
        self.volatility_regime_avg_returns = None # Will store a dictionary of average returns for the three different volatility regimes.
        self.market_regime_avg_returns = None # Will store a dictionary of average returns for the two volatility regimes.


class BacktestDataUtils:
    """Class that contains the methods necessary to process and prepare the backtest data for analysis."""

    @staticmethod
    def calc_strategy_returns(data: pd.DataFrame):
        """Calculates the returns of the tested strategy and stores it in the ["Capital Returns"] column of the testing data.

        Args:
            data (pd.DataFrame): Pandas dataframe of a data instance variable from the Data object.
        """
        data["Capital Returns"] = (data["Capital Log"] - data["Capital Log"].shift(1)) / data["Capital Log"].shift(1)


    @staticmethod
    def calc_market_returns(data: pd.DataFrame):
        """Calculates the market returns during the testing window.

        Args:
            data (pd.DataFrame): Pandas dataframe of a data instance variable from the Data object.
        """
        data["Market Returns"] = (data["Open"] - data["Open"].shift(1)) / data["Open"].shift(1)

    
    @staticmethod
    def calc_beta(data: pd.DataFrame, storage: BacktestDataStorage):
        """Calculates the beta (systematic risk) by comparing capital returns to market returns
        and storing the value in the passed in BacktestDataStorage object's beta instance variable.

        Args:
            data (pd.DataFrame): Pandas dataframe of a data instance variable from the Data object.
            storage (BacktestDataStorage): Object which contains the beta instance variable where the beta value will be stored.
        """
        # Compute the covariance matrix for capital and market returns.
        cov_matrix = data[["Capital Returns", "Market Returns"]].cov().values
        
        # Extracting covariance between strategy and market returns.
        covariance = cov_matrix[0, 1]
        # Extracting variance of market returns.
        variance = cov_matrix[1, 1]
        
        # Calculating beta.
        storage.beta = covariance / variance


    @staticmethod
    def calc_total_returns(data: pd.DataFrame, storage: BacktestDataStorage):
        """Method that calculates the total profit/loss over the backtest period.

        Args:
            data (pd.DataFrame): Pandas DataFrame of a data instance variable from the Data object.
            storage (BacktestDataStorage): BacktestDataStorage object which contains the beta instance variable where the beta value will be stored.
        """
        storage.total_return_usd = round(data["Capital Log"].iloc[-1] - data["Capital Log"].iloc[0], 2)
        storage.total_return_pct = round(((data["Capital Log"].iloc[-1] - data["Capital Log"].iloc[0]) \
                                          / data["Capital Log"].iloc[0]) * 100, 2)


    @staticmethod
    def calc_market_regime(data: pd.DataFrame, data_extended: du.Data) -> pd.DataFrame:
        """
        Calculate the market regime (bull vs. bear) using a 200-day moving average.

        This method concatenates the extended market data to avoid NaN issues, calculates the 200 moving average of 
        the "Open" price (shifted by one period), and sets the market regime to "bull" if the current open is above 
        the moving average, or "bear" otherwise.

        Args:
            data (pd.DataFrame): DataFrame of the main market data.
            data_extended (du.Data): Data object containing extended market data.

        Returns:
            pd.DataFrame: DataFrame with market returns, moving average, and market regime.
        """
        # Concatenate extended data to avoid NaNs in the testing data.
        local_data = pd.concat([data_extended.data, data], ignore_index=False)
        
        # Compute the 200-day simple moving average (shifted by one period to avoid look-ahead bias).
        local_data["MA 200"] = ta.sma(local_data["Open"], length=200).shift(1)

        local_data = local_data.drop(data_extended.data.index)

        # Define market regime: bull if Open > MA 200, else bear.
        local_data["Market Regime"] = np.where(local_data["Open"] > local_data["MA 200"], "bull", "bear")
        
        return local_data
        

    @staticmethod
    def calc_volatility_regime(data: pd.DataFrame, data_extended: du.Data) -> pd.DataFrame:
        """Categorizes the volatility of the market based on ATR.

        Args:
            data (pd.DataFrame): The main testing data.
            data_extended (du.Data): Data object containing the extended data.

        Returns:
            pd.DataFrame: Returns a DataFrame that is meant to be reassigned to the variable containing the main testing data.
        """
        # Concatenate extended data to avoid NaNs in the calculations.
        local_data = pd.concat([data_extended.data, data], ignore_index=False)

        # Calculate 60-day ATR and shift it by one period
        local_data["ATR"] = ta.atr(
            high=local_data["High"], 
            low=local_data["Low"], 
            close=local_data["Close"], 
            length=14
        ).shift(1)

        # Remove the extended data.
        local_data = local_data.drop(data_extended.data.index)

        # Classify the ATR into three quantile-based categories.
        local_data["Volatility Regime"] = pd.qcut(
        local_data["ATR"],
        q=3,
        labels=["low", "medium", "high"]
        )

        return local_data

    
    @staticmethod
    def calc_market_regime_avg_returns(storage: BacktestDataStorage):
        """Calculates and stores the average returns for each market regime (bull/bear). Averages
        are multiplied by 100 for easier readability."""

        # Group by "Market Regime" and calculate the mean of "Capital Returns"
        avg_returns_dict = storage.data.groupby("Market Regime")["Capital Returns"].mean().to_dict()
        
        # Multiply each value by 100 for percentage representation
        updated_avg_returns = {}
        for regime, avg_return in avg_returns_dict.items():
            updated_avg_returns[regime] = round(avg_return * 100, 2)

        # Store the updated dictionary
        storage.market_regime_avg_returns = updated_avg_returns


    @staticmethod
    def calc_volatility_regime_avg_returns(storage: BacktestDataStorage):
        """Calculates and stores the average returns for each volatility regime. Averages are multiplied by 100
        for easier readability."""
        # Group by "Volatility Regime" and calculate the mean of "Capital Returns"
        avg_returns_dict = storage.data.groupby("Volatility Regime")["Capital Returns"].mean().to_dict()
    
        # Multiply each value by 100 for percentage representation
        updated_avg_returns = {}
        for regime, avg_return in avg_returns_dict.items():
            updated_avg_returns[regime] = round(avg_return * 100, 2)
    
        # Store the updated dictionary
        storage.volatility_regime_avg_returns = updated_avg_returns

    
    @staticmethod
    def save_backtest_data(data: pd.DataFrame, storage: BacktestDataStorage):
        """Sets the data instance variable of a BacktestDataStorage object to the passed in DataFrame.

        Args:
            storage (BacktestDataStorage): Object which will contain the instance variable to store the data.
            data (pd.DataFrame): DataFrame which will bes tored in the instance variable of the BacktestDataStorage object.
        """
        storage.data = data

    
    @staticmethod
    def process_backtest_full(data: pd.DataFrame, data_extended: du.Data, storage: BacktestDataStorage):
        BacktestDataUtils.calc_strategy_returns(data)
        BacktestDataUtils.calc_market_returns(data)
        BacktestDataUtils.calc_beta(data, storage)
        BacktestDataUtils.calc_total_returns(data, storage)
        temp_data = BacktestDataUtils.calc_market_regime(data, data_extended)
        BacktestDataUtils.save_backtest_data(temp_data, storage)
        temp_data = BacktestDataUtils.calc_volatility_regime(storage.data, data_extended)
        BacktestDataUtils.save_backtest_data(temp_data, storage)
        BacktestDataUtils.calc_market_regime_avg_returns(storage)
        BacktestDataUtils.calc_volatility_regime_avg_returns(storage)


class BacktestDataAnalysis:
    """Class with methods that help with the analysis of the backtest data stored in an object of type BacktestDataStorage."""

    @staticmethod
    def plot_capital_log(storage: BacktestDataStorage):
        """Method that plots the total capital data over the testing period.

        Args:
            storage (BacktestDataStorage): Object storing the backtest data.
        """
        data = storage.data
        plt.figure(figsize=(10, 6))
        plt.plot(data["Open time"], data["Capital Log"], label="Capital Log", linewidth=2)
        plt.xlabel("Open time")
        plt.ylabel("Total Capital")
        plt.title("Total Capital Over Time")
        plt.legend()
        plt.grid(True)
        plt.show()


    @staticmethod
    def order_check(storage: BacktestDataStorage, number: int):
        """Prints a user-provided number of random orders and the first stop limit order that was executed during
        the backtest (if there is one) so that the user can verify correct algorithm behavior, for example by
        comparing algorithmic execution with TradingView charts to make sure everything is as it should be.

        Args:
            data (pd.DataFrame): Pandas DataFrame of a data instance variable from the Data object.
            number (int): The number of random trade events that the user wants printed out.
        """
        data = storage.data
        print("RANDOMlY SELECTED ORDERS:")

        # Filtering out empty lists from the "Trade Log" column.
        non_empty_trades = data[data["Trade Log"].apply(len) != 0]
        print(non_empty_trades)

        # Print 'number' random trade events.
        for i in range(number):
            print(random.choice(non_empty_trades["Trade Log"]))

        # Find and print the first list of trade dictionaries containing a stop-limit exit.
        for index, row in non_empty_trades.iterrows():
            trade_list = row["Trade Log"]
            # Check if there's a dictionary in trade_list with "type": "exit_stop_limit"
            if any(trade.get("type") == "exit_stop_limit" for trade in trade_list):
                print("FIRST STOP-LIMIT ORDER FOUND:")
                print(trade_list)
                break
        else:
            print("No stop-limit exits found in this dataset.")