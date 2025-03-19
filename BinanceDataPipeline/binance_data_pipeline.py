# FUTURE IMPLEMENTATION NOTES: THE REPEATED RETRY LOGIC SHOULD BE HANDLED BY A HELPER METHOD.

#Import necessary libraries.
import pandas as pd
from dotenv import load_dotenv
from binance.client import Client
from binance.exceptions import (
    BinanceAPIException,
    BinanceRequestException
)
import os
import logging
import time

#Configuring logging
logging.basicConfig(filename="the_log.log", level=logging.DEBUG, 
                    format="%(levelname)s - %(filename)s - %(funcName)s - Line %(lineno)d: %(message)s")

class BinanceDataPipeline:

    def __init__(self, api_key: str = None, secret_key: str = None, tld: str = "us") -> None:
        """Initializes the BinanceDataPipeline object.

        Args:
            api_key (str, optional): The api key which is used to access the Binance API. Defaults to None.
            secret_key (str, optional): The secret key which is used to access the Binance API. Defaults to None.
            tld (str, optional): Indicates which Binance server the API will connect to. Defaults to "us".

        Raises:
            ValueError: Raised if the API keys were not set properly.
        """

        # Default values for the Binance API Keys
        if api_key is None or secret_key is None:
            load_dotenv()
            api_key = os.getenv("BINANCE_API_KEY")
            secret_key = os.getenv("BINANCE_SECRET_KEY")

        self.client = Client(api_key, secret_key, tld=tld)
        logging.info("Binance client initialized successfully.")


    def import_historical_data(self, ticker: str, frequency: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Instance method to import historical data for a given ticker, time interval, and time frequency.
        Other methods that use this method should check if the returned DataFrame is empty and handle it accordingly.

        Parameters:
            ticker (str): The trading pair (e.g., "BTCUSDT").
            frequency (str): Time frequency (e.g., "1d").
            start_date (str): The beginning date of the range (e.g, "1 Jan 2017").
            end_date (str): The ending date of the range (e.g., "1 Jan 2018").

        Returns:
            pd.DataFrame: A dataframe containing the historical data.
        """
        # Setting parameters for the request retries in case of a transient error.
        max_retries = 3
        delay = 1
        for attempt in range(1, max_retries + 1):
            try:
                klines = self.client.get_historical_klines(ticker, frequency, start_date, end_date)
                break  # If it's successful, exit the loop.
            except (BinanceAPIException, BinanceRequestException) as e:
                if BinanceDataPipeline.transient_error(e):
                    logging.warning(
                        "Transient error encountered on attempt %d/%d: %s. Retrying in %d seconds...",
                        attempt,
                        max_retries,
                        e,
                        delay
                    )
                    time.sleep(delay)
                    delay *= 2  # Exponentially increase the delay.
                else:
                    logging.error("Non-transient error encountered: %s", e)
                    raise
        else:
            # Since all retry attempts have failed, raise an exception.
            logging.error("Failed to fetch historical data for %s after %d attempts.", ticker, max_retries)
            raise Exception("Max retries reached for import_historical_data.")
        
        # This handles the issue of empty historical data being fetched.
        if not klines:
            logging.warning("No data returned for %s between %s and %s.", ticker, start_date, end_date)
            return pd.DataFrame()
        
        # Converts data to a dataframe.
        data = pd.DataFrame(klines, columns=[
            "Open time", "Open", "High", "Low", "Close", "Volume",
            "Close time", "Quote asset volume", "Number of trades",
            "Taker buy base asset volume", "Taker buy quote asset volume", "Ignore"
        ])
        
        # Convert the open time column to datetime and set it as the index. Also set the close time column to datetime.
        data["Open time"] = pd.to_datetime(data["Open time"], unit="ms")
        data["Close time"] = pd.to_datetime(data["Close time"], unit="ms")
        data.set_index("Close time", inplace=True)

        # Convert columns to numeric data for easier processing down the line.
        cols_to_convert = [
            "Open", "High", "Low", "Close", "Volume",
            "Quote asset volume", "Number of trades", 
            "Taker buy base asset volume", "Taker buy quote asset volume"
        ]
        data[cols_to_convert] = data[cols_to_convert].apply(pd.to_numeric, errors="coerce")

        # Return the dataframe.
        return data
    

    @staticmethod
    def transient_error(error: BinanceAPIException | BinanceRequestException) -> bool:
        """Method that checks if an error is transient to determine if the request should be retried.

        Args:
            error (BinanceAPIException | BinanceRequestException): The BinanceAPI error.

        Returns:
            bool: True if the error is transient, and False otherwise.
        """
        match error.code:
            case -1000 | -1001 | -1008 | -1015 | -1021:
                return True
            case _:
                return False
        







    
    # THESE METHODS ARE NOT VERY USEFUL ANYMORE AND SHOULD BE MOVED TO A SEPARATE CLASS IN THE FUTURE.

    def get_usdt_tickers(self) -> pd.DataFrame:
        """Gets all USDT tickers on BinanceUS.

        Returns:
            pd.DataFrame: Returns a pandas dataframe of all USDT tickers.
        """
        # Setting parameters for the request retries in case of a transient error.
        max_retries = 3
        delay = 1
        for attempt in range(1, max_retries + 1):
            try:
                tickers = self.client.get_all_tickers()
                break # If it's successful, the loop is exited.
            except (BinanceAPIException, BinanceRequestException) as e:
                if BinanceDataPipeline.transient_error(e):
                    logging.warning(
                    "Transient error encountered on attempt %d/%d: %s. Retrying in %d seconds...",
                    attempt,
                    max_retries,
                    e,
                    delay
                    )
                    time.sleep(delay)
                    delay *= 2 # Delay is exponentially increased with each attempt.
                else:
                    logging.error("Non-transient error encountered: %s", e)
                    raise
        else:
            # If the loop normally completes normally, then all retries failed, so there is an error.
            logging.error("Failed to get tickers after %d attempts.", max_retries)
            raise Exception("Max retries reached for get_usdt_tickers.")

        usdt_tickers = [ticker["symbol"] for ticker in tickers if ticker["symbol"].endswith("USDT")]
        logging.info("Fetched %d USDT tickers.", len(usdt_tickers))
        return pd.DataFrame(usdt_tickers, columns=["Ticker"])
    

    def save_usdt_tickers(self, filepath: str = "binanceus_tickers.csv") -> None:
        """
        Retrieve USDT tickers and save them to a CSV file.

        Parameters:
            filepath (str): The path to the CSV file where tickers will be saved.
        """
        df = self.get_usdt_tickers()
        df.to_csv(filepath, index=False)