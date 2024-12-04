from alt_backtest import start

from config import start_cash,data__path, start_date,end_date, format_date
from strategy import MixedStrategy

start.run(MixedStrategy, start_cash, data__path,start_date,end_date, format_date)