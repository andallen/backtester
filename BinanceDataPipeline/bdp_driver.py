from binance_data_pipeline import BinanceDataPipeline
from binance.client import Client
from binance.exceptions import BinanceAPIException
import os

def main():

    # Load API keys from environment variables (ensure these are set or provide incorrect keys to force an error)
    api_key = os.getenv("BINANCE_API_KEY", "invalid_key")
    secret_key = os.getenv("BINANCE_SECRET_KEY", "invalid_secret")

    # Initialize the Binance client
    client = Client(api_key, secret_key, tld="us")

    try:
        # Attempt to fetch historical data for a non-existent trading pair to trigger an error
        client.get_historical_klines("INVALIDPAIR", "1d", "1 Jan 2021", "1 Jan 2022")
    except BinanceAPIException as e:
        # Print the error code and message to inspect its contents
        print(f"Error Code: {e.code}, Message: {e.message}")


if __name__ == "__main__":
    main()