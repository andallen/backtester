# Backtester
This is a framework for importing historical data, managing data, implementing trading algorithms, and backtesting trading algorithms. It is designed for testing trading algorithms for cryptocurrencies listed on BinanceUS.

The BinanceDataPipeline directory contains everything needed to import the historical data using the Binance API. This code is abstracted away by the DataUtils class and none of the BinanceDataPipeline methods need to be called directly in the driver.py file when filling out the framework to test your own algorithm.

In the Framework directory, data_utils.py and algorithm.py must be adjusted to fit the specific algorithm that the user of the framework wants to test. Spots which the user must implement themselves are marked by comments in those two files. When filling out the framework, the user must also initialize a driver.py file and fill it out in order to run the backtest on their algorithm.

The ExampleMACrossoverImplementation directory shows a fully functioning example of the framework filled out, including the driver.py file which runs all necessary code to perform the backtest and display results. This example is of a simple moving average crossover algorithmic implementation which uses the pandas-ta library.

You can refer to the documentation present in each code file for specific details on the implementation and purpose of each method in the framework.

Note: I began using this GitHub account for personal projects after completing this project, so I had to upload the full project to this account. That is why there are so few commits for this project.
