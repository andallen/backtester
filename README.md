# Backtester

This is a Python program I wrote that can test trading strategies on past cryptocurrency data. It downloads historical prices from BinanceUS, applies a trading rule (in the MACrossover example, a moving average crossover), simulates trades using that rule on historical data, and then performs an analysis of the results.

---

## How to run a quick test of the example

1) **Requirements**
   - Python **3.10+**
   - The instructions are for macOS/Linux but you can use Windows too, you just have to change the commands.

2) **Open the Terminal and Clone and enter the project**
```bash
git clone https://github.com/andallen/backtester.git
cd backtester
```

3) **Create a virtual environment and install dependencies**
```bash
python -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

4) **Enter API keys** 

Refer to this [link](https://support.binance.us/en/articles/9842800-how-to-create-an-api-key-on-binance-us$0) to generate your API keys for BinanceUS.
Then, create a `.env` file in the repository root and run the following commands:
```bash
echo "BINANCE_API_KEY=your_key"   >> .env
echo "BINANCE_SECRET_KEY=your_secret" >> .env
```

5) **Run the example**
```bash
python MACrossover/driver.py
```
What happens:
- Downloads BTCUSDT daily candles for 2023–2024
- Computes two SMAs (5/20) and splits the data into two sections: **Backtest** (70%) and **Walk‑Forward** (30%). The data is separated in case optimization functionality is added, in which case you only want to optimize parameters on Backtest and then test the optimized algorithm on Walk-Forward to minimize overfitting.
- Runs the SMA‑crossover strategy while incorporating trading fees, slippage (average mismatch between order price and order execution price), and a stop‑loss.
- Creates and writes to `data_log.pkl` and prints a summary of the results to the console.

---

## Expanded Description

This is a framework to backtest trading strategies on crypto price data. You can find the ideas/explanation underlying the code in the 'Backtester Framework Conceptual Explanation.pdf' in this repository, which aggregates a lot of information I found useful during my research on algorithmic trading. 

The functionality is separated into:
- **Data Pipeline** (Data ingestion from BinanceUS)
- **Data Utilities** (Functions to prepare the data for the backtest)
- **Strategy Logic** (handles trading signals, risk/capital management, and order execution)
- **Backtest Runner & Analysis** (handles looping through historical data, logging, maintaing metrics, and analysis of metrics)

---

## Repository layout

```
pythonparrot-backtester/
├─ BinanceDataPipeline/
│  ├─ binance_data_pipeline.py      # BinanceUS client + historical data loader
│  └─ bdp_driver.py                 # Stand‑alone file to debug binance_data_pipeline (optional)
├─ MACrossover/                     # Example implementation of the framework
│  ├─ data_utils.py                 # Data model + features + windowing + logging helpers
│  ├─ algorithm.py                  # Signals, risk/capital mgmt, execution, core Algorithm
│  ├─ backtest.py                   # Backtest loop + metrics + analysis utilities
│  └─ driver.py                     # Copy of Framework, with an end‑to‑end runnable example filled in
└─ Framework/                       # The base template copy to be filled in by you with other strategies
   ├─ data_utils.py
   ├─ algorithm.py
   └─ backtest.py
```

---

## How the pieces fit together

```
          +-------------------------+
          | BinanceDataPipeline     |
          | - import_historical_data|
          +-----------+-------------+
                      |
                      v
          +-------------------------+
          | Data (DataUtils)        |
          | - calculate_ma          | *this is specific to MACrossover
          | - define_windows        |
          | - log_trade             |
          +-----------+-------------+
                      |
                 (DataFrames)
                      |
                      v
          +-------------------------+
          | Algorithm               |
          | - SignalDetector        |
          | - CapitalManagement     |
          | - RiskManagement        |
          | - TradeExecution        |
          +-----------+-------------+
                      |
                      |
                      v
          +-------------------------+
          | Backtest                |
          | - RunBacktest           |
          | - BacktestDataUtils     |
          | - BacktestDataAnalysis  |
          +-------------------------+
```

For further information, read the documentation included in the code for each function.

## Dependencies

All Python package dependencies are listed in `requirements.txt`. Install them with:
```bash
pip install -r requirements.txt
```

---

## Limitations

- This framework does not handle portfolio allocation.
- This framework splits data to prepare it for optimization, but it does not provide code to optimize parameters.
