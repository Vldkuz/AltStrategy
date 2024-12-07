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
        self.m_indicator = MACDIndicator(short_period = short_period, long_period = long_period)
        self.r_indicator = RSI(period = rsi_period)
        self.e_short_indicator = EMA(period=short_period)
        self.e_long_indicator = EMA(period=long_period)
        self._short_sma = SMA(period=short_sma_period)
        self._long_sma = SMA(period=long_sma_period)
        self.last_mcs = []
        self.last_ema_short = []
        self.last_ema_long = []

        self.margin_c = 1

        self.min_flet_rsi = min_flet_rsi
        self.max_flet_rsi = max_flet_rsi

        self.max_rsi = max_rsi
        self.min_rsi = min_rsi

        self.rsi_sell = rsi_sell
        self.rsi_buy = rsi_buy

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
        if not (self.m_indicator.is_ready() and self.r_indicator.is_ready()):
            return

        price = self.get_price()

        self.previous_stop_loss = self.stop_loss
        self.previous_stop_buy = self.upper_stop_buy

        self.stop_loss = 0.9 * price
        self.upper_stop_buy = price * 1.2

        self.last_mcs.append(self.m_indicator.macd[0])
        volume = self.get_volume(price, stop_loss, self.risk)
        signal = self.m_indicator.ema(self.last_mcs, 0, len(self.last_mcs))

        if not self.in_position():
            if self.min_flet_rsi <= self.r_indicator.rsi[0] <= self.max_flet_rsi:
                if self.r_indicator.rsi[0] <= self.min_rsi:
                    self.send_market_order_buy(size = volume)
                    self.position_status = Position.long
                    self.previous = self.position_status
                    print("Mean", price)
                    return
                elif self.r_indicator.rsi[0] >= self.max_rsi:
                    self.send_market_order_sell(size = volume)
                    self.position_status = Position.short
                    self.previous = self.position_status
                    print("Mean", price)
                return
            else:
                if self.m_indicator.macd[0] - signal > 0 and self._short_sma.sma[0] > self._long_sma.sma[0]:
                    self.send_market_order_buy(size = volume)
                    self.position_status = Position.long
                    self.previous = self.position_status
                    return
                elif self.m_indicator.macd[0] - signal < 0 and self._short_sma.sma[0] < self._long_sma.sma[0]:
                    self.send_market_order_sell(size = volume)
                    self.position_status = Position.short
                    self.previous = self.position_status
                    return
                else:
                    return

        if self.position_status == Position.long:
            if price < self.previous_stop_loss:
                print("StopLoss", price)
                self.send_market_order_sell(size = volume)
                self.position_status = Position.none
                return

            if self.min_flet_rsi < self.r_indicator.rsi[0] < self.max_flet_rsi:
                if self.r_indicator.rsi[0] >= self.rsi_sell and self.e_short_indicator.ema[0] > self.e_long_indicator.ema[0] and self._short_sma.sma[0] < self._long_sma.sma[0]:
                    self.send_market_order_sell(size = volume)
                    self.position_status = Position.none

                    return
            else:
                signal = self.m_indicator.ema(self.last_mcs, 0, len(self.last_mcs))

                if self.m_indicator.macd[0] - signal < 0 and self.e_short_indicator.ema[0] <= self.e_long_indicator.ema[0] and self._short_sma.sma[0] < self._long_sma.sma[0]:
                    self.send_market_order_sell(size = volume)
                    self.position_status = Position.long
                    return

        if self.position_status == Position.short:
            if price > self.previous_stop_buy:
                self.send_market_order_buy(size = volume)
                self.position_status = Position.none
                return

            if self.min_flet_rsi < self.r_indicator.rsi[0] < self.max_flet_rsi and self.e_short_indicator.ema[0] > self.e_long_indicator.ema[0] and self._short_sma.sma[0] > self._long_sma.sma[0]:
                print("Mean", price)
                if self.r_indicator.rsi[0] >= self.rsi_sell:
                    self.send_market_order_buy(size = volume)
                    self.position_status = Position.none
                    return
                else:
                    return
            else:
                if self.m_indicator.macd[0] - signal > 0 and self.e_short_indicator.ema[0] > self.e_long_indicator.ema[0] and self._short_sma.sma[0] > self._long_sma.sma[0]:
                    self.send_market_order_buy(size = volume)
                    self.position_status = Position.none
                    return
                else:
                    return

    def margin_call(self):
        self.margin = True

        volume = self.get_volume(self.get_price(), stop_loss, self.risk)

        if self.previous == Position.long:
            self.send_market_order_buy(size = volume)
        else:
            self.send_market_order_sell(size = volume)



        # Здесь продаем 10 акций портфеля, чтобы немного снизить убыток, но все же сидим в позиции
















