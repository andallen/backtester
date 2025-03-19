from MACrossover import data_utils as du
import pandas as pd
import numpy as np


class SignalDetector:
    """Handles trade signal detection logic."""
    
    @staticmethod
    def detect_entry(previous_row: pd.Series, current_row: pd.Series) -> str:
        """Determines if there is an entry signal in the previous row of data.

        Args:
            previous_row (pd.Series): Previous row's data, usually from the Data object's data_bt or data_wf instance variables.
            current_row (pd.Series): Current row's data, usually from the Data object's data_bt or data_wf instance variables.

        Returns:
            str: Returns a string that indicates whether an entry signal was detected or not.
        """
        # Conditional that makes sure there is signal data in the previous row in order to properly handle the
        # first row in the data.

        # INSERT ENTRY DETECTION LOGIC HERE


    @staticmethod
    def detect_exit(previous_row: pd.Series, current_row: pd.Series) -> bool:
        """Determines if there is an exit signal in the previous row.

        Args:
            previous_row (pd.Series): Previous row's data, usually from the Data object's data_bt or data_wf instance variables.
            current_row (pd.Series): Current row's data, usually from the Data object's data_bt or data_wf instance variables.

        Returns:
            bool: True if there is an exit condition in the previous row, False otherwise.
        """
        # INSERT EXIT DETECTION LOGIC HERE

class CapitalManagement:
    """Handles the account's capital adjustments."""

    def __init__(self, initial_capital: float, fee: float, slippage: float, data: pd.DataFrame):
        """Initializes a CapitalManagement instance and
        necessary instance variables.

        Args:
            initial_capital (float): The initial balance of the account (e.g., 10000).
            fee (float): The trading fee of the crypto exchange (e.g., 0.006). 0.01 means a 1% fee.
            slippage (float): The slippage per entry and exit (e.g., 0.002). 0.01 means 1% slippage.
        """
        self.total_capital = initial_capital # Will hold liquid capital + capital in trade
        self.liquid_capital = initial_capital # Will hold only the capital that is not in a trade
        self.fee = fee
        self.slippage = slippage
        self.data = data

        # Creating the "Capital Log" column
        self.data["Capital Log"] = np.nan

        # Inserting the initial capital at the first row of the "Capital Log" column so because the run_backtest() method in the backtest class "skips" over the first row.
        self.data.loc[self.data.index[0], "Capital Log"] = initial_capital
    

    def log_capital(self, row: pd.Series):
        """Stores the current total capital in the historical data.

        Args:
            row (pd.Series): Row of the DataFrame corresponding to the data entry.
        """

        # Insert the current total capital into the row's "Capital Log" cell.
        self.data.at[row.name, "Capital Log"] = self.total_capital


class RiskManagement:
    """Handles the algorithm's risk management."""

    def __init__(self, position_size: float, max_loss_pct: float):
        """Initializes the RiskManagement object and all necessary instance variables.

        Args:
            position_size (float): The % of total capital to be risked/entered for each trade (e.g., 0.01). A value of 0.01, for example, corresponds to 1% of total capital to be risked per trade.
            max_loss_pct (float): The maximum allowed loss, in % of entry capital, before a stop limit order is executed (e.g., 0.1). A value of 0.1, for example, corresponds to an maximum allowed loss of 10% of entry capital.
        """
        self.position_size = position_size
        self.max_loss_pct = max_loss_pct


    @staticmethod
    def compute_current_loss(current_trade: dict, current_row: pd.Series) -> float:
        """
        Computes the current unrealized dollar loss of an open trade
        using the current row's opening price.
        """
        current_price = current_row["Open"]
        potential_exit_capital = current_trade["entry_capital"] * (current_price / current_trade["entry_price"])
        return current_trade["entry_capital"] - potential_exit_capital


class TradeExecution:
    """Manages trade execution."""

    def __init__(self, capital_manager: CapitalManagement, risk_manager: RiskManagement, data: pd.DataFrame):
        """Initializes a TradeExecution object and all necessary instance variables.

        Args:
            capital_manager (CapitalManagement): CapitalManagement object parameter facilitates the integration of account capital updates with trade execution.
            risk_manager (RiskManagement): RiskManagement object parameter facilitates the integration of risk management with trade execution.
            data (pd.DataFrame): Dataframe which is an instance variable of a Data object.
        """
        self.capital_manager = capital_manager
        self.risk_manager = risk_manager
        self.data = data


    def execute_entry(self, current_row: pd.Series) -> dict:
        """This method will be called whenever SignalDetector's detect_entry method returns "Entry". It simulates
        entering a trade position and updates the account's capital.

        Args:
            current_row (pd.Series): The current row of the dataframe of the data on which the algorithm is being tested.

        Returns:
            dict: Dictionary of the trade details which will be set equal to the Algorithm object's current_trade instance variable.
        """
        entry_amount = self.capital_manager.liquid_capital * self.risk_manager.position_size
        self.capital_manager.liquid_capital -= entry_amount
        initial_trade_capital = entry_amount * (1 - self.capital_manager.fee - self.capital_manager.slippage)
        self.capital_manager.total_capital = self.capital_manager.liquid_capital + initial_trade_capital

        trade = {
            "type": "entry",
            "time": current_row["Open time"],
            "entry_capital": initial_trade_capital,
            "entry_price": current_row["Open"]
        }

        du.DataUtils.log_trade(trade, self.data)

        return trade


    def execute_exit(self, current_trade: dict, current_row: pd.Series, stop_limit: bool):
        """Executes trade exit, logs the trade, and updates capital. Handles both stop limit exits and normal exits.

        Args:
            current_trade (dict): Dictionary containing the trade details of the currently open trade.
            current_row (pd.Series): The current row of the dataframe of the data on which the algorithm is being tested.
            stop_limit (bool): Boolean value indicating whether the exit is through a stop limit order (True) or not (False).
        """
        fee_slip_multiplier = 1 - (self.capital_manager.fee + self.capital_manager.slippage)

        if stop_limit:
            price_change_multiplier = 1 - self.risk_manager.max_loss_pct
            trade = {
                "type": "exit_stop_limit",
                "time": current_row["Open time"],
                "exit_capital": price_change_multiplier * current_trade["entry_capital"] * fee_slip_multiplier
            }
        else:
            price_change_multiplier = current_row["Open"] / current_trade["entry_price"]
            trade = {
                "type": "exit",
                "time": current_row["Open time"],
                "exit_price": current_row["Open"],
                "exit_capital": price_change_multiplier * current_trade["entry_capital"] * fee_slip_multiplier
            }
        du.DataUtils.log_trade(trade, self.data)
        self.capital_manager.liquid_capital += trade["exit_capital"]
        self.capital_manager.total_capital = self.capital_manager.liquid_capital


class Algorithm:
    """Handles the trading algorithm by coordinating signal detection, trade execution, capital management, and risk management."""

    def __init__(self, data: pd.DataFrame, initial_capital: float, fee: float, slippage: float, position_size: float, max_loss_pct: float):
        """Initializes the Algorithm object and all necessary instance variables.

        Args:
            data (pd.DataFrame): One of the instance variables of the Data object like data_bt.
            initial_capital (float): Initial balance of the trading account. Example argument: 10000.
            fee (float): Trading fee of the crypto exchange which will be applied at entry AND exit; if the exchange only applies fees once per entry/exit, pass in half of their actual fee. Example argument: 0.006 (represents 0.6%).
            slippage (float): Slippage per trade which will be applied at entry AND exit. Example argument: 0.002 (represents 0.2%).
            position_size (float): Percentage of total capital to be risked/entered for every trade entry. Example argument: 0.1 (represents 10%).
            max_loss_pct (float): Maximum percentage of capital that was entered into the trade which is allowed to be lost before a stop limit order is executed. Example argument: 0.1 (represents 10%).
        """

        # Instantiating helper classes
        self.capital_manager = CapitalManagement(initial_capital, fee, slippage, data)
        self.risk_manager = RiskManagement(position_size, max_loss_pct)
        self.trade_executor = TradeExecution(self.capital_manager, self.risk_manager, data)
        
        # Instance variable to keep track of whether or not a trade is open.
        self.current_trade = None

        self.data = data # The data that will be iterated over during the backtest.


    def on_new_row(self, previous_row: pd.Series, current_row: pd.Series):
        """Processes each new data row (from a DataFrame of the Data object) to determine and execute trades.

        Args:
            previous_row (pd.Series): Previous row of data.
            current_row (pd.Series): Current row of data.
        """
        # Placed before the operations below in order to align with how market returns are calculated.
        self.capital_manager.log_capital(current_row)

        if self.current_trade is None:
            # Checking for entry signal in the previous row.
            signal = SignalDetector.detect_entry(previous_row, current_row)
            if signal == "Entry":
                self.current_trade = self.trade_executor.execute_entry(current_row)
        else:
            # Managing open trade: check for stop limit exit or MA crossover exit, and manage capital if trade is not closed.
            current_loss = self.risk_manager.compute_current_loss(self.current_trade, current_row)
            if current_loss >= (self.risk_manager.max_loss_pct * self.current_trade["entry_capital"]):
                self.trade_executor.execute_exit(self.current_trade, current_row, stop_limit=True)
                self.current_trade = None
            elif SignalDetector.detect_exit(previous_row, current_row):
                self.trade_executor.execute_exit(self.current_trade, current_row, stop_limit=False)
                self.current_trade = None
            else:
                price_change_multipler = current_row["Open"] / self.current_trade["entry_price"]
                current_capital_in_trade = self.current_trade["entry_capital"] * price_change_multipler
                self.capital_manager.total_capital = self.capital_manager.liquid_capital + current_capital_in_trade