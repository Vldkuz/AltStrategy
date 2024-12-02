from alt_backtest import start

from config import start_cash,data__path, start_date,end_date, format_date
from strategy import TrendStrategy

start.run(TrendStrategy, start_cash, data__path,start_date,end_date, format_date)