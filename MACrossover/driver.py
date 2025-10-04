from MACrossover import data_utils as du
from MACrossover import backtest as bt
from MACrossover import algorithm as alg
import pickle
import pandas as pd

def main():
    base_data = du.Data("BTCUSDT", "1d", "1 Jan 2024", "31 Dec 2024")
    extended_data = du.Data("BTCUSDT", "1d", "1 Jan 2023", "31 Dec 2023")
    du.DataUtils.calculate_ma(base_data, extended_data, 5, 20)
    data_bt, data_wf = du.DataUtils.define_windows(base_data)

    algorithm = alg.Algorithm(data_bt, 10000, 0, 0.002, 1, 0.05)
    bt.RunBacktest.run_backtest(algorithm)

    with open("data_log.pkl", "rb") as file:
        backtest_data = pickle.load(file)
    storage = bt.BacktestDataStorage()
    bt.BacktestDataUtils.process_backtest_full(backtest_data, extended_data, storage)
    for key, value in vars(storage).items():
         print(f"{key} : {value}")
    

main()