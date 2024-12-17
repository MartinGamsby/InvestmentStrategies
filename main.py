import csv
import yfinance as yf
import pandas as pd
import os
import shutil

tickers = tickers = [ \
    'BND',
    'SPY',
    'QQQ', 
    ]

def get_history(tickers, start_year, end_year, interval):
    tickers_data = {}
    for ticker in tickers:
        print(f"Fetching data for {ticker}")
        combined_data = pd.DataFrame()
        # Read existing data from CSV files into combined_data
        for year in range(start_year, end_year + 1):
            file_name = f'data/stock_data_{ticker}_{interval}_{year}.csv'
            if os.path.isfile(file_name):
                data = pd.read_csv(file_name, index_col=0)
                combined_data = combined_data._append(data)
            else:
                # Fetch new data and append to combined_data if not already present
                start_date = f'{year}-01-01'
                end_date = f'{year + 1}-01-01'

                # Check if data for the year is already present in combined_data
                #if f'{year}-01-01' not in combined_data.index:
                data = yf.download([ticker], start=start_date, end=end_date, interval=interval)
                print(data)
                #combined_data = combined_data._append(data)
                # Save new data to a CSV file
                try:
                    os.makedirs("data")
                except:
                    pass
                data.to_csv(file_name, quoting=csv.QUOTE_NONNUMERIC)#https://stackoverflow.com/questions/43913521/pandas-to-csv-and-from-csv-number-of-reords-mismatch
                
                # I picked this project from a while ago, and doesn't behave the same.
                # I don't want to check why it does this rght now, just edit the file afterwards ...
                file_name_temp = file_name + "~"
                shutil.move(file_name, file_name_temp)
                destination = open(file_name, "w")
                source = open(file_name_temp, "r")
                for line in source:              
                    if line == '"Price","Adj Close","Close","High","Low","Open","Volume"':
                        destination.write('"Date","Open","High","Low","Close","Adj Close","Volume"')
                    elif line.startswith('"Ticker",'):
                        continue
                    elif line.startswith('"Date",'):
                        continue
                    else:
                        destination.write(line)
                source.close()
                destination.close()
                os.remove(file_name_temp)
                
                data = pd.read_csv(file_name, index_col=0)
                combined_data = combined_data._append(data)

        tickers_data[ticker] = combined_data
    return tickers_data
    
def test_dca(data, shares_strategy, num_months, investment_amount):    
    for i in range(num_months):
        if i == 0:  # First month
            shares_strategy.iloc[i, 0] = float(investment_amount) / data.Close.iloc[i]
        else:
            shares_strategy.iloc[i, 0] = shares_strategy.iloc[i - 1, 0] + (float(investment_amount) / data.Close.iloc[i])
    
def test_lump_sum(data, shares_strategy, num_months, investment_amount):    
    for i in range(num_months):
        if i == 0:  # First month
            shares_strategy.iloc[i, 0] = float(investment_amount*num_months) / data.Close.iloc[i]
        else:
            shares_strategy.iloc[i, 0] = shares_strategy.iloc[i - 1, 0]
            
def test_strategy(tickers_data, ticker, num_months, investment_amount, columns, strategy, suffix):   
    print(ticker)

    data = tickers_data[ticker]
    strategy_name = ticker+suffix
    columns.append(strategy_name)

    ## Calculate the number of shares bought for each ETF monthly based on QQQ performance
    shares_strategy = pd.DataFrame(0, index=data.index, columns=[strategy_name])
    portfolio_value_strategy = pd.Series(0, index=data.index)
    
    strategy(data, shares_strategy, num_months, investment_amount)
    return shares_strategy[strategy_name] * data.Close
    
def test_tickers():
            
    tickers_data = get_history( tickers=tickers,
       start_year=2020, end_year=2024, interval='1mo')


    investment_amount = 1000  # Amount invested each month
        
        
    first_data = tickers_data[next(iter(tickers_data))]
    num_months = len(first_data.index)
    
    invested_value = pd.DataFrame(0, index=first_data.index, columns=["Invested"] )
    for i in range(num_months):
        if i == 0:  # First month
            invested_value.iloc[i, 0] += investment_amount
        else:
            invested_value.iloc[i, 0] = invested_value.iloc[i - 1, 0] + investment_amount
    
    
    compare_portfolios = invested_value
    columns = ["Invested"]
    for ticker in tickers_data:        
        # Calculate the number of months in the data
        portfolio_value_strategy = test_strategy(tickers_data, ticker, num_months, investment_amount, columns, test_dca, " DCA")
        compare_portfolios = pd.concat([compare_portfolios, portfolio_value_strategy], axis=1)
        
        portfolio_value_strategy = test_strategy(tickers_data, ticker, num_months, investment_amount, columns, test_lump_sum, " Lump Sum")        
        compare_portfolios = pd.concat([compare_portfolios, portfolio_value_strategy], axis=1)

    print("\nCompare portfolios")
    compare_portfolios.columns = columns
    print(compare_portfolios) 
    
    import matplotlib.pyplot as plt
    compare_portfolios.plot()
    plt.show()
        
test_tickers()
        