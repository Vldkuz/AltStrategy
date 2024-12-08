from math import sqrt

from alt_backtest import Strategy, Position

from indicators import MACDIndicator, RSI, EMA, SMA
from config import *


class MixedStrategy(Strategy):
    margin = False
    previous = None

    def __init__(self):
        super().__init__()
        self.previous_stop_loss = None
        self.previous_stop_buy = None

        self.e_short_indicator = EMA(period=short_period)
        self.e_long_indicator = EMA(period=long_period)
        self._short_sma = SMA(period=short_sma_period)
        self._long_sma = SMA(period=long_sma_period)
        self.last_mcs = []
        self.margin_c = 1

        self.stop_loss = stop_loss
        self.upper_stop_buy = upper_stop_loss

        self.risk = risk

    def get_volume(self, income_price, stop_loss, risk):
        if self.margin:
            self.margin_c //= 2
            self.margin = False
        else:
            self.margin_c = 1

        return (risk * self.get_current_balance() * self.margin_c) / abs(income_price - stop_loss)

    def next(self):
        if not (
                self.e_long_indicator.is_ready()
                and self.e_short_indicator.is_ready()
                and self._short_sma.is_ready()
                and self._long_sma.is_ready()) :
            return

        price = self.get_price()

        self.previous_stop_loss = self.stop_loss
        self.previous_stop_buy = self.upper_stop_buy

        self.stop_loss = 0.9 * price
        self.upper_stop_buy = price * 1.2

        volume = self.get_volume(price, stop_loss, self.risk)

        if not self.in_position():
            if self.e_short_indicator.ema[0] > self.e_long_indicator.ema[0] and self._short_sma.sma[0] > self._long_sma.sma[0]:
                self.send_market_order_buy(size=volume)
                self.position_status = Position.long
                self.previous = self.position_status
                return
            elif self.e_short_indicator.ema[0] < self.e_long_indicator.ema[0] and self._short_sma.sma[0] < self._long_sma.sma[0]:
                self.send_market_order_sell(size=volume)
                self.position_status = Position.short
                self.previous = self.position_status
                return

        if self.position_status == Position.long:
            if price < self.previous_stop_loss:
                print("StopLoss", price)
                self.send_market_order_sell(size = volume)
                self.position_status = Position.none
                return

            if self.e_short_indicator.ema[0] < self.e_long_indicator.ema[0] and self._short_sma.sma[0] < self._long_sma.sma[0]:
                self.send_market_order_sell(size=volume)
                self.position_status = Position.long
                return

        if self.position_status == Position.short:
            if price > self.previous_stop_buy:
                self.send_market_order_buy(size = volume)
                self.position_status = Position.none
                return
        if self.e_short_indicator.ema[0] > self.e_long_indicator.ema[0] and self._short_sma.sma[0] > self._long_sma.sma[0]:
            self.send_market_order_buy(size=volume)
            self.position_status = Position.none
            return

    def margin_call(self):
        self.margin = True

        volume = self.get_volume(self.get_price(), stop_loss, self.risk)

        if self.previous == Position.long:
            self.send_market_order_buy(size = volume)
        else:
            self.send_market_order_sell(size = volume)



        # Здесь продаем 10 акций портфеля, чтобы немного снизить убыток, но все же сидим в позиции
















