from alt_backtest import strategy, position

from config import long_period, short_period, stop_loss, risk, all_period
from indicators import MACDIndicator, SMA

rsi_prev = []

class PositionSize:
    def get(self, balance, price):
        risky_distance = (price - (price * (1 - (stop_loss / 100))))
        return int((balance * risk) / risky_distance)

class TrendStrategy(strategy.Strategy):
    order = None

    def __init__(self):
        super().__init__()

        self._macd_list = []
        self.macd = MACDIndicator(short_period= short_period, long_period = long_period, period=all_period)
        self.sma = SMA(period=all_period)
        self.sma_short = SMA(period=short_period)

        self.size = PositionSize()
        self.order = None
        self.stop_loss = None
        self.available = None

    def next(self):

        if not self.in_position():
            if self.macd.macd[0] > self._signal():
                self.available = self.size.get(self.get_current_balance(), self.get_price())
                self.order = self.send_market_order_buy(size=self.available)
                self.position_status = position.Position.long
                self.stop_loss = self.get_price() * (1 - (stop_loss / 100))
                return

            if self.macd.macd[0] < self._signal():
                self.available = self.size.get(self.get_current_balance(), self.get_price())
                self.order = self.send_market_order_sell(size=self.available)
                self.position_status = position.Position.short
                self.stop_loss = self.get_price() * (1 + (stop_loss / 100))
            return

        if self.position_status == position.Position.long:
            if self.sma_short.sma[0] > self.sma.sma[0]:
                self.send_market_order_buy(size=self.available)
                self.position_status = position.Position.none
                return

            if (self.sma_short.sma[0] < self.sma.sma[0]) or self.get_price() <= self.stop_loss:
                self.send_market_order_sell(size=self.available)
                self.position_status = position.Position.none
                return


        if self.position_status == position.Position.short:
            if self.macd.macd[0] > self._signal():
                self.send_market_order_buy(size=self.available)
                self.position_status = position.Position.none
            if self.macd.macd[0] < self._signal():
                self.send_market_order_sell(size=self.available)
                self.position_status = position.Position.none

    def margin_call(self):
        raise Exception("Not implemented")

    def _signal(self):
        alpha = 2 / (len(self._macd_list) + 1)
        self._macd_list.append(self.macd.macd[0])
        ema = self._macd_list[0]

        for macd in self._macd_list[1:]:
            ema = alpha * macd + (1 - alpha) * ema

        return ema